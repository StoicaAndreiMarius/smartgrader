from functools import wraps
from django.http import JsonResponse
from django.shortcuts import render, redirect


def student_required(view_func):
    """Decorator to require student role.

    Checks that the user is authenticated and has role='student'.
    Returns 401 if not authenticated, 403 if not a student.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            # Redirect to login page for HTML views, JSON for API
            if request.headers.get('Accept') == 'application/json':
                return JsonResponse({'error': 'Authentication required'}, status=401)
            return redirect(f'/accounts/login/?next={request.path}')

        profile = getattr(request.user, 'profile', None)
        if not profile or profile.role != 'student':
            if request.headers.get('Accept') == 'application/json':
                return JsonResponse({'error': 'Student access required'}, status=403)
            return render(request, 'test_grader/access_denied.html', {
                'message': 'Only students can access this page.'
            }, status=403)

        return view_func(request, *args, **kwargs)
    return wrapper


def teacher_required(view_func):
    """Decorator to require teacher role.

    Checks that the user is authenticated and has role='teacher'.
    Returns 401 if not authenticated, 403 if not a teacher.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            # Redirect to login page for HTML views, JSON for API
            if request.headers.get('Accept') == 'application/json':
                return JsonResponse({'error': 'Authentication required'}, status=401)
            return redirect(f'/accounts/login/?next={request.path}')

        profile = getattr(request.user, 'profile', None)
        if not profile or profile.role != 'teacher':
            if request.headers.get('Accept') == 'application/json':
                return JsonResponse({'error': 'Teacher access required'}, status=403)
            return render(request, 'test_grader/access_denied.html', {
                'message': 'Only teachers can access this page.'
            }, status=403)

        return view_func(request, *args, **kwargs)
    return wrapper
