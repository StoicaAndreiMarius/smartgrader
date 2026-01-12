import json
from copy import deepcopy
from pathlib import Path
from random import sample
import sys

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from pdf_generator.pdf_generator import generate_test_pdf
from test_grader.models import Test as GraderTest
from .models import TestEntry


def _ensure_teacher(user):
    """Return True when the requester is an authenticated teacher."""
    profile = getattr(user, "profile", None)
    return user.is_authenticated and profile and profile.role == "teacher"


def generator_page(request):
    """Render the generator page for teachers only."""
    if not _ensure_teacher(request.user):
        return JsonResponse({"error": "Only professors can generate tests."}, status=403)
    return render(request, "test_generator/test_generator.html")


def _serialize_test(entry):
    """Convert a TestEntry into a JSON-friendly dict with summary stats."""
    payload = entry.payload or {}
    questions = payload.get("questions", [])
    try:
        grader_test = _ensure_grader_test(entry)
        subs = grader_test.submissions.filter(processed=True)
        submission_count = subs.count()
        avg_pct = round(sum(s.percentage for s in subs) / submission_count, 2) if submission_count else 0
    except Exception:
        grader_test = None
        submission_count = payload.get("submission_count", 0)
        avg_pct = payload.get("average_percentage", 0)

    latest_submission = None
    if grader_test:
        latest = grader_test.submissions.order_by("-submitted_at").first()
        if latest:
            latest_submission = {
                "student": latest.full_name,
                "percentage": latest.percentage,
                "score": latest.score,
                "submitted_at": latest.submitted_at.strftime("%Y-%m-%d %H:%M"),
            }
    if not latest_submission:
        latest_submission = payload.get("latest_submission")

    return {
        "id": entry.id,
        "title": entry.title,
        "description": entry.description or "",
        "submission_count": submission_count,
        "average_percentage": avg_pct,
        "latest_submission": latest_submission,
        "latest_percentage": latest_submission["percentage"] if isinstance(latest_submission, dict) else 0,
        "num_questions": len(questions),
        "created_at": entry.created_at.strftime("%Y-%m-%d %H:%M"),
        "created_timestamp": int(entry.created_at.timestamp()),
        "owner_email": entry.owner.email if getattr(entry, "owner_id", None) else "",
    }


def test_list_page(request):
    """Serve the test list using DB-backed entries."""
    if not _ensure_teacher(request.user):
        return JsonResponse({"error": "Only professors can view tests."}, status=403)

    tests = TestEntry.objects.filter(owner=request.user).order_by("-created_at")
    data = [_serialize_test(t) for t in tests]

    return render(
        request,
        "test_generator/test_list.html",
        {"tests_json": json.dumps(data)},
    )


def _build_questions(payload):
    """Normalize raw question payload into the shape expected by templates."""
    questions = []
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for idx_q, q in enumerate(payload.get("questions", []), start=1):
        # Handle correct_answer as either a single value or a list
        correct_answer_raw = q.get("correct_answer", 0)
        if isinstance(correct_answer_raw, list):
            correct_indices = set(correct_answer_raw)
        elif isinstance(correct_answer_raw, int):
            correct_indices = {correct_answer_raw}
        else:
            try:
                correct_indices = {int(correct_answer_raw)}
            except (TypeError, ValueError):
                correct_indices = {0}

        opts = []
        for idx, text in enumerate(q.get("options", [])):
            label = letters[idx] if idx < len(letters) else str(idx + 1)
            opts.append({"label": label, "text": text, "is_correct": idx in correct_indices})
        questions.append(
            {
                "id": q.get("id") or q.get("question_id") or q.get("uuid") or idx_q,
                "text": q.get("text") or q.get("question") or "",
                "img": q.get("img"),
                "points": q.get("points", 0),
                "options": opts,
            }
        )
    return questions


