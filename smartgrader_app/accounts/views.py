from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import Test
import json
import os
import sys

# Add pdf_generator to path
sys.path.append(os.path.join(settings.BASE_DIR.parent, 'pdf_generator'))
from pdf_generator import generate_test_pdf_from_db

User = get_user_model()

def landing(request):
    return render(request, 'accounts/landing.html')


def login_page(request):
    return render(request, 'accounts/login.html')

def register_page(request):
    return render(request, 'accounts/register.html')


@csrf_exempt
def register_user(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=400)

    data = json.loads(request.body)

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return JsonResponse({"error": "Email and password required"}, status=400)

    if User.objects.filter(email=email).exists():
        return JsonResponse({"error": "Email already registered"}, status=400)

    user = User.objects.create_user(email=email, password=password)

    return JsonResponse({"message": "User created successfully", "email": user.email}, status=201)


@csrf_exempt
def login_user(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=400)

    data = json.loads(request.body)

    email = data.get("email")
    password = data.get("password")

    user = authenticate(request, email=email, password=password)

    if user is None:
        return JsonResponse({"error": "Invalid credentials"}, status=400)

    login(request, user)

    return JsonResponse({"message": "Login successful", "email": user.email})


def test_generator_page(request):
    """Render the test generator page"""
    return render(request, 'accounts/test_generator.html')


@csrf_exempt
def create_test(request):
    """API endpoint to create a new test"""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=400)

    try:
        data = json.loads(request.body)

        # Validate required fields
        title = data.get("title")
        questions = data.get("questions", [])
        num_options = data.get("num_options", 5)

        if not title:
            return JsonResponse({"error": "Test title is required"}, status=400)

        if not questions or len(questions) == 0:
            return JsonResponse({"error": "At least one question is required"}, status=400)

        # For now, create test for the first user (or anonymous)
        # In production, use: user = request.user if request.user.is_authenticated else None
        # Get first user or create a default user
        user = User.objects.first()
        if not user:
            # Create a default user for testing
            user = User.objects.create_user(
                email="admin@smartgrader.com",
                password="admin123"
            )

        # Create the test
        test = Test.objects.create(
            title=title,
            description=data.get("description", ""),
            questions=questions,
            num_questions=len(questions),
            num_options=num_options,
            created_by=user
        )

        response_data = {
            "message": "Test created successfully!",
            "test_id": test.id,
            "title": test.title,
            "num_questions": test.num_questions
        }

        # If generate_pdf flag is set, generate the PDF
        if data.get("generate_pdf", False):
            try:
                # Create media directory if it doesn't exist
                media_root = os.path.join(settings.BASE_DIR, 'media', 'tests')
                os.makedirs(media_root, exist_ok=True)

                # Generate PDF
                pdf_filename = f"test_{test.id}.pdf"
                pdf_path = os.path.join(media_root, pdf_filename)
                generate_test_pdf_from_db(test, pdf_path)

                response_data["message"] = "Test created and PDF generated successfully!"
                response_data["pdf_url"] = f"/media/tests/{pdf_filename}"
            except Exception as e:
                response_data["message"] = "Test created but PDF generation failed."
                response_data["pdf_error"] = str(e)

        return JsonResponse(response_data, status=201)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def test_list_page(request):
    """Render the test list page"""
    tests = Test.objects.all().order_by('-created_at')
    return render(request, 'accounts/test_list.html', {'tests': tests})