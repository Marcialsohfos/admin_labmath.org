import os
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from flask_cors import CORS  # Très important pour lier les deux sites
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
CORS(app) # Autorise votre site web à appeler cette API

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'votre_cle_secrete_ici')
# Si pas de DB externe, on utilise un fichier local sqlite
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///labmath_data.db').replace("postgres://", "postgresql://")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- MODELES DE DONNÉES ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Activite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date_publication = db.Column(db.DateTime, default=datetime.utcnow)

class Offre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poste = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=False)
    active = db.Column(db.Boolean, default=True)

# --- ROUTES ADMIN (HTML) ---

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Identifiants incorrects')
    return render_template('login.html')

@app.route('/admin/dashboard')
@login_required
def dashboard():
    activites = Activite.query.order_by(Activite.date_publication.desc()).all()
    offres = Offre.query.all()
    return render_template('dashboard.html', activites=activites, offres=offres)

@app.route('/admin/add_activity', methods=['POST'])
@login_required
def add_activity():
    nouvelle = Activite(titre=request.form['titre'], description=request.form['description'])
    db.session.add(nouvelle)
    db.session.commit()
    flash('Activité publiée !')
    return redirect(url_for('dashboard'))

@app.route('/admin/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- ROUTES API (JSON pour le site principal) ---

@app.route('/api/activites', methods=['GET'])
def get_activites():
    activites = Activite.query.order_by(Activite.date_publication.desc()).all()
    return jsonify([{
        "id": a.id,
        "titre": a.titre,
        "description": a.description,
        "date": a.date_publication.strftime('%d/%m/%Y')
    } for a in activites])

@app.route('/api/offres', methods=['GET'])
def get_offres():
    offres = Offre.query.filter_by(active=True).all()
    return jsonify([{
        "id": o.id,
        "poste": o.poste,
        "details": o.details
    } for o in offres])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)