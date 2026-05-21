from flask import Blueprint, request, jsonify
from config import get_db

mesures_bp = Blueprint('mesures', __name__)

@mesures_bp.route('/mesures', methods=['POST'])
def add_mesure():
    data = request.get_json()

    conn   = get_db()
    cursor = conn.cursor()

    # مقارنة مع ranges ديال الزيت
    cursor.execute("""
        SELECT h.temp_max, h.pression_max, h.debit_min, h.rendement_min
        FROM sessions_reacteur s
        JOIN huiles h ON s.huile_id = h.id
        WHERE s.id = ?
    """, (data['session_id'],))
    huile = cursor.fetchone()

    statut = 'normal'
    if data['temperature'] > huile[0]: statut = 'critique'
    elif data['pression']  > huile[1]: statut = 'critique'
    elif data['debit_h2']  < huile[2]: statut = 'alerte'
    elif data['rendement'] < huile[3]: statut = 'alerte'

    cursor.execute("""
        INSERT INTO mesures_reacteur
        (session_id, temperature, pression, debit_h2, rendement, statut_global)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data['session_id'],
        data['temperature'],
        data['pression'],
        data['debit_h2'],
        data['rendement'],
        statut
    ))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Mesure enregistrée', 'statut': statut}), 201


@mesures_bp.route('/mesures/<int:session_id>', methods=['GET'])
def get_mesures(session_id):
    conn   = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT TOP 20 timestamp, temperature, pression,
                      debit_h2, rendement, statut_global
        FROM mesures_reacteur
        WHERE session_id = ?
        ORDER BY timestamp DESC
    """, (session_id,))
    rows = cursor.fetchall()
    conn.close()

    mesures = []
    for r in rows:
        mesures.append({
            'timestamp'   : str(r[0]),
            'temperature' : r[1],
            'pression'    : r[2],
            'debit_h2'    : r[3],
            'rendement'   : r[4],
            'statut'      : r[5]
        })

    return jsonify(mesures), 200