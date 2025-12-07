from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import json

SAMPLE_TEST = json.loads(
    r'''
    {
      "id": 4,
      "title": "Test Matematică — 50 întrebări",
      "num_questions": 50,
      "num_answers": 4,
      "questions": [
        {"id": 1, "text": "Cât este 7 + 9?", "img": null, "correct_answer": "2", "options": ["15", "18", "16", "19"], "points": 5},
        {"id": 2, "text": "Care este rezultatul: 5 × 6?", "img": null, "correct_answer": "3", "options": ["20", "25", "50", "30"], "points": 5},
        {"id": 3, "text": "Cât este 45 − 28?", "img": null, "correct_answer": "0", "options": ["17", "13", "18", "16"], "points": 5},
        {"id": 4, "text": "Rezultatul împărțirii 100 ÷ 4 este:", "img": null, "correct_answer": "1", "options": ["30", "25", "20", "15"], "points": 5},
        {"id": 5, "text": "Cât este 3² + 4²?", "img": null, "correct_answer": "2", "options": ["18", "20", "25", "30"], "points": 5},
        {"id": 6, "text": "Dacă x − 7 = 9, atunci x este:", "img": null, "correct_answer": "3", "options": ["12", "13", "15", "16"], "points": 5},
        {"id": 7, "text": "Perimetrul unui dreptunghi cu laturile 8 cm și 5 cm este:", "img": null, "correct_answer": "0", "options": ["26 cm", "30 cm", "20 cm", "18 cm"], "points": 5},
        {"id": 8, "text": "Aria unui pătrat cu latura 6 cm este:", "img": null, "correct_answer": "1", "options": ["24 cm²", "36 cm²", "30 cm²", "12 cm²"], "points": 5},
        {"id": 9, "text": "Cât este 15% din 200?", "img": null, "correct_answer": "2", "options": ["25", "20", "30", "35"], "points": 5},
        {"id": 10, "text": "√225 este:", "img": null, "correct_answer": "3", "options": ["10", "12", "14", "15"], "points": 5},
        {"id": 11, "text": "Media aritmetică a numerelor 5, 7 și 9 este:", "img": null, "correct_answer": "0", "options": ["7", "6", "8", "10"], "points": 5},
        {"id": 12, "text": "Cât este 11 × 11?", "img": null, "correct_answer": "1", "options": ["100", "121", "110", "132"], "points": 5},
        {"id": 13, "text": "Dacă 3x = 27, atunci x este:", "img": null, "correct_answer": "2", "options": ["7", "8", "9", "6"], "points": 5},
        {"id": 14, "text": "Cât este 2⁵?", "img": null, "correct_answer": "3", "options": ["16", "12", "24", "32"], "points": 5},
        {"id": 15, "text": "Cât este 1/4 din 300?", "img": null, "correct_answer": "0", "options": ["75", "50", "60", "90"], "points": 5},
        {"id": 16, "text": "Perimetrul unui triunghi cu laturile 6, 7 și 8 este:", "img": null, "correct_answer": "1", "options": ["18", "21", "20", "19"], "points": 5},
        {"id": 17, "text": "Dacă 12 + x = 30, atunci x este:", "img": null, "correct_answer": "2", "options": ["15", "16", "18", "20"], "points": 5},
        {"id": 18, "text": "Aria unui dreptunghi cu lungimea 9 cm și lățimea 7 cm este:", "img": null, "correct_answer": "3", "options": ["56", "60", "70", "63"], "points": 5},
        {"id": 19, "text": "Cât este 90 ÷ 9?", "img": null, "correct_answer": "0", "options": ["10", "9", "8", "7"], "points": 5},
        {"id": 20, "text": "Valorarea expresiei 2 × (15 − 4) este:", "img": null, "correct_answer": "2", "options": ["18", "20", "22", "26"], "points": 5},
        {"id": 21, "text": "Cât este 6³?", "img": null, "correct_answer": "3", "options": ["86", "96", "136", "216"], "points": 5},
        {"id": 22, "text": "Cât este 8 + 12 ÷ 3?", "img": null, "correct_answer": "1", "options": ["10", "12", "14", "16"], "points": 5},
        {"id": 23, "text": "Dacă 5x = 40, atunci x este:", "img": null, "correct_answer": "2", "options": ["6", "7", "8", "9"], "points": 5},
        {"id": 24, "text": "Cât este 100 − 37?", "img": null, "correct_answer": "3", "options": ["50", "40", "70", "63"], "points": 5},
        {"id": 25, "text": "Cât este 30% din 200?", "img": null, "correct_answer": "0", "options": ["60", "45", "55", "70"], "points": 5},
        {"id": 26, "text": "√64 este:", "img": null, "correct_answer": "1", "options": ["6", "8", "10", "12"], "points": 5},
        {"id": 27, "text": "Aria unui pătrat cu latura 11 cm este:", "img": null, "correct_answer": "2", "options": ["100", "110", "121", "132"], "points": 5},
        {"id": 28, "text": "Perimetrul unui pătrat cu latura 4 cm este:", "img": null, "correct_answer": "3", "options": ["14", "12", "10", "16"], "points": 5},
        {"id": 29, "text": "Cât este 2 × 14?", "img": null, "correct_answer": "0", "options": ["28", "24", "32", "30"], "points": 5},
        {"id": 30, "text": "Media aritmetică a numerelor 10 și 20 este:", "img": null, "correct_answer": "1", "options": ["12", "15", "18", "16"], "points": 5},
        {"id": 31, "text": "Cât este 50 ÷ 5?", "img": null, "correct_answer": "2", "options": ["15", "20", "10", "5"], "points": 5},
        {"id": 32, "text": "Cât este 9²?", "img": null, "correct_answer": "3", "options": ["72", "75", "81", "90"], "points": 5},
        {"id": 33, "text": "Dacă x/2 = 14, atunci x este:", "img": null, "correct_answer": "0", "options": ["28", "24", "30", "32"], "points": 5},
        {"id": 34, "text": "Cât este 120 − 48?", "img": null, "correct_answer": "1", "options": ["60", "72", "68", "66"], "points": 5},
        {"id": 35, "text": "Cât este 40% din 150?", "img": null, "correct_answer": "2", "options": ["40", "50", "60", "80"], "points": 5},
        {"id": 36, "text": "√169 este:", "img": null, "correct_answer": "3", "options": ["10", "12", "15", "13"], "points": 5},
        {"id": 37, "text": "Aria unui dreptunghi de 10 cm și 12 cm este:", "img": null, "correct_answer": "0", "options": ["120 cm²", "100 cm²", "110 cm²", "90 cm²"], "points": 5},
        {"id": 38, "text": "Cât este 3 × (9 − 3)?", "img": null, "correct_answer": "1", "options": ["12", "18", "15", "20"], "points": 5},
        {"id": 39, "text": "Cât este 56 ÷ 8?", "img": null, "correct_answer": "2", "options": ["5", "6", "7", "8"], "points": 5},
        {"id": 40, "text": "Cât este 7 × 7?", "img": null, "correct_answer": "3", "options": ["45", "46", "47", "49"], "points": 5},
        {"id": 41, "text": "Dacă x + 15 = 40, atunci x este:", "img": null, "correct_answer": "0", "options": ["25", "20", "22", "24"], "points": 5},
        {"id": 42, "text": "Cât este 18 × 2?", "img": null, "correct_answer": "1", "options": ["32", "36", "28", "40"], "points": 5},
        {"id": 43, "text": "Cât este 8³?", "img": null, "correct_answer": "2", "options": ["400", "448", "512", "520"], "points": 5},
        {"id": 44, "text": "Cât este 5% din 200?", "img": null, "correct_answer": "3", "options": ["20", "15", "12", "10"], "points": 5},
        {"id": 45, "text": "Perimetrul unui pătrat cu latura 15 cm este:", "img": null, "correct_answer": "0", "options": ["60 cm", "45 cm", "75 cm", "30 cm"], "points": 5},
        {"id": 46, "text": "Cât este 144 ÷ 12?", "img": null, "correct_answer": "1", "options": ["10", "12", "14", "15"], "points": 5},
        {"id": 47, "text": "Cât este 20 + 35 − 15?", "img": null, "correct_answer": "2", "options": ["35", "30", "40", "45"], "points": 5},
        {"id": 48, "text": "√100 este:", "img": null, "correct_answer": "3", "options": ["8", "9", "12", "10"], "points": 5},
        {"id": 49, "text": "Media aritmetică a numerelor 2, 4, 6 și 8 este:", "img": null, "correct_answer": "0", "options": ["5", "4", "6", "7"], "points": 5},
        {"id": 50, "text": "Cât este 9 × (5 − 2)?", "img": null, "correct_answer": "1", "options": ["21", "27", "36", "18"], "points": 5}
      ]
    }
    '''
)


