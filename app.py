import os
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'labmath_secret_123')
# Utilise DATABASE_URL de Render, sinon crée un fichier sqlite local
database_url = os.environ.get('DATABASE_URL', 'sqlite:///labmath.db')
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- MODELES ---

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

# --- ROUTES AUTH & NAVIGATION ---

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    # Redirige la racine vers le dashboard ou le login
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

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
    nouvelle = Activite(
        titre=request.form['titre'], 
        description=request.form['description']
    )
    db.session.add(nouvelle)
    db.session.commit()
    flash('Activité publiée avec succès !')
    return redirect(url_for('dashboard'))

@app.route('/admin/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- ROUTES API (Pour le site web principal) ---

@app.route('/api/activites', methods=['GET'])
def get_activites():
    activites = Activite.query.order_by(Activite.date_publication.desc()).all()
    return jsonify([{
        "id": a.id,
        "titre": a.titre,
        "description": a.description,
        "date": a.date_publication.strftime('%d/%m/%Y')
    } for a in activites])

# --- INITIALISATION ---

def setup_database():
    with app.app_context():
        db.create_all()
        # Création d'un compte admin par défaut s'il n'y en a aucun
        if not User.query.filter_by(username='admin').first():
            hashed_pwd = generate_password_hash('Labmath2024!') # Changez ce mot de passe !
            default_admin = User(username='admin', password=hashed_pwd)
            db.session.add(default_admin)
            db.session.commit()
            print("Compte admin par défaut créé : admin / Labmath2024!")

if __name__ == '__main__':
    setup_database()
    app.run(debug=True)
else:
    # Pour le déploiement Gunicorn sur Render
    setup_database()