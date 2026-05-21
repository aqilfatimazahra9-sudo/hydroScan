from flask import Blueprint, jsonify, request
from config import get_db

huiles_bp = Blueprint('huiles', __name__)

@huiles_bp.route('/huiles', methods=['GET'])
def get_huiles():
    conn   = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nom, description,
               temp_min, temp_opt, temp_max,
               pression_min, pression_opt, pression_max,
               debit_min, debit_opt, debit_max,
               duree_opt_min, rendement_opt
        FROM huiles
    """)
    rows = cursor.fetchall()
    conn.close()

    huiles = []
    for r in rows:
        huiles.append({
            'id'          : r[0],
            'nom'         : r[1],
            'description' : r[2],
            'temperature' : {'min': r[3], 'opt': r[4], 'max': r[5]},
            'pression'    : {'min': r[6], 'opt': r[7], 'max': r[8]},
            'debit_h2'    : {'min': r[9], 'opt': r[10], 'max': r[11]},
            'duree_opt'   : r[12],
            'rendement_opt': r[13]
        })

    return jsonify(huiles), 200


@huiles_bp.route('/huiles/<int:id>', methods=['GET'])
def get_huile(id):
    conn   = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nom, description,
               temp_min, temp_opt, temp_max,
               pression_min, pression_opt, pression_max,
               debit_min, debit_opt, debit_max,
               duree_min_min, duree_opt_min, duree_max_min,
               rendement_min, rendement_opt
        FROM huiles
        WHERE id = ?
    """, (id,))
    r = cursor.fetchone()
    conn.close()

    if not r:
        return jsonify({'error': 'Huile introuvable'}), 404

    return jsonify({
        'id'          : r[0],
        'nom'         : r[1],
        'description' : r[2],
        'temperature' : {'min': r[3], 'opt': r[4], 'max': r[5]},
        'pression'    : {'min': r[6], 'opt': r[7], 'max': r[8]},
        'debit_h2'    : {'min': r[9], 'opt': r[10], 'max': r[11]},
        'duree'       : {'min': r[12], 'opt': r[13], 'max': r[14]},
        'rendement'   : {'min': r[15], 'opt': r[16]}
    }), 200


@huiles_bp.route('/huiles/<int:id>', methods=['PUT'])
def update_huile(id):
    data = request.get_json() or {}

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM huiles WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Huile introuvable'}), 404

    cursor.execute("""
        UPDATE huiles
        SET nom = ?,
            description = ?,
            temp_min = ?, temp_opt = ?, temp_max = ?,
            pression_min = ?, pression_opt = ?, pression_max = ?,
            debit_min = ?, debit_opt = ?, debit_max = ?,
            duree_min_min = ?, duree_opt_min = ?, duree_max_min = ?,
            rendement_min = ?, rendement_opt = ?
        WHERE id = ?
    """, (
        data.get('nom'),
        data.get('description'),
        data.get('temperature', {}).get('min'),
        data.get('temperature', {}).get('opt'),
        data.get('temperature', {}).get('max'),
        data.get('pression', {}).get('min'),
        data.get('pression', {}).get('opt'),
        data.get('pression', {}).get('max'),
        data.get('debit_h2', {}).get('min'),
        data.get('debit_h2', {}).get('opt'),
        data.get('debit_h2', {}).get('max'),
        data.get('duree', {}).get('min'),
        data.get('duree', {}).get('opt'),
        data.get('duree', {}).get('max'),
        data.get('rendement', {}).get('min'),
        data.get('rendement', {}).get('opt'),
        id
    ))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Huile mise a jour'}), 200
