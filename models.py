from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Activite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date_publication = db.Column(db.DateTime, server_default=db.func.now())

class Offre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poste = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=False)
    active = db.Column(db.Boolean, default=True)