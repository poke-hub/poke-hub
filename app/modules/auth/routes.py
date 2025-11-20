from flask import flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user

from app.modules.auth import auth_bp
from app.modules.auth.forms import LoginForm, SignupForm, TwoFactorLoginForm
from app.modules.auth.models import User
from app.modules.auth.services import AuthenticationService
from app.modules.profile.services import UserProfileService

authentication_service = AuthenticationService()
user_profile_service = UserProfileService()


@auth_bp.route("/signup/", methods=["GET", "POST"])
def show_signup_form():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    form = SignupForm()
    if form.validate_on_submit():
        email = form.email.data
        if not authentication_service.is_email_available(email):
            return render_template("auth/signup_form.html", form=form, error=f"Email {email} in use")

        try:
            user = authentication_service.create_with_profile(**form.data)
        except Exception as exc:
            return render_template("auth/signup_form.html", form=form, error=f"Error creating user: {exc}")

        # Log user and create session
        login_user(user, remember=True)
        authentication_service.create_user_session(user)  # <-- CREAR SESIÓN
        return redirect(url_for("public.index"))

    return render_template("auth/signup_form.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():

        # Si login_result es True, create_user_session ya se llamó dentro de service.login()
        login_result = authentication_service.login(form.email.data, form.password.data, form.remember_me.data)

        if login_result is True:
            return redirect(url_for("public.index"))

        elif login_result is False:
            return render_template("auth/login_form.html", form=form, error="Invalid credentials")

        else:
            # Es un objeto usuario, requiere 2FA
            user = login_result
            session["2fa_user_id"] = user.id
            return redirect(url_for("auth.verify_2fa"))

    return render_template("auth/login_form.html", form=form)


@auth_bp.route("/login/verify-2fa", methods=["GET", "POST"])
def verify_2fa():
    """Página para introducir el código de 6 dígitos (Paso 2 del Login)."""

    if "2fa_user_id" not in session:
        return redirect(url_for("auth.login"))

    form = TwoFactorLoginForm()

    if form.validate_on_submit():
        user_id = session["2fa_user_id"]
        user = User.query.get(user_id)
        if not user:
            flash("Authentication failed. Please try again.", "danger")
            return redirect(url_for("auth.login"))

        token = form.token.data

        if authentication_service.verify_2fa_token(user, token):
            pass

        elif authentication_service.verify_recovery_code(user, token):
            flash("You have used a recovery code.", "warning")
            pass

        else:
            flash("Invalid code. Please try again.", "danger")
            return render_template("auth/verify_2fa.html", form=form)

        login_user(user, remember=True)
        authentication_service.create_user_session(user)  # <-- CREAR SESIÓN
        session.pop("2fa_user_id", None)
        return redirect(url_for("public.index"))

    return render_template("auth/verify_2fa.html", form=form)


@auth_bp.route("/logout")
def logout():
    authentication_service.logout_session()
    logout_user()
    return redirect(url_for("public.index"))
