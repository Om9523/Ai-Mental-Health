from flask import Blueprint, request, redirect, render_template, session

auth_bp = Blueprint('auth', __name__)

# Dummy user data (can be replaced with database check)
users = {
    "admin": "password123",
    "user": "mindmood"
}

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if users.get(username) == password:
            session['user'] = username
            return redirect('/')
        else:
            return render_template('login.html', error="Invalid username or password")
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')
