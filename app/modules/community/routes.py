from flask import abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app import db
from app.modules.community import community_bp
from app.modules.community.forms import CommunityForm, ProposeDatasetForm, UpdateCommunityForm
from app.modules.community.models import Community, CommunityDatasetRequest
from app.modules.community.services import CommunityService
from app.modules.community.utils.email import send_email
from app.modules.community.utils.files import save_image


@community_bp.route("/list", methods=["GET"])
@login_required
def list_communities():
    communities = Community.query.all()
    return render_template("community/list_communities.html", communities=communities)


@community_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_community():
    form = CommunityForm()

    if form.validate_on_submit():

        existing = Community.query.filter_by(name=form.name.data).first()
        if existing:
            flash("A community with this name already exists.", "danger")
            return redirect(url_for("community.create_community"))

        new_community = Community(
            name=form.name.data,
            description=form.description.data,
        )

        if form.logo.data:
            try:
                new_community.logo_path = save_image(form.logo.data, "communities/logos")
            except Exception as e:
                flash(f"Error uploading logo: {e}", "danger")
                return redirect(url_for("community.create_community"))

        if form.banner.data:
            try:
                new_community.banner_path = save_image(form.banner.data, "communities/banners")
            except Exception as e:
                flash(f"Error uploading banner: {e}", "danger")
                return redirect(url_for("community.create_community"))

        new_community.curators.append(current_user)
        new_community.members.append(current_user)

        db.session.add(new_community)
        db.session.commit()

        flash("Community created successfully!", "success")
        return redirect(url_for("community.view_community", community_id=new_community.id))

    return render_template("community/create_community.html", form=form)


@community_bp.route("/<int:community_id>/edit", methods=["GET", "POST"])
@login_required
def edit_community(community_id):
    community = Community.query.get_or_404(community_id)

    if current_user not in community.curators:
        abort(403)

    form = UpdateCommunityForm(obj=community)

    if form.validate_on_submit():
        community.name = form.name.data
        community.description = form.description.data

        if form.logo.data:
            community.logo_path = save_image(form.logo.data, "logos")

        if form.banner.data:
            community.banner_path = save_image(form.banner.data, "banners")

        db.session.commit()

        flash("Community updated successfully!", "success")
        return redirect(url_for("community.view_community", community_id=community.id))

    return render_template("community/edit_community.html", form=form, community=community)


@community_bp.route("/<int:community_id>/delete", methods=["POST"])
@login_required
def delete_community(community_id):
    community = Community.query.get_or_404(community_id)

    if current_user not in community.curators:
        abort(403)

    db.session.delete(community)
    db.session.commit()

    flash("Community deleted successfully.", "info")
    return redirect(url_for("community.list_communities"))


@community_bp.route("/view/<int:community_id>", methods=["GET"])
@login_required
def view_community(community_id):
    community = Community.query.get(community_id)
    if not community:
        flash("Community not found!", "danger")
        return redirect(url_for("community.list_communities"))
    propose_form = ProposeDatasetForm()
    return render_template("community/view_community.html", community=community, propose_form=propose_form)


@community_bp.route("/join/<int:community_id>", methods=["POST"])
@login_required
def join_community(community_id):
    community = Community.query.get(community_id)
    if not community:
        flash("Community not found!", "danger")
        return redirect(url_for("community.list_communities"))
    if community in current_user.communities:
        flash("You are already a member of this community.", "info")
        return redirect(url_for("community.view_community", community_id=community.id))
    current_user.communities.append(community)
    db.session.commit()
    flash(f"You have successfully joined the community: {community.name}", "success")
    return redirect(url_for("community.view_community", community_id=community.id))


@community_bp.route("/<int:community_id>/leave", methods=["POST"])
@login_required
def leave_community(community_id):
    community = Community.query.get_or_404(community_id)

    if current_user in community.members:
        community.members.remove(current_user)
        db.session.commit()
        flash("Has salido de la comunidad.", "info")
    else:
        flash("No eres miembro de la comunidad.", "warning")

    return redirect(url_for("community.view_community", community_id=community.id))


@community_bp.route("/propose/<int:community_id>", methods=["GET", "POST"])
@login_required
def propose_dataset(community_id):
    community = Community.query.get_or_404(community_id)
    form = ProposeDatasetForm()

    available_datasets = CommunityService.get_available_user_datasets_for_proposal(current_user, community)

    if not available_datasets:
        flash("You don't have any dataset available to propose.", "warning")
        return redirect(url_for("community.view_community", community_id=community.id))

    if form.validate_on_submit():
        dataset_id = form.dataset_id.data
        dataset = next((ds for ds in available_datasets if str(ds.id) == str(dataset_id)), None)

        if not dataset:
            flash("Invalid or unavailable dataset.", "danger")
            return redirect(url_for("community.propose_dataset", community_id=community.id))

        try:
            CommunityService.create_proposal(
                community=community, dataset=dataset, requester=current_user, message=form.message.data
            )
            flash("Request sent successfully!", "success")
        except ValueError as e:
            flash(str(e), "danger")

        return redirect(url_for("community.view_community", community_id=community.id))

    return render_template(
        "community/request_dataset.html", form=form, community=community, datasets=available_datasets
    )


@community_bp.route("/<int:community_id>/review-requests")
@login_required
def review_requests(community_id):
    community = Community.query.get_or_404(community_id)

    if current_user not in community.curators:
        flash("You are not allowed to review requests.", "danger")
        return redirect(url_for("community.view_community", community_id=community.id))

    requests_list = (
        CommunityDatasetRequest.query.filter_by(community_id=community.id)
        .order_by(CommunityDatasetRequest.created_at.desc())
        .all()
    )

    return render_template("community/review_requests.html", community=community, requests=requests_list)


@community_bp.route("/request/<int:req_id>/accept", methods=["POST"])
@login_required
def accept_request(req_id):
    req = CommunityDatasetRequest.query.get_or_404(req_id)
    community = req.community

    if current_user not in community.curators:
        flash("You are not allowed.", "danger")
        return redirect(url_for("community.review_requests", community_id=community.id))

    req.status = "accepted"
    req.dataset.community_id = community.id
    db.session.commit()

    send_email(
        subject=f"Your dataset was accepted in {req.community.name}",
        recipients=[req.dataset.user.email],
        body=(
            f"Hi {req.dataset.user.profile.name},\n\n"
            f"Your dataset '{req.dataset.ds_meta_data.title}' has been accepted into the community "
            f"'{req.community.name}'.\n\n"
            "Thanks for contributing, and gotta catch 'em all!!"
        ),
    )

    for member in req.community.members:
        send_email(
            subject=f"New dataset added to {req.community.name}",
            recipients=[member.email],
            body=(
                f"Hi {member.profile.name},\n\n"
                f"A new dataset '{req.dataset.ds_meta_data.title}' has been added to a community you follow: "
                f"{req.community.name}.\n\n"
                "You can view it on the platform.\n\n"
                "Best,\nUVLHub Team"
            ),
        )

    flash("Dataset accepted and included in this community.", "success")
    return redirect(url_for("community.review_requests", community_id=community.id))


@community_bp.route("/request/<int:req_id>/reject", methods=["POST"])
@login_required
def reject_request(req_id):
    req = CommunityDatasetRequest.query.get_or_404(req_id)
    community = req.community

    if current_user not in community.curators:
        flash("You are not allowed.", "danger")
        return redirect(url_for("community.review_requests", community_id=community.id))

    req.status = "rejected"
    db.session.commit()

    flash("Request rejected.", "warning")
    return redirect(url_for("community.review_requests", community_id=community.id))
