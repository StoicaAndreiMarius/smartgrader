from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
import json
from .models import Profile

User = get_user_model()

def landing(request):
    return render(request, 'accounts/landing.html')

def login_page(request):
    return render(request, 'accounts/login.html')

def register_page(request):
    return render(request, 'accounts/register.html')


@csrf_exempt
def register_user(request):
    """Register a new user and create their profile."""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=400)

    try:
        data = json.loads(request.body)

        email = data.get("email")
        password = data.get("password")
        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()
        role = data.get("role", "student")

        if not email or not password:
            return JsonResponse({"error": "Email and password required"}, status=400)

        if not first_name or not last_name:
            return JsonResponse({"error": "First name and last name required"}, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({"error": "Email already registered"}, status=400)

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_active=True
        )
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.role = role
        profile.save()

    except Exception as e:
        return JsonResponse({"error": f"Registration failed: {str(e)}"}, status=500)

    return JsonResponse(
        {
            "message": "Registration successful",
            "email": user.email,
            "role": profile.role,
        }
    )


@csrf_exempt
def login_user(request):
    """Authenticate a user and return a JSON response."""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=400)

    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid request body"}, status=400)

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return JsonResponse({"error": "Email and password required"}, status=400)

    user = authenticate(request, email=email, password=password)

    if user is None:
        try:
            existing = User.objects.get(email=email)
            if not existing.is_active:
                return JsonResponse({"error": "Account is not active"}, status=400)
        except User.DoesNotExist:
            pass
        return JsonResponse({"error": "Invalid credentials"}, status=400)

    login(request, user)

    return JsonResponse({"message": "Login successful", "email": user.email})


def logout_user(request):
    logout(request)
    if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.method == "POST":
        return JsonResponse({"message": "Logged out"})
    return redirect("landing")