def _ensure_grader_test(entry):
    """Create or update a TestGrader.Test row for this generated test."""
    payload = entry.payload or {}
    questions_payload = payload.get("questions", [])
    normalized = []
    max_options = 0

    for q in questions_payload:
        options = q.get("options") or []
        max_options = max(max_options, len(options))

        # Handle correct_answer which can be int, list, or string
        raw_answer = q.get("correct_answer", 0)
        try:
            if isinstance(raw_answer, list):
                # If it's a list, take the first element
                correct_answer = int(raw_answer[0]) if raw_answer else 0
            else:
                correct_answer = int(raw_answer)
        except (TypeError, ValueError, IndexError):
            correct_answer = 0

        normalized.append(
            {
                "question": q.get("text") or q.get("question") or "",
                "options": options,
                "correct_answer": correct_answer,
            }
        )

    try:
        num_options = int(payload.get("num_answers") or payload.get("num_options") or max_options or 5)
    except (TypeError, ValueError):
        num_options = max_options or 5

    # Update existing or create new
    grader_test, created = GraderTest.objects.update_or_create(
        id=entry.id,
        defaults={
            'title': entry.title,
            'description': entry.description or "",
            'questions': normalized,
            'created_by': entry.owner,
            'num_questions': len(normalized),
            'num_options': num_options,
        }
    )
    return grader_test


def test_detail_page(request, test_id: int):
    """Serve detail for a specific test and its submissions."""
    if not _ensure_teacher(request.user):
        return JsonResponse({"error": "Only professors can view tests."}, status=403)

    try:
        entry = TestEntry.objects.get(id=test_id, owner=request.user)
    except TestEntry.DoesNotExist:
        return JsonResponse({"error": "Test not found"}, status=404)

    payload = entry.payload or {}
    grader_test = _ensure_grader_test(entry)
    submissions_qs = grader_test.submissions.filter(processed=True).order_by("-submitted_at")
    submission_count = submissions_qs.count()
    avg_pct = round(sum(sub.percentage for sub in submissions_qs) / submission_count, 2) if submission_count else 0

    latest_submission = submissions_qs.first()
    latest_data = (
        {
            "student": latest_submission.full_name,
            "percentage": latest_submission.percentage,
            "score": latest_submission.score,
            "submitted_at": latest_submission.submitted_at.strftime("%Y-%m-%d %H:%M"),
        }
        if latest_submission
        else None
    )

    submissions_table = []
    for sub in submissions_qs[:10]:
        image_url = sub.image.url if sub.image else None
        if image_url:
            image_url = request.build_absolute_uri(image_url)

        submissions_table.append(
            {
                "id": sub.id,
                "student_name": sub.full_name,
                "first_name": sub.first_name or "",
                "last_name": sub.last_name or "",
                "score": sub.score,
                "total": sub.total_questions,
                "percentage": sub.percentage,
                "submitted_at": sub.submitted_at.strftime("%Y-%m-%d %H:%M"),
                "image_url": image_url,
                "answers": sub.answers,
                "correct_answers": [q.get("correct_answer") for q in grader_test.questions],
            }
        )

    test_detail = {
        "id": entry.id,
        "title": entry.title,
        "description": entry.description or "",
        "num_questions": grader_test.num_questions or len(payload.get("questions", [])),
        "num_answers": payload.get("num_answers") or payload.get("num_options") or grader_test.num_options,
        "created_at": entry.created_at.strftime("%Y-%m-%d %H:%M"),
        "submission_count": submission_count,
        "average_percentage": avg_pct,
        "latest_submission": latest_data,
    }

    questions = _build_questions(payload)

    return render(
        request,
        "test_generator/test_detail.html",
        {
            "test": test_detail,
            "submissions": submissions_table,
            "submissions_json": json.dumps(submissions_table),
            "correct_answers": [q.get("correct_answer") for q in grader_test.questions],
            "questions": questions,
        },
    )


