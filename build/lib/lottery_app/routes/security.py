"""Security routes: login, logout, signup, password change, and user deletion."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from lottery_app.database.user_model import User

security_bp = Blueprint("security", __name__)


@security_bp.route("/signup", methods=["GET", "POST"])
@login_required
def signup():
    """Handle new user registration."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form.get("role", "standard")

        User.create(username, password, role)
        flash("Account created! You can now log in.", "business-profile_success")
        return redirect(url_for("business_profile.business_profile"))

    return redirect(url_for("business_profile.business_profile"))


@security_bp.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.get_by_username(username)
        if user and user.verify_password(password):
            login_user(user)
            flash("Welcome back!", "login_success")
            return redirect(url_for("tickets.scan_tickets"))
        flash("Invalid username or password", "login_error")

    return render_template("login.html")


@security_bp.route("/logout")
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    flash("You’ve been logged out.", "login_success")
    return redirect(url_for("security.login"))


@security_bp.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    """Handle password change requests."""
    if request.method == "POST":
        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]
        user = User.get_by_id(current_user.id)

        if not user.verify_password(current_password):
            flash("Current password is incorrect.", "settings_error")
        elif new_password != confirm_password:
            flash("New passwords do not match.", "settings_error")
        else:
            user.update_password(user.id, new_password)
            flash("Password updated successfully!", "settings_success")
            return redirect(url_for("settings.settings"))

    return render_template("settings.html")


@security_bp.route("/delete_user", methods=["POST"])
@login_required
def delete_user():
    """Handle user deletion requests."""
    username_to_delete = request.form.get("username", "").strip()
    c_user = User.get_by_id(current_user.id)
    # Protect self-delete
    if username_to_delete == c_user.username:
        flash(
            "You cannot delete the currently logged-in user.", "business-profile_error"
        )
        return redirect(url_for("business_profile.business_profile"))

    User.delete(username_to_delete)
    flash(
        f"{username_to_delete}'s account was deleted sucessfully.",
        "business-profile_success",
    )
    return redirect(url_for("business_profile.business_profile"))
