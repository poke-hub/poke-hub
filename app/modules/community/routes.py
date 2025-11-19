from flask import render_template, redirect, url_for, flash
from app import db
from app.modules.community.forms import CommunityForm
from app.modules.community.models import Community
from app.modules.community import community_bp
from flask_login import login_required, current_user


@community_bp.route('/list', methods=["GET", "POST"])
@login_required
def list_communities():
    communities = Community.query.all()

    return render_template('community/list_communities.html', communities=communities)


@community_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_community():

    form = CommunityForm()
    if form.validate_on_submit():
        new_community = Community(
            name=form.name.data,
            description=form.description.data,
        )
        # To move to the service layer
        existing_community = Community.query.filter_by(name=form.name.data).first()
        if existing_community:
            flash('A community with this name already exists.', 'danger')
            return redirect(url_for('community.create_community'))
        db.session.add(new_community)
        db.session.commit()

        flash('Community created successfully!', 'success')
        return redirect(url_for('public.index'))

    return render_template("community/create.html", form=form)

@community_bp.route('/join/<int:community_id>', methods=['POST'])
@login_required
def join_community(community_id):
    community = Community.query.get(community_id)
    
    if not community:
        flash('Community not found!', 'danger')
        return redirect(url_for('community.list_communities'))

    if community in current_user.communities:
        flash('You are already a member of this community.', 'info')
        return redirect(url_for('community.list_communities'))

    current_user.communities.append(community)
    db.session.commit()
    
    flash(f'You have successfully joined the community: {community.name}', 'success')
    return redirect(url_for('community.list_communities'))

@community_bp.route('/view/<int:community_id>', methods=["GET"])
@login_required
def view_community(community_id):
    """Displays details of a specific community."""
    community = Community.query.get(community_id)

    if not community:
        flash('Community not found!', 'danger')
        return redirect(url_for('community.list_communities'))

    return render_template('community/view_community.html', community=community)