@csrf_exempt
def create_test(request):
    """Accept JSON payload to create a new test and store it in the DB."""
    if not _ensure_teacher(request.user):
        return JsonResponse({"error": "Only professors can generate tests."}, status=403)

    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=400)

    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)

    title = (payload.get("title") or "").strip()
    description = (payload.get("description") or "").strip()
    questions = payload.get("questions") or []
    enable_random = bool(payload.get("enable_randomization"))
    try:
        num_variants = int(payload.get("num_variants") or 1)
    except (TypeError, ValueError):
        num_variants = 1
    num_variants = max(1, num_variants)
    try:
        questions_per_variant = int(payload.get("questions_per_variant") or len(questions))
    except (TypeError, ValueError):
        questions_per_variant = len(questions)

    if not title:
        return JsonResponse({"error": "Title is required"}, status=400)
    if not questions:
        return JsonResponse({"error": "At least one question is required"}, status=400)
    if enable_random and questions_per_variant > len(questions):
        return JsonResponse({"error": "questions_per_variant cannot exceed total questions"}, status=400)
    if enable_random and num_variants < 1:
        return JsonResponse({"error": "num_variants must be at least 1"}, status=400)

    created_ids = []
    created_entries = []
    variants_to_create = num_variants if enable_random else 1
    original_questions = deepcopy(questions)

    try:
        for idx in range(variants_to_create):
            variant_payload = deepcopy(payload)

            if enable_random:
                variant_questions = sample(questions, questions_per_variant)
                variant_payload["questions"] = variant_questions
                variant_payload["num_variants"] = num_variants
                variant_payload["questions_per_variant"] = questions_per_variant
                variant_payload["original_questions"] = original_questions
                variant_title = f"{title} (Variant {idx + 1})"
            else:
                variant_title = title
                variant_payload["original_questions"] = original_questions

            entry = TestEntry.objects.create(
                title=variant_title,
                description=description,
                payload=variant_payload,
                owner=request.user if request.user.is_authenticated else None,
            )
            created_ids.append(entry.id)
            created_entries.append(entry)
    except Exception as exc:
        return JsonResponse({"error": f"Failed to save test: {exc}"}, status=500)

    pdf_urls = []
    if payload.get("generate_pdf"):
        try:
            for entry in created_entries:
                pdf_payload, error = _build_pdf_payload(entry)
                if error:
                    raise ValueError(error)

                json_path, pdf_path = _pdf_storage_paths(entry.id)
                with open(json_path, "w", encoding="utf-8") as fh:
                    json.dump(pdf_payload, fh, ensure_ascii=False, indent=2)
                generate_test_pdf(str(json_path), str(pdf_path))
                pdf_urls.append(_pdf_url(request, entry.id))
        except Exception as exc:
            return JsonResponse({"error": f"Failed to generate PDF: {exc}"}, status=500)

    response = {"message": "Test saved", "test_ids": created_ids}
    if pdf_urls:
        response["pdf_urls"] = pdf_urls
    return JsonResponse(response)


@csrf_exempt
def delete_test(request, test_id: int):
    """Delete a test by id."""
    if not _ensure_teacher(request.user):
        return JsonResponse({"error": "Only professors can delete tests."}, status=403)

    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=400)

    try:
        entry = TestEntry.objects.get(id=test_id, owner=request.user)
    except TestEntry.DoesNotExist:
        return JsonResponse({"error": "Test not found"}, status=404)

    entry.delete()
    return JsonResponse({"message": "Test deleted", "deleted_id": test_id})


