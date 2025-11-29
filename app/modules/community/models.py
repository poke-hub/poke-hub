from datetime import datetime
from app import db

community_members = db.Table(
    'community_members',
    db.Column('community_id', db.Integer, db.ForeignKey('community.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

community_curators = db.Table(
    'community_curators',
    db.Column('community_id', db.Integer, db.ForeignKey('community.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)


class Community(db.Model):
    __tablename__ = 'community'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)
    description = db.Column(db.String(512), nullable=True)
    creation_date = db.Column(db.DateTime, default=datetime.utcnow)

    logo_path = db.Column(db.String(256), nullable=True)
    banner_path = db.Column(db.String(256), nullable=True)

    members = db.relationship('User', secondary=community_members, back_populates='communities')
    curators = db.relationship('User', secondary=community_curators, back_populates='curated_communities')

    datasets = db.relationship('DataSet', back_populates='community', lazy='dynamic')

    dataset_requests = db.relationship('CommunityDatasetRequest', back_populates='community', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Community {self.name}>"

class CommunityDatasetRequest(db.Model):
    __tablename__ = 'community_dataset_request'
    id = db.Column(db.Integer, primary_key=True)
    community_id = db.Column(db.Integer, db.ForeignKey('community.id'), nullable=False)
    dataset_id = db.Column(db.Integer, db.ForeignKey('data_set.id'), nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    status = db.Column(db.String(16), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    decision_at = db.Column(db.DateTime, nullable=True)
    message = db.Column(db.String(1024), nullable=True)

    community = db.relationship('Community', back_populates='dataset_requests')
    dataset = db.relationship('DataSet', back_populates='community_requests')
    requester = db.relationship('User')

    def accept(self, actor):
        self.status = 'accepted'
        self.decision_at = datetime.utcnow()
        self.dataset.community = self.community
        db.session.add(self)
        db.session.add(self.dataset)
        db.session.commit()

    def reject(self, actor):
        self.status = 'rejected'
        self.decision_at = datetime.utcnow()
        db.session.add(self)
        db.session.commit()
