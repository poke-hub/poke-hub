from flask import render_template, redirect, url_for, flash, request, abort
from app import db
from app.modules.community.forms import CommunityForm, ProposeDatasetForm
from app.modules.community.models import Community, CommunityDatasetRequest
from app.modules.community import community_bp
from app.modules.dataset.models import DataSet
from flask_login import login_required, current_user
from datetime import datetime

@community_bp.route('/list', methods=["GET"])
@login_required
def list_communities():
    communities = Community.query.all()
    return render_template('community/list_communities.html', communities=communities)

@community_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_community():
    form = CommunityForm()
    if form.validate_on_submit():
        existing = Community.query.filter_by(name=form.name.data).first()
        if existing:
            flash('A community with this name already exists.', 'danger')
            return redirect(url_for('community.create_community'))

        new_community = Community(
            name=form.name.data,
            description=form.description.data,
        )

        new_community.curators.append(current_user)
        new_community.members.append(current_user)

        db.session.add(new_community)
        db.session.commit()

        flash('Community created successfully!', 'success')
        return redirect(url_for('community.view_community', community_id=new_community.id))
    return render_template("community/create.html", form=form)


@community_bp.route('/view/<int:community_id>', methods=["GET"])
@login_required
def view_community(community_id):
    community = Community.query.get(community_id)
    if not community:
        flash('Community not found!', 'danger')
        return redirect(url_for('community.list_communities'))
    propose_form = ProposeDatasetForm()
    return render_template('community/view_community.html', community=community, propose_form=propose_form)


@community_bp.route('/join/<int:community_id>', methods=['POST'])
@login_required
def join_community(community_id):
    community = Community.query.get(community_id)
    if not community:
        flash('Community not found!', 'danger')
        return redirect(url_for('community.list_communities'))
    if community in current_user.communities:
        flash('You are already a member of this community.', 'info')
        return redirect(url_for('community.view_community', community_id=community.id))
    current_user.communities.append(community)
    db.session.commit()
    flash(f'You have successfully joined the community: {community.name}', 'success')
    return redirect(url_for('community.view_community', community_id=community.id))


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


@community_bp.route('/propose/<int:community_id>', methods=['GET', 'POST'])
@login_required
def propose_dataset(community_id):
    community = Community.query.get_or_404(community_id)
    form = ProposeDatasetForm()

    available_datasets = [ds for ds in current_user.data_sets if ds.community_id != community.id]

    if not available_datasets:
        flash("No tienes datasets disponibles para proponer.", "warning")
        return redirect(url_for("community.view_community", community_id=community.id))

    if form.validate_on_submit():
        dataset_id = form.dataset_id.data
        message = form.message.data

        dataset = next((ds for ds in available_datasets if str(ds.id) == str(dataset_id)), None)
        if dataset is None:
            flash("Dataset inválido o no disponible para proponer.", "danger")
            return redirect(url_for("community.request_dataset", community_id=community.id))

        existing = CommunityDatasetRequest.query.filter_by(
            community_id=community.id,
            dataset_id=dataset.id,
            status='pending'
        ).first()
        if existing:
            flash("Ya existe una solicitud pendiente para este dataset en la comunidad.", "info")
            return redirect(url_for("community.view_community", community_id=community.id))

        req = CommunityDatasetRequest(
            community_id=community.id,
            dataset_id=dataset.id,
            requester_id=current_user.id,
            message=message,
            status='pending'
        )

        db.session.add(req)
        db.session.commit()

        flash("Solicitud enviada correctamente. Los curadores la revisarán pronto.", "success")
        return redirect(url_for("community.view_community", community_id=community.id))

    return render_template(
        "community/request_dataset.html",
        community=community,
        datasets=available_datasets,
        form=form
    )


@community_bp.route("/<int:community_id>/review-requests")
@login_required
def review_requests(community_id):
    community = Community.query.get_or_404(community_id)

    if current_user not in community.curators:
        flash("No tienes permisos para revisar solicitudes.", "danger")
        return redirect(url_for("community.view_community", community_id=community.id))

    requests_list = CommunityDatasetRequest.query.filter_by(
        community_id=community.id
    ).order_by(CommunityDatasetRequest.created_at.desc()).all()

    return render_template(
        "community/review_requests.html",
        community=community,
        requests=requests_list
    )


@community_bp.route("/request/<int:req_id>/accept", methods=["POST"])
@login_required
def accept_request(req_id):
    req = CommunityDatasetRequest.query.get_or_404(req_id)
    community = req.community

    if current_user not in community.curators:
        flash("No tienes permisos.", "danger")
        return redirect(url_for("community.review_requests", community_id=community.id))

    req.status = "accepted"

    req.dataset.community_id = community.id

    db.session.commit()

    flash("Dataset aceptado e incluido en la comunidad.", "success")
    return redirect(url_for("community.review_requests", community_id=community.id))


@community_bp.route("/request/<int:req_id>/reject", methods=["POST"])
@login_required
def reject_request(req_id):
    req = CommunityDatasetRequest.query.get_or_404(req_id)
    community = req.community

    if current_user not in community.curators:
        flash("No tienes permisos.", "danger")
        return redirect(url_for("community.review_requests", community_id=community.id))

    req.status = "rejected"
    db.session.commit()

    flash("Solicitud rechazada.", "warning")
    return redirect(url_for("community.review_requests", community_id=community.id))
