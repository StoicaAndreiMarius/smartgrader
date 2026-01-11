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
    """Convert raw question payloads into a consistent structure and count options."""
    normalized = []
    max_options = 0

    for raw in raw_questions:
        question_text = (raw.get('question') or raw.get('text') or '').strip()
        options = raw.get('options') or []

        # Normalize correct_answer to list format for multiple answer support
        correct_answer_raw = raw.get('correct_answer', 0)
        if isinstance(correct_answer_raw, list):
            correct_answer = correct_answer_raw
        elif isinstance(correct_answer_raw, int):
            correct_answer = [correct_answer_raw]
        else:
            try:
                correct_answer = [int(correct_answer_raw)]
            except (TypeError, ValueError):
                correct_answer = [0]

        grading_mode = raw.get('grading_mode', 'all_or_nothing')

        normalized.append(
            {
                'question': question_text,
                'options': options,
                'correct_answer': correct_answer,
                'grading_mode': grading_mode,
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
            value = payload.get('num_answers') or payload.get('num_options') or detected_options or 5
            # Handle case where value might be a list
            if isinstance(value, list):
                num_options = detected_options or 5
            else:
                num_options = int(value)
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
    """Create and return the temporary directory for a test's uploads."""
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

    # Extract correct answers and grading modes for all questions
    correct_answers = [q['correct_answer'] for q in test.questions]
    grading_modes = [q.get('grading_mode', 'all_or_nothing') for q in test.questions]
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
                        result = process_single_submission(test, str(image_path), filename, correct_answers, grading_modes)
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
                result = process_single_submission(test, str(temp_path), uploaded_file.name, correct_answers, grading_modes)
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


def process_single_submission(test, image_path, filename, correct_answers, grading_modes):
    """Process a single submission image."""
    try:
        omr_result = process_omr_image(image_path, test.num_questions, test.num_options, darkness_threshold=0.6)
        if not omr_result['success']:
            return {
                'filename': filename,
                'success': False,
                'error': omr_result.get('error') or 'Unable to process image',
            }

        detected_answers = omr_result['answers']
        grading = grade_submission(detected_answers, correct_answers, grading_modes)

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
        grading_mode = question.get('grading_mode', 'all_or_nothing')

        # Normalize both to sets for comparison
        student_set = set()
        if isinstance(student_answer, list):
            student_set = set(student_answer)
        elif isinstance(student_answer, int):
            student_set = {student_answer}

        correct_set = set()
        if isinstance(correct_answer, list):
            correct_set = set(correct_answer)
        elif isinstance(correct_answer, int):
            correct_set = {correct_answer}

        is_correct = student_set == correct_set

        answer_details.append(
            {
                'question_num': i + 1,
                'question_text': question['question'],
                'options': question['options'],
                'student_answer': student_answer,
                'correct_answer': correct_answer,
                'is_correct': is_correct,
                'grading_mode': grading_mode,
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
            if i < len(submission.answers):
                answer = submission.answers[i]

                if answer is None:
                    row.append('-')
                elif isinstance(answer, list):
                    # Multiple answers - show as "A,C,E"
                    answer_str = ','.join([option_letters[idx] if idx < len(option_letters) else str(idx)
                                          for idx in sorted(answer)])
                    row.append(answer_str)
                else:
                    # Single answer
                    row.append(option_letters[answer] if answer < len(option_letters) else str(answer))
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


# =============================================================================
# Share Code Management Views (Teacher)
# =============================================================================

@login_required
def generate_share_code_view(request, test_id):
    """Generate or regenerate share code for a test."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        test = _get_or_create_test(test_id, request.user)
    except (Test.DoesNotExist, TestEntry.DoesNotExist):
        return JsonResponse({"error": "Test not found"}, status=404)

    from .utils import generate_share_code, format_share_code

    # Generate new code
    test.share_code = generate_share_code()
    test.is_open_for_submissions = True
    test.save()

    share_url = request.build_absolute_uri(
        f'/student/test/{test.share_code}/'
    )

    return JsonResponse({
        'success': True,
        'share_code': test.share_code,
        'formatted_code': format_share_code(test.share_code),
        'share_url': share_url,
        'is_open': test.is_open_for_submissions
    })


@login_required
def toggle_submissions(request, test_id):
    """Toggle whether submissions are open for a test."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        test = _get_or_create_test(test_id, request.user)
    except (Test.DoesNotExist, TestEntry.DoesNotExist):
        return JsonResponse({"error": "Test not found"}, status=404)

    try:
        data = json.loads(request.body or '{}')
        test.is_open_for_submissions = data.get('is_open', False)
        test.save()
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    return JsonResponse({
        'success': True,
        'is_open': test.is_open_for_submissions
    })


@login_required
def get_share_info(request, test_id):
    """Get share code and settings for a test."""
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET allowed'}, status=405)

    try:
        test = _get_or_create_test(test_id, request.user)
    except (Test.DoesNotExist, TestEntry.DoesNotExist):
        return JsonResponse({"error": "Test not found"}, status=404)

    from .utils import format_share_code

    share_url = None
    if test.share_code:
        share_url = request.build_absolute_uri(
            f'/student/test/{test.share_code}/'
        )

    return JsonResponse({
        'share_code': test.share_code,
        'formatted_code': format_share_code(test.share_code) if test.share_code else None,
        'share_url': share_url,
        'is_open': test.is_open_for_submissions,
        'allow_multiple': test.allow_multiple_submissions
    })


# =============================================================================
# Student Submission Views
# =============================================================================

@login_required
def student_dashboard(request):
    """Student dashboard with share code input and recent submissions."""
    # Check if user is a student
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'student':
        return render(request, 'test_grader/access_denied.html', {
            'message': 'Only students can access the student dashboard.'
        }, status=403)

    # Get recent submissions for this student
    recent_submissions = Submission.objects.filter(
        student_user=request.user
    ).select_related('test').order_by('-submitted_at')[:5]

    context = {
        'recent_submissions': recent_submissions
    }

    return render(request, 'test_grader/student_dashboard.html', context)


@login_required
def student_test_access(request, share_code):
    """Student access page for a test via share code."""
    from django.shortcuts import redirect

    # Check if user is a student
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'student':
        return render(request, 'test_grader/access_denied.html', {
            'message': 'Only students can access tests via share codes.'
        }, status=403)

    # Find test by share code
    try:
        test = Test.objects.get(share_code=share_code)
    except Test.DoesNotExist:
        return render(request, 'test_grader/test_not_found.html', {
            'message': 'Invalid share code. Please check and try again.'
        }, status=404)

    # Check if submissions are open
    if not test.is_open_for_submissions:
        return render(request, 'test_grader/submissions_closed.html', {
            'test': test,
            'message': 'This test is not currently accepting submissions.'
        }, status=403)

    # Check if student already submitted
    existing_submission = Submission.objects.filter(
        test=test,
        student_user=request.user
    ).first()

    if existing_submission and not test.allow_multiple_submissions:
        # Redirect to results page
        return redirect('student-submission-result',
                       share_code=share_code,
                       submission_id=existing_submission.id)

    # Build questions without correct answers
    questions_for_display = []
    for i, q in enumerate(test.questions, 1):
        questions_for_display.append({
            'number': i,
            'text': q.get('question', ''),
            'num_options': test.num_options
        })

    context = {
        'test': test,
        'questions': questions_for_display,
        'share_code': share_code,
        'has_previous_submission': existing_submission is not None,
        'previous_score': existing_submission.percentage if existing_submission else None
    }

    return render(request, 'test_grader/student_test_access.html', context)


@csrf_exempt
@login_required
def student_submit_answers(request, share_code):
    """Handle student answer sheet upload."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    # Verify student role
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'student':
        return JsonResponse({'error': 'Only students can submit answers'}, status=403)

    # Find test
    try:
        test = Test.objects.get(share_code=share_code)
    except Test.DoesNotExist:
        return JsonResponse({'error': 'Invalid share code'}, status=404)

    # Check if submissions are open
    if not test.is_open_for_submissions:
        return JsonResponse({'error': 'Submissions are closed for this test'}, status=403)

    # Check for existing submission
    existing = Submission.objects.filter(test=test, student_user=request.user).first()
    if existing and not test.allow_multiple_submissions:
        return JsonResponse({
            'error': 'You have already submitted this test',
            'submission_id': existing.id
        }, status=400)

    # Get uploaded file
    uploaded_file = request.FILES.get('answer_sheet')
    if not uploaded_file:
        return JsonResponse({'error': 'No file uploaded'}, status=400)

    # Validate file type
    if not uploaded_file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
        return JsonResponse({'error': 'Invalid file type. Please upload an image.'}, status=400)

    # Process the submission
    temp_dir = _temp_dir(test.id)
    temp_path = temp_dir / f"student_{request.user.id}_{uploaded_file.name}"

    try:
        # Save uploaded file temporarily
        with open(temp_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        # Extract correct answers and grading modes
        correct_answers = [q['correct_answer'] for q in test.questions]
        grading_modes = [q.get('grading_mode', 'all_or_nothing') for q in test.questions]

        # Process with OMR
        result = process_single_submission(
            test,
            str(temp_path),
            uploaded_file.name,
            correct_answers,
            grading_modes
        )

        if not result.get('success'):
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Failed to process answer sheet')
            }, status=400)

        # Update the submission with student user
        submission = Submission.objects.get(id=result['submission_id'])
        submission.student_user = request.user
        submission.first_name = request.user.first_name
        submission.last_name = request.user.last_name
        submission.save()

        return JsonResponse({
            'success': True,
            'submission_id': submission.id,
            'score': result['score'],
            'total': result['total'],
            'percentage': result['percentage'],
            'redirect_url': f'/student/test/{share_code}/result/{submission.id}/'
        })

    except Exception as exc:
        return JsonResponse({
            'success': False,
            'error': f'Error processing submission: {str(exc)}'
        }, status=500)
    finally:
        # Clean up temp file
        if temp_path.exists():
            temp_path.unlink()


@login_required
def student_submission_result(request, share_code, submission_id):
    """Show student their submission results."""
    # Verify student role
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'student':
        return render(request, 'test_grader/access_denied.html', {
            'message': 'Access denied.'
        }, status=403)

    # Find test and submission
    try:
        test = Test.objects.get(share_code=share_code)
        submission = Submission.objects.get(
            id=submission_id,
            test=test,
            student_user=request.user  # Ensure student can only see their own
        )
    except (Test.DoesNotExist, Submission.DoesNotExist):
        return render(request, 'test_grader/test_not_found.html', {
            'message': 'Submission not found.'
        }, status=404)

    # Build answer details
    answer_details = []
    for i, question in enumerate(test.questions):
        student_answer = submission.answers[i] if i < len(submission.answers) else None
        correct_answer = question['correct_answer']

        # Normalize to sets for comparison
        student_set = set()
        if isinstance(student_answer, list):
            student_set = set(student_answer)
        elif isinstance(student_answer, int):
            student_set = {student_answer}

        correct_set = set()
        if isinstance(correct_answer, list):
            correct_set = set(correct_answer)
        elif isinstance(correct_answer, int):
            correct_set = {correct_answer}

        is_correct = student_set == correct_set

        answer_details.append({
            'question_num': i + 1,
            'question_text': question['question'],
            'options': question['options'],
            'student_answer': student_answer,
            'correct_answer': correct_answer,
            'is_correct': is_correct,
            'grading_mode': question.get('grading_mode', 'all_or_nothing')
        })

    context = {
        'test': test,
        'submission': submission,
        'answer_details': answer_details,
        'share_code': share_code
    }

    return render(request, 'test_grader/student_result.html', context)


# =============================================================================
# General Information Pages
# =============================================================================

def help_page(request):
    """Display the help page."""
    return render(request, 'help.html')


def information_page(request):
    """Display the information/about page."""
    return render(request, 'information.html')
