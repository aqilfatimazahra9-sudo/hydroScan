from flask import Blueprint, request, jsonify
from config import get_db

alertes_bp = Blueprint('alertes', __name__)


# ── GET /api/alertes/<session_id>
@alertes_bp.route('/alertes/<int:session_id>', methods=['GET'])
def get_alertes(session_id):
    conn   = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, timestamp, type_alerte, parametre,
               valeur_lue, valeur_seuil, niveau, message, resolue
        FROM alertes
        WHERE session_id = ?
        ORDER BY timestamp DESC
    """, (session_id,))
    rows = cursor.fetchall()
    conn.close()

    return jsonify([{
        'id'          : r[0],
        'timestamp'   : str(r[1]),
        'type_alerte' : r[2],
        'parametre'   : r[3],
        'valeur_lue'  : r[4],
        'valeur_seuil': r[5],
        'niveau'      : r[6],
        'message'     : r[7],
        'resolue'     : bool(r[8])
    } for r in rows]), 200


# ── PUT /api/alertes/<id>/resoudre
@alertes_bp.route('/alertes/<int:id>/resoudre', methods=['PUT'])
def resoudre_alerte(id):
    conn   = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE alertes
        SET resolue = 1, resolue_at = GETDATE()
        WHERE id = ?
    """, (id,))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Alerte résolue'}), 200


# ── GET /api/alertes/actives
@alertes_bp.route('/alertes/actives', methods=['GET'])
def get_alertes_actives():
    conn   = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM v_alertes_actives
        ORDER BY timestamp DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    return jsonify([{
        'id'          : r[0],
        'session_id'  : r[1],
        'huile'       : r[2],
        'timestamp'   : str(r[3]),
        'type_alerte' : r[4],
        'parametre'   : r[5],
        'valeur_lue'  : r[6],
        'valeur_seuil': r[7],
        'niveau'      : r[8],
        'message'     : r[9]
    } for r in rows]), 200