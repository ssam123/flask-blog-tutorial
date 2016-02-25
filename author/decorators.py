from functools import wraps
from flask import session, request, redirect, url_for, abort

def login_required(f):
    @wraps(f)
    #args = positional arguments kwargs = keyword arguments
    def decorated_function(*args, **kwargs):
        if session.get('username') is None:
            #next sends back to og page
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
            
def author_required(f):
    @wraps(f)
    #args = positional arguments kwargs = keyword arguments
    def decorated_function(*args, **kwargs):
        if session.get('is_author') is None:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function