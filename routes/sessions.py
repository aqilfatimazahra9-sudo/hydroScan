from flask import Blueprint, request, jsonify
from config import get_db

sessions_bp = Blueprint('sessions', __name__)


# ── POST /api/sessions — بداية session جديدة
@sessions_bp.route('/sessions', methods=['POST'])
@sessions_bp.route('/sessions/start', methods=['POST'])
def start_session():
    data = request.get_json()

    user_id  = data.get('user_id')
    huile_id = data.get('huile_id')

    if not user_id or not huile_id:
        return jsonify({'error': 'user_id et huile_id requis'}), 400

    conn   = get_db()
    cursor = conn.cursor()

    # إيقاف sessions السابقة ديال نفس المستخدم
    cursor.execute("""
        UPDATE sessions_reacteur
        SET statut = 'termine', fin = GETDATE()
        WHERE user_id = ? AND statut = 'en_cours'
    """, (user_id,))

    # بداية session جديدة
    cursor.execute("""
        INSERT INTO sessions_reacteur (user_id, huile_id, statut)
        OUTPUT INSERTED.id
        VALUES (?, ?, 'en_cours')
    """, (user_id, huile_id))

    session_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()

    return jsonify({
        'message'   : 'Session démarrée',
        'session_id': session_id
    }), 201


# ── PUT /api/sessions/<id>/stop — إيقاف session
@sessions_bp.route('/sessions/<int:id>/stop', methods=['PUT'])
def stop_session(id):
    conn   = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE sessions_reacteur
        SET statut = 'termine', fin = GETDATE()
        WHERE id = ?
    """, (id,))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Session arrêtée'}), 200


# ── GET /api/sessions — كل Sessions
@sessions_bp.route('/sessions', methods=['GET'])
def get_sessions():
    conn   = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.id, u.nom, h.nom, s.debut, s.fin, s.statut
        FROM sessions_reacteur s
        JOIN users  u ON s.user_id  = u.id
        JOIN huiles h ON s.huile_id = h.id
        ORDER BY s.debut DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    return jsonify([{
        'id'       : r[0],
        'operateur': r[1],
        'huile'    : r[2],
        'debut'    : str(r[3]),
        'fin'      : str(r[4]) if r[4] else None,
        'statut'   : r[5]
    } for r in rows]), 200


# ── GET /api/sessions/active — Session en cours
@sessions_bp.route('/sessions/active', methods=['GET'])
def get_active_session():
    user_id = request.args.get('user_id')

    conn   = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.id, h.nom, h.id, s.debut
        FROM sessions_reacteur s
        JOIN huiles h ON s.huile_id = h.id
        WHERE s.statut = 'en_cours' AND s.user_id = ?
    """, (user_id,))
    r = cursor.fetchone()
    conn.close()

    if not r:
        return jsonify({'active': False}), 200

    return jsonify({
        'active'    : True,
        'session_id': r[0],
        'huile'     : r[1],
        'huile_id'  : r[2],
        'debut'     : str(r[3])
    }), 200


@sessions_bp.route('/sessions/stop', methods=['POST'])
def stop_session_from_body():
    data = request.get_json()
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({'error': 'session_id requis'}), 400

    return stop_session(session_id)
