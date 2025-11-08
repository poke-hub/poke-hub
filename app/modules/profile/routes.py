from flask import abort, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.modules.auth.models import User
from app.modules.auth.services import AuthenticationService
from app.modules.dataset.models import DataSet
from app.modules.profile import profile_bp
from app.modules.profile.services import UserProfileService
from flask import jsonify, session, flash
from app.modules.profile.forms import UserProfileForm, TwoFactorEnableForm, TwoFactorDisableForm


@profile_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    auth_service = AuthenticationService()
    profile = auth_service.get_authenticated_user_profile
    if not profile:
        return redirect(url_for("public.index"))

    form = UserProfileForm()
    if request.method == "POST":
        service = UserProfileService()
        result, errors = service.update_profile(profile.id, form)
        return service.handle_service_response(
            result, errors, "profile.edit_profile", "Profile updated successfully", "profile/edit.html", form
        )

    return render_template("profile/edit.html", form=form)


@profile_bp.route("/profile/summary")
@login_required
def my_profile():
    page = request.args.get("page", 1, type=int)
    per_page = 5

    user_datasets_pagination = (
        db.session.query(DataSet)
        .filter(DataSet.user_id == current_user.id)
        .order_by(DataSet.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    total_datasets_count = db.session.query(DataSet).filter(DataSet.user_id == current_user.id).count()

    print(user_datasets_pagination.items)

    return render_template(
        "profile/summary.html",
        user_profile=current_user.profile,
        user=current_user,
        datasets=user_datasets_pagination.items,
        pagination=user_datasets_pagination,
        total_datasets=total_datasets_count,
        profile_endpoint="profile.my_profile",
    )


@profile_bp.route("/profile/<int:user_id>")
def view_profile(user_id):
    """Public view of a user's profile and their uploaded datasets."""
    page = request.args.get("page", 1, type=int)
    per_page = 5

    user = db.session.query(User).get(user_id)
    if not user:
        abort(404)

    user_datasets_pagination = (
        db.session.query(DataSet)
        .filter(DataSet.user_id == user.id)
        .order_by(DataSet.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    total_datasets_count = db.session.query(DataSet).filter(DataSet.user_id == user.id).count()

    return render_template(
        "profile/summary.html",
        user_profile=user.profile,
        user=user,
        datasets=user_datasets_pagination.items,
        pagination=user_datasets_pagination,
        total_datasets=total_datasets_count,
        profile_endpoint="profile.view_profile",
    )


@profile_bp.route("/profile/security", methods=["GET"])
@login_required
def security_settings():
    """Muestra la página de configuración de seguridad, con formularios para habilitar/deshabilitar 2FA."""
    enable_form = TwoFactorEnableForm()
    disable_form = TwoFactorDisableForm()
    return render_template(
        "profile/security.html", 
        enable_form=enable_form, 
        disable_form=disable_form
    )

@profile_bp.route('/profile/2fa/setup', methods=['POST'])
@login_required
def setup_2fa():
    """
    Paso 1: Genera un secreto y un QR para escanear.
    """
    auth_service = AuthenticationService()
    
    secret = auth_service.generate_2fa_secret() 
    uri = auth_service.get_2fa_provisioning_uri(current_user.email, secret)
    qr_base64 = auth_service.generate_qr_code_base64(uri)
    
    auth_service.set_user_2fa_secret(current_user, secret)
    
    return jsonify({'secret': secret, 'qr_base64': qr_base64})

@profile_bp.route('/profile/2fa/enable', methods=['POST'])
@login_required
def enable_2fa():
    """
    Paso 2: Verifica el token del usuario y activa el 2FA.
    """
    form = TwoFactorEnableForm()
    auth_service = AuthenticationService()
    
    if form.validate_on_submit():
        token = form.token.data
        if auth_service.verify_2fa_token(current_user, token):
            
            plain_codes, hashed_codes_json = auth_service.generate_recovery_codes()
            auth_service.set_user_2fa_recovery_codes(current_user, hashed_codes_json)
            
            auth_service.set_user_2fa_enabled(current_user, True)

            flash('2FA enabled successfully.', 'success')
            return render_template('profile/recovery_codes.html', codes=plain_codes)
        else:
            flash('Invalid code. Please try again.', 'danger')

    return redirect(url_for('profile.security_settings'))

@profile_bp.route('/profile/2fa/disable', methods=['POST'])
@login_required
def disable_2fa():
    """Desactiva 2FA si la contraseña es correcta."""
    form = TwoFactorDisableForm()
    auth_service = AuthenticationService()

    if form.validate_on_submit():
        if auth_service.check_user_password(current_user, form.password.data):
            auth_service.clear_user_2fa_data(current_user)
            flash('2FA has been disabled.', 'success')
        else:
            flash('Wrong password.', 'danger')
            
    return redirect(url_for('profile.security_settings'))