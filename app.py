from flask import Flask, redirect, render_template, request, jsonify
from flask_cors import CORS
from config import get_db
from routes.auth import auth_bp
from routes.huiles import huiles_bp
from routes.sessions import sessions_bp
from routes.mesures  import mesures_bp
from routes.alertes import alertes_bp
from routes.frontend_api import frontend_api_bp
from routes.simulation import start_simulation_thread
import hashlib




app = Flask(__name__)
CORS(app)
app.register_blueprint(huiles_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(sessions_bp, url_prefix='/api')
app.register_blueprint(mesures_bp,  url_prefix='/api')
app.register_blueprint(alertes_bp, url_prefix='/api')
app.register_blueprint(frontend_api_bp, url_prefix='/api')


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def index():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        data = request.get_json() or {}
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nom, email, role, actif
            FROM users
            WHERE email = ? AND password_hash = ?
        """, (email, hash_password(password)))
        user = cursor.fetchone()
        conn.close()

        if not user:
            return jsonify({'success': False, 'message': 'Identifiants incorrects'}), 401
        if not user[4]:
            return jsonify({'success': False, 'message': 'Compte desactive'}), 403

        return jsonify({
            'success': True,
            'user_id': user[0],
            'nom': user[1],
            'email': user[2],
            'role': user[3]
        }), 200

    return render_template('login.html')

@app.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html')


@app.route('/historique')
def historique_page():
    return render_template('historique.html')


@app.route('/alertes')
def alertes_page():
    return render_template('alertes.html')


@app.route('/settings')
def settings_page():
    return render_template('settings.html')
@app.route('/api/sessions/start-simulation', methods=['POST'])
def start_sim():
    data       = request.get_json()
    session_id = data['session_id']
    huile_id   = data['huile_id']
    start_simulation_thread(session_id, huile_id)
    return jsonify({'message': 'Simulation démarrée'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