def _build_pdf_payload(entry):
    """Prepare the JSON structure the PDF generator expects for a test entry."""
    payload = entry.payload or {}
    questions_payload = payload.get("questions") or payload.get("original_questions") or []
    if not questions_payload:
        return None, "No questions available to generate PDF"

    first_options = []
    if questions_payload and isinstance(questions_payload[0], dict):
        first_options = questions_payload[0].get("options") or []

    try:
        num_answers = int(payload.get("num_answers") or payload.get("num_options") or len(first_options))
    except (TypeError, ValueError):
        num_answers = len(first_options)
    num_answers = max(1, num_answers)

    data = {
        "id": entry.id,
        "title": entry.title,
        "num_questions": len(questions_payload),
        "num_answers": num_answers,
        "varianta": payload.get("varianta") or 1,
        "questions": [],
    }

    for idx, raw_q in enumerate(questions_payload, start=1):
        q = raw_q if isinstance(raw_q, dict) else {"text": str(raw_q), "options": []}
        raw_options = q.get("options") or []
        options = []
        for opt in raw_options:
            if isinstance(opt, dict):
                options.append(opt.get("text") or opt.get("label") or "")
            else:
                options.append(str(opt))

        # Handle both int and list format for correct_answer
        correct_answer_raw = q.get("correct_answer", 0)
        if isinstance(correct_answer_raw, list):
            # For PDF, just use first answer (not displayed to students anyway)
            correct_answer = correct_answer_raw[0] if correct_answer_raw else 0
        else:
            try:
                correct_answer = int(correct_answer_raw)
            except (TypeError, ValueError):
                correct_answer = 0

        data["questions"].append(
            {
                "id": q.get("id") or q.get("question_id") or q.get("uuid") or idx,
                "text": q.get("text") or q.get("question") or "",
                "img": q.get("img"),
                "correct_answer": correct_answer,
                "options": options,
                "points": q.get("points", 0),
            }
        )

    return data, None


def _pdf_storage_paths(test_id: int):
    """Return paths for the intermediate JSON file and generated PDF."""
    generated_dir = Path(settings.BASE_DIR) / "static" / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)
    json_path = generated_dir / f"test_{test_id}.json"
    pdf_path = generated_dir / f"test_{test_id}.pdf"
    return json_path, pdf_path


def _pdf_url(request, test_id: int):
    """Build the absolute URL to the generated PDF for a test."""
    static_url = settings.STATIC_URL or "/static/"
    if not static_url.startswith(("http://", "https://", "/")):
        static_url = f"/{static_url}"
    if not static_url.endswith("/"):
        static_url = f"{static_url}/"
    relative_url = f"{static_url}generated/test_{test_id}.pdf"
    return request.build_absolute_uri(relative_url)


def pdf_test(request, test_id: int):
    """Generate a PDF for the given test using the stored JSON payload."""
    if not _ensure_teacher(request.user):
        return JsonResponse({"error": "Only professors can view tests."}, status=403)

    try:
        entry = TestEntry.objects.get(id=test_id, owner=request.user)
    except TestEntry.DoesNotExist:
        return JsonResponse({"error": "Test not found"}, status=404)

    data, error = _build_pdf_payload(entry)
    if error:
        return JsonResponse({"error": error}, status=400)

    json_path, pdf_path = _pdf_storage_paths(entry.id)

    try:
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        generate_test_pdf(str(json_path), str(pdf_path))
    except Exception as exc:
        return JsonResponse({"error": f"PDF generation failed: {exc}"}, status=500)

    pdf_url = _pdf_url(request, entry.id)
    return JsonResponse({"message": "PDF generated", "pdf_url": pdf_url, "test_id": entry.id})


