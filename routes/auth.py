from flask import Blueprint, request, jsonify, session
from config import get_db
import hashlib

auth_bp = Blueprint('auth', __name__)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ── POST /api/login
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email    = data.get('email', '').strip()
    password = data.get('password', '').strip()

    if not email or not password:
        return jsonify({'error': 'Email et mot de passe requis'}), 400
    print("EMAIL:", email)
    print("PASSWORD:", password)
    print("HASH:", hash_password(password))

    conn   = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nom, email, role, actif
        FROM users
        WHERE email = ? AND password_hash = ?
    """, (email, hash_password(password)))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return jsonify({'error': 'Email ou mot de passe incorrect'}), 401

    if not user[4]:
        return jsonify({'error': 'Compte désactivé'}), 403

    return jsonify({
        'message'  : 'Connexion réussie',
        'user_id'  : user[0],
        'nom'      : user[1],
        'email'    : user[2],
        'role'     : user[3]
    }), 200


# ── POST /api/logout
@auth_bp.route('/logout', methods=['POST'])
def logout():
    return jsonify({'message': 'Déconnecté'}), 200


# ── POST /api/register (باش تزيد users)
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    conn   = get_db()
    cursor = conn.cursor()

    # تحقق واش email كاين
    cursor.execute("SELECT id FROM users WHERE email = ?", (data['email'],))
    if cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Email déjà utilisé'}), 409

    cursor.execute("""
        INSERT INTO users (nom, email, password_hash, role, actif)
        VALUES (?, ?, ?, ?, 1)
    """, (
        data['nom'],
        data['email'],
        hash_password(data['password']),
        data.get('role', 'operator')
    ))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Utilisateur créé'}), 201