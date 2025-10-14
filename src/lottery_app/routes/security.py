from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from lottery_app.database.user_model import User

security_bp = Blueprint("security", __name__)

@security_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        User.create(username, password)
        flash("Account created! You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")

@security_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.get_by_username(username)
        if user and user.verify_password(password):
            login_user(user)
            flash("Welcome back!", "success")
            return redirect(url_for("tickets.scan_tickets"))  # change this route as needed
        else:
            flash("Invalid username or password", "danger")

    return render_template("login.html")

@security_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You’ve been logged out.", "info")
    return redirect(url_for("security.login"))