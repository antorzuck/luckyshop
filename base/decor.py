from django.shortcuts import redirect
from functools import wraps

def agent_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect('/')
        if hasattr(request.user, 'profile') and request.user.profile.agent:
            return view_func(request, *args, **kwargs)
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        

        return redirect('/')
    return wrapper
