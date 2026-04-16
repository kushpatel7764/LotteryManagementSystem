"""
Security routes for the Flask application.
 
Provides user authentication routes including login, logout,
signup, password change, and user deletion.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from lottery_app.database.user_model import User
from lottery_app.extensions import limiter

security_bp = Blueprint("security", __name__)


@security_bp.route("/signup", methods=["GET", "POST"])
@login_required
def signup():
    """Create a new user account. Only accessible by admins."""
    c_user = User.get_by_id(current_user.id)
    if c_user.role not in ("admin", "default_admin"):
        flash("Unauthorized.", "error")
        return redirect(url_for("business_profile.business_profile"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form.get("role", "standard")
        if role not in ("standard", "admin"):
            role = "standard"

        User.create(username, password, role)
        return redirect(url_for("business_profile.business_profile"))

    return redirect(url_for("business_profile.business_profile"))


@security_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    """Authenticate a user and redirect to the ticket scanning page on success."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.get_by_username(username)
        if user and user.verify_password(password):
            login_user(user)
            flash("Welcome back!", "login_success")
            return redirect(
                url_for("tickets.scan_tickets")
            )  # change this route as needed
        flash("Invalid username or password", "login_error")

    return render_template("login.html")


@security_bp.route("/logout")
@login_required
def logout():
    """Log out the current user and redirect to the login page."""
    logout_user()
    flash("You’ve been logged out.", "login_success")
    return redirect(url_for("security.login"))


@security_bp.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    """Allow the current user to change their password."""
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
    """Delete a user account. Only accessible by admins. Prevents self-deletion."""
    c_user = User.get_by_id(current_user.id)
    if c_user.role not in ("admin", "default_admin"):
        flash("Unauthorized.", "error")
        return redirect(url_for("business_profile.business_profile"))

    username_to_delete = request.form.get("username", "").strip()
    if username_to_delete == c_user.username:
        flash(
            "You cannot delete the currently logged-in user.", "business-profile_error"
        )
        return redirect(url_for("business_profile.business_profile"))

    User.delete(username_to_delete)
    return redirect(url_for("business_profile.business_profile"))
