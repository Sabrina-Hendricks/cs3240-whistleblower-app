from django.shortcuts import redirect


def root(request):
    """Redirect the user to the main app"""
    return redirect("myapp:home")
