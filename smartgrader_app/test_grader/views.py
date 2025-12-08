import csv
import json
import os
import shutil
import sys
import zipfile
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from test_generator.models import TestEntry

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from grade_processor.omr_main import grade_submission, process_omr_image  # noqa: E402

from .models import Submission, Test


def _normalize_questions(raw_questions):
    normalized = []
    max_options = 0

    for raw in raw_questions:
        question_text = (raw.get('question') or raw.get('text') or '').strip()
        options = raw.get('options') or []
        try:
            correct_answer = int(raw.get('correct_answer', 0))
        except (TypeError, ValueError):
            correct_answer = 0

        normalized.append(
            {
                'question': question_text,
                'options': options,
                'correct_answer': correct_answer,
            }
        )
        max_options = max(max_options, len(options))

    return normalized, max_options


def _get_or_create_test(test_id, user):
    """Ensure a Test row exists for this test_id and user, seeded from the generator entry."""
    try:
        return Test.objects.get(id=test_id, created_by=user)
    except Test.DoesNotExist:
        entry = TestEntry.objects.get(id=test_id, owner=user)
        payload = entry.payload or {}
        questions, detected_options = _normalize_questions(payload.get('questions') or [])

        try:
            num_options = int(payload.get('num_answers') or payload.get('num_options') or detected_options or 5)
        except (TypeError, ValueError):
            num_options = detected_options or 5

        test = Test(
            id=test_id,
            title=entry.title,
            description=entry.description or '',
            questions=questions,
            created_by=entry.owner,
            num_questions=len(questions),
            num_options=num_options or 5,
        )
        test.save()
        return test


def _temp_dir(test_id):
    temp_dir = Path(settings.MEDIA_ROOT) / 'temp' / f'test_{test_id}'
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


