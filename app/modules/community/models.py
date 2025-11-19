from datetime import datetime

from app import db

community_members = db.Table(
    'community_members',
    db.Column('community_id', db.Integer, db.ForeignKey('community.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)


class Community(db.Model):
    __tablename__ = 'community'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False, unique=True)
    description = db.Column(db.String(128), nullable=True)
    creationDate = db.Column(db.DateTime, default=datetime.utcnow)

    members = db.relationship('User', secondary=community_members, back_populates='communities')

    def __repr__(self):
        return f"<Community {self.name}>"