@csrf_exempt
def ai_generate_questions(request):
    """Generate multiple-choice questions using the Anthropic API."""
    if not _ensure_teacher(request.user):
        return JsonResponse({"error": "Only professors can generate tests."}, status=403)

    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=400)

    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON in request"}, status=400)

    topic = (payload.get("topic") or "").strip()
    difficulty = (payload.get("difficulty") or "medium").strip().lower()
    try:
        num_questions = int(payload.get("num_questions") or 10)
    except (TypeError, ValueError):
        num_questions = 10
    try:
        num_options = int(payload.get("num_options") or 5)
    except (TypeError, ValueError):
        num_options = 5

    if not topic:
        return JsonResponse({"error": "Topic is required"}, status=400)
    if num_questions < 1 or num_questions > 50:
        return JsonResponse({"error": "Number of questions must be between 1 and 50"}, status=400)
    if num_options < 2 or num_options > 5:
        return JsonResponse({"error": "Number of options must be between 2 and 5"}, status=400)
    if difficulty not in {"easy", "medium", "hard"}:
        difficulty = "medium"

    try:
        import anthropic
    except ImportError:
        return JsonResponse(
            {"error": "AI generation requires the 'anthropic' package. Install it with: pip install anthropic"},
            status=500,
        )

    api_key = getattr(settings, "ANTHROPIC_API_KEY", None)
    if not api_key:
        return JsonResponse(
            {"error": "ANTHROPIC_API_KEY environment variable not set. Please configure your API key."},
            status=500,
        )

    client = anthropic.Anthropic(api_key=api_key)

    option_letters = ["A", "B", "C", "D", "E"][:num_options]
    extra_options = ""
    if num_options >= 4:
        extra_options += ', "Option D text"'
    if num_options >= 5:
        extra_options += ', "Option E text"'

    prompt = (
        f"Generate {num_questions} multiple-choice questions about: {topic}\n\n"
        f"Difficulty level: {difficulty}\n"
        f"Number of options per question: {num_options} ({', '.join(option_letters)})\n\n"
        "Format each question as a JSON object with this exact structure:\n"
        "{\n"
        '    \"question\": \"The question text\",\n'
        f'    \"options\": [\"Option A text\", \"Option B text\", \"Option C text\"{extra_options}],\n'
        '    \"correct_answer\": [0],\n'
        '    \"grading_mode\": \"all_or_nothing\"\n'
        "}\n\n"
        f"Where correct_answer is an ARRAY of indices (0-{num_options - 1}) of correct options.\n"
        "Use [index] for single correct answer, [index1, index2, ...] for multiple correct answers.\n"
        "Set grading_mode to 'all_or_nothing' for single answers or 'partial_credit' for multiple correct answers.\n\n"
        f"Return a JSON array of {num_questions} questions. Make the questions educational, clear, and appropriately challenging for {difficulty} level.\n"
        f"Ensure each question tests understanding of {topic}."
    )

    try:
        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )
        response_text = message.content[0].text if message.content else ""

        if "```json" in response_text:
            response_text = response_text.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```", 1)[1].split("```", 1)[0].strip()

        questions = json.loads(response_text)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON received from AI"}, status=500)
    except Exception as exc:
        return JsonResponse({"error": f"AI generation failed: {exc}"}, status=500)

    if not isinstance(questions, list):
        return JsonResponse({"error": "Invalid response format from AI"}, status=500)

    validated_questions = []
    for q in questions:
        if not isinstance(q, dict):
            continue

        text = (q.get("question") or q.get("text") or "").strip()
        options = q.get("options") or []

        # Parse correct_answer - support both array and int formats
        correct_answer_raw = q.get("correct_answer", [0])
        if isinstance(correct_answer_raw, list):
            correct_indices = correct_answer_raw
        elif isinstance(correct_answer_raw, int):
            correct_indices = [correct_answer_raw]
        else:
            try:
                correct_indices = [int(correct_answer_raw)]
            except (TypeError, ValueError):
                correct_indices = [0]

        grading_mode = q.get("grading_mode", "all_or_nothing")

        if not text or not isinstance(options, list) or len(options) != num_options:
            continue

        # Validate all indices are in range
        if not all(0 <= idx < num_options for idx in correct_indices):
            continue

        if len(correct_indices) == 0:
            continue

        validated_questions.append(
            {
                "question": text,
                "options": [str(opt).strip() for opt in options],
                "correct_answer": correct_indices,
                "grading_mode": grading_mode,
            }
        )

    if not validated_questions:
        return JsonResponse({"error": "No valid questions generated"}, status=500)

    return JsonResponse({"success": True, "questions": validated_questions, "count": len(validated_questions)})