@csrf_exempt
@login_required
def upload_submissions(request, test_id):
    """Upload and process student submissions (images or zip file)."""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        test = _get_or_create_test(test_id, request.user)
    except (Test.DoesNotExist, TestEntry.DoesNotExist):
        return JsonResponse({"error": "Test not found"}, status=404)

    correct_answers = [q['correct_answer'] for q in test.questions]
    uploaded_files = request.FILES.getlist('files')
    zip_file = request.FILES.get('zip_file')

    results = []
    errors = []
    temp_dir = _temp_dir(test_id)

    if zip_file:
        zip_path = temp_dir / zip_file.name
        extract_path = temp_dir / 'extracted'
        try:
            with open(zip_path, 'wb+') as destination:
                for chunk in zip_file.chunks():
                    destination.write(chunk)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)

            for root, _, files in os.walk(extract_path):
                for filename in files:
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                        image_path = Path(root) / filename
                        result = process_single_submission(test, str(image_path), filename, correct_answers)
                        results.append(result)
        except Exception as exc:
            errors.append(f"Error processing zip file: {exc}")
        finally:
            if zip_path.exists():
                zip_path.unlink()
            shutil.rmtree(extract_path, ignore_errors=True)

    elif uploaded_files:
        for uploaded_file in uploaded_files:
            temp_path = temp_dir / uploaded_file.name
            with open(temp_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            try:
                result = process_single_submission(test, str(temp_path), uploaded_file.name, correct_answers)
                results.append(result)
            finally:
                if temp_path.exists():
                    temp_path.unlink()
    else:
        return JsonResponse({"error": "No files uploaded"}, status=400)

    return JsonResponse(
        {
            "message": f"Processed {len(results)} submission(s)",
            "results": results,
            "errors": errors,
        },
        status=200,
    )


def process_single_submission(test, image_path, filename, correct_answers):
    """Process a single submission image."""
    try:
        omr_result = process_omr_image(image_path, test.num_questions, test.num_options)
        if not omr_result['success']:
            return {
                'filename': filename,
                'success': False,
                'error': omr_result.get('error') or 'Unable to process image',
            }

        detected_answers = omr_result['answers']
        grading = grade_submission(detected_answers, correct_answers)

        submission_image_path = f"submissions/test_{test.id}_{filename}"
        with open(image_path, 'rb') as image_file:
            saved_path = default_storage.save(submission_image_path, ContentFile(image_file.read()))

        submission = Submission.objects.create(
            test=test,
            student_user=None,
            first_name='',
            last_name='',
            image=saved_path,
            answers=detected_answers,
            score=grading['score'],
            total_questions=grading['total'],
            percentage=grading['percentage'],
            processed=True,
        )

        return {
            'filename': filename,
            'success': True,
            'submission_id': submission.id,
            'score': grading['score'],
            'total': grading['total'],
            'percentage': grading['percentage'],
        }

    except Exception as exc:
        return {
            'filename': filename,
            'success': False,
            'error': str(exc),
        }


@login_required
def get_test_submissions(request, test_id):
    """Get all submissions for a test."""
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET allowed'}, status=405)

    try:
        test = _get_or_create_test(test_id, request.user)
    except (Test.DoesNotExist, TestEntry.DoesNotExist):
        return JsonResponse({"error": "Test not found"}, status=404)

    correct_answers = [q.get('correct_answer') for q in test.questions]
    submissions = test.submissions.all()
    submissions_data = []
    for sub in submissions:
        image_url = sub.image.url if sub.image else None
        if image_url:
            image_url = request.build_absolute_uri(image_url)

        submissions_data.append(
            {
                'id': sub.id,
                'student_name': sub.full_name,
                'first_name': sub.first_name or '',
                'last_name': sub.last_name or '',
                'score': sub.score,
                'total': sub.total_questions,
                'percentage': sub.percentage,
                'submitted_at': sub.submitted_at.strftime('%Y-%m-%d %H:%M'),
                'image_url': image_url,
                'answers': sub.answers,
                'correct_answers': correct_answers,
            }
        )

    average_percentage = (
        round(sum(sub['percentage'] for sub in submissions_data) / len(submissions_data), 2)
        if submissions_data
        else 0
    )

    return JsonResponse(
        {
            'submissions': submissions_data,
            'count': len(submissions_data),
            'average_percentage': average_percentage,
            'correct_answers': correct_answers,
        },
        status=200,
    )


@login_required
def submission_detail_page(request, test_id, submission_id):
    """View detailed submission with answer breakdown."""
    try:
        test = _get_or_create_test(test_id, request.user)
        submission = Submission.objects.get(id=submission_id, test=test)
    except (Test.DoesNotExist, Submission.DoesNotExist, TestEntry.DoesNotExist):
        return render(request, 'test_grader/test_not_found.html', status=404)

    answer_details = []
    for i, question in enumerate(test.questions):
        student_answer = submission.answers[i] if i < len(submission.answers) else None
        correct_answer = question['correct_answer']
        is_correct = student_answer == correct_answer

        answer_details.append(
            {
                'question_num': i + 1,
                'question_text': question['question'],
                'options': question['options'],
                'student_answer': student_answer,
                'correct_answer': correct_answer,
                'is_correct': is_correct,
            }
        )

    context = {
        'test': test,
        'submission': submission,
        'answer_details': answer_details,
    }
    return render(request, 'test_grader/submission_detail.html', context)


@csrf_exempt
@login_required
def update_submission_name(request, test_id, submission_id):
    """Update the student name on a submission."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    try:
        test = _get_or_create_test(test_id, request.user)
        submission = Submission.objects.get(id=submission_id, test=test)
    except (Test.DoesNotExist, Submission.DoesNotExist, TestEntry.DoesNotExist):
        return JsonResponse({'error': 'Test or submission not found'}, status=404)

    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)

    first_name = (data.get('first_name') or '').strip()
    last_name = (data.get('last_name') or '').strip()

    if not first_name or not last_name:
        return JsonResponse({'error': 'Both first name and last name are required'}, status=400)

    submission.first_name = first_name
    submission.last_name = last_name
    submission.save()

    return JsonResponse(
        {
            'success': True,
            'full_name': submission.full_name,
            'first_name': first_name,
            'last_name': last_name,
        }
    )


@login_required
def export_results_csv(request, test_id):
    """Export test results to CSV."""
    try:
        test = _get_or_create_test(test_id, request.user)
    except (Test.DoesNotExist, TestEntry.DoesNotExist):
        return HttpResponse("Test not found", status=404)

    submissions = test.submissions.filter(processed=True).order_by('-percentage')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="test_{test_id}_results.csv"'

    writer = csv.writer(response)
    header = ['Rank', 'First Name', 'Last Name', 'Score', 'Total', 'Percentage', 'Grade', 'Submitted At']
    for i in range(test.num_questions):
        header.append(f'Q{i+1}')
    writer.writerow(header)

    option_letters = ['A', 'B', 'C', 'D', 'E']
    for rank, submission in enumerate(submissions, start=1):
        grade_letter = (
            'A' if submission.percentage >= 90 else 'B' if submission.percentage >= 80 else 'C'
            if submission.percentage >= 70 else 'D' if submission.percentage >= 60 else 'F'
        )

        row = [
            rank,
            submission.first_name or '',
            submission.last_name or '',
            submission.score,
            submission.total_questions,
            f'{submission.percentage}%',
            grade_letter,
            submission.submitted_at.strftime('%Y-%m-%d %H:%M'),
        ]

        for i in range(test.num_questions):
            if i < len(submission.answers) and submission.answers[i] is not None:
                answer_idx = submission.answers[i]
                row.append(option_letters[answer_idx] if answer_idx < len(option_letters) else str(answer_idx))
            else:
                row.append('-')

        writer.writerow(row)

    writer.writerow([])
    writer.writerow(['SUMMARY STATISTICS'])
    writer.writerow(['Total Submissions', submissions.count()])

    if submissions.count() > 0:
        avg_score = sum(s.score for s in submissions) / submissions.count()
        avg_pct = sum(s.percentage for s in submissions) / submissions.count()
        writer.writerow(['Average Score', f'{avg_score:.2f}/{test.num_questions}'])
        writer.writerow(['Average Percentage', f'{avg_pct:.2f}%'])
        writer.writerow(['Highest Score', max(s.score for s in submissions)])
        writer.writerow(['Lowest Score', min(s.score for s in submissions)])
        pass_count = len([s for s in submissions if s.percentage >= 60])
        writer.writerow(
            ['Pass Rate (>=60%)', f'{pass_count}/{submissions.count()} ({pass_count/submissions.count()*100:.1f}%)']
        )

    return response