def _ensure_teacher(user):
    # Verify the requester is a teacher
    profile = getattr(user, "profile", None)
    return user.is_authenticated and profile and profile.role == "teacher"


def generator_page(request):
    # Render the generator for teachers
    if not _ensure_teacher(request.user):
        return JsonResponse({"error": "Only professors can generate tests."}, status=403)
    return render(request, "test_generator/test_generator.html")


def test_list_page(request):
    # Serve the test list using current data (stub until persistence exists)
    if not _ensure_teacher(request.user):
        return JsonResponse({"error": "Only professors can view tests."}, status=403)

    sample_tests = [
        {
            "id": SAMPLE_TEST["id"],
            "title": SAMPLE_TEST["title"],
            "description": None,
            "submission_count": 0,
            "average_percentage": 0,
            "latest_submission": None,
            "latest_percentage": 0,
            "num_questions": SAMPLE_TEST["num_questions"],
            "created_at": "N/A",
            "created_timestamp": 0,
        }
    ]

    return render(
        request,
        "test_generator/test_list.html",
        {"tests_json": json.dumps(sample_tests)},
    )


def test_detail_page(request, test_id: int):
    # Serve detail for the sample test
    if not _ensure_teacher(request.user):
        return JsonResponse({"error": "Only professors can view tests."}, status=403)

    if test_id != SAMPLE_TEST["id"]:
        return JsonResponse({"error": "Test not found"}, status=404)

    test_detail = {
        "id": SAMPLE_TEST["id"],
        "title": SAMPLE_TEST["title"],
        "description": None,
        "num_questions": SAMPLE_TEST["num_questions"],
        "num_answers": SAMPLE_TEST["num_answers"],
        "created_at": "N/A",
        "submission_count": 0,
        "average_percentage": 0,
        "latest_submission": None,
    }

    questions = []
    for q in SAMPLE_TEST["questions"]:
        questions.append(
            {
                "id": q["id"],
                "text": q["text"],
                "img": q.get("img"),
                "points": q.get("points", 0),
                "correct_index": int(q.get("correct_answer", 0)),
                "options": q.get("options", []),
            }
        )

    return render(
        request,
        "test_generator/test_detail.html",
        {"test": test_detail, "submissions": [], "questions": questions},
    )


@csrf_exempt
def create_test(request):
    # Accept JSON payload to create a new test (placeholder until persistence added)
    if not _ensure_teacher(request.user):
        return JsonResponse({"error": "Only professors can generate tests."}, status=403)

    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=400)

    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)

    title = (payload.get("title") or "").strip()
    questions = payload.get("questions") or []

    if not title:
        return JsonResponse({"error": "Title is required"}, status=400)
    if not questions:
        return JsonResponse({"error": "At least one question is required"}, status=400)

    return JsonResponse({"message": "Test saved", "test_id": 1})
