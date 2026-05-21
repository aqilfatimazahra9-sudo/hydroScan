from flask import Blueprint, Response, jsonify, request
from config import get_db
import csv
import io
import random

frontend_api_bp = Blueprint('frontend_api', __name__)

SESSION_LIMIT_COLUMNS = [
    ('lim_temp_min', 'float'), ('lim_temp_opt', 'float'), ('lim_temp_max', 'float'),
    ('lim_pression_min', 'float'), ('lim_pression_opt', 'float'), ('lim_pression_max', 'float'),
    ('lim_debit_min', 'float'), ('lim_debit_opt', 'float'), ('lim_debit_max', 'float'),
    ('lim_duree_min', 'int'), ('lim_duree_opt', 'int'), ('lim_duree_max', 'int'),
    ('lim_rendement_min', 'float'), ('lim_rendement_opt', 'float')
]


def _ensure_session_limit_columns(cursor):
    for column, sql_type in SESSION_LIMIT_COLUMNS:
        cursor.execute("""
            IF COL_LENGTH('sessions_reacteur', ?) IS NULL
            BEGIN
                EXEC('ALTER TABLE sessions_reacteur ADD ' + ? + ' ' + ? + ' NULL')
            END
        """, (column, column, sql_type))



def _rand_range(min_value, max_value, digits=1):
    return round(random.uniform(min_value, max_value), digits)


def _get_live_session(cursor):
    cursor.execute("""
        SELECT TOP 1 id, huile_id
        FROM sessions_reacteur
        WHERE statut = 'en_cours'
        ORDER BY debut DESC
    """)
    row = cursor.fetchone()
    if row:
        return row[0], row[1]

    return None, None


def _create_live_session(cursor, huile_id=None):
    _ensure_session_limit_columns(cursor)
    if huile_id:
        cursor.execute("""
            SELECT id, temp_min, temp_opt, temp_max,
                   pression_min, pression_opt, pression_max,
                   debit_min, debit_opt, debit_max,
                   duree_min_min, duree_opt_min, duree_max_min,
                   rendement_min, rendement_opt
            FROM huiles
            WHERE id = ?
        """, (huile_id,))
    else:
        cursor.execute("""
            SELECT TOP 1 id, temp_min, temp_opt, temp_max,
                   pression_min, pression_opt, pression_max,
                   debit_min, debit_opt, debit_max,
                   duree_min_min, duree_opt_min, duree_max_min,
                   rendement_min, rendement_opt
            FROM huiles
            ORDER BY id
        """)

    huile = cursor.fetchone()
    if not huile:
        return None, None

    cursor.execute("""
        INSERT INTO sessions_reacteur
        (user_id, huile_id, statut,
         lim_temp_min, lim_temp_opt, lim_temp_max,
         lim_pression_min, lim_pression_opt, lim_pression_max,
         lim_debit_min, lim_debit_opt, lim_debit_max,
         lim_duree_min, lim_duree_opt, lim_duree_max,
         lim_rendement_min, lim_rendement_opt)
        OUTPUT INSERTED.id
        VALUES (1, ?, 'en_cours', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (huile[0], *huile[1:]))
    return cursor.fetchone()[0], huile[0]


def _load_huile(cursor, huile_id):
    cursor.execute("""
        SELECT temp_min, temp_opt, temp_max,
               pression_min, pression_opt, pression_max,
               debit_min, debit_opt, debit_max,
               rendement_min, rendement_opt
        FROM huiles
        WHERE id = ?
    """, (huile_id,))
    return cursor.fetchone()


def _load_session_limits(cursor, session_id, huile_id):
    _ensure_session_limit_columns(cursor)
    cursor.execute("""
        SELECT COALESCE(s.lim_temp_min, h.temp_min),
               COALESCE(s.lim_temp_opt, h.temp_opt),
               COALESCE(s.lim_temp_max, h.temp_max),
               COALESCE(s.lim_pression_min, h.pression_min),
               COALESCE(s.lim_pression_opt, h.pression_opt),
               COALESCE(s.lim_pression_max, h.pression_max),
               COALESCE(s.lim_debit_min, h.debit_min),
               COALESCE(s.lim_debit_opt, h.debit_opt),
               COALESCE(s.lim_debit_max, h.debit_max),
               COALESCE(s.lim_rendement_min, h.rendement_min),
               COALESCE(s.lim_rendement_opt, h.rendement_opt)
        FROM sessions_reacteur s
        JOIN huiles h ON s.huile_id = h.id
        WHERE s.id = ? AND s.huile_id = ?
    """, (session_id, huile_id))
    return cursor.fetchone()


def _simulate_value(min_value, opt_value, max_value, digits=1):
    if random.random() < 0.16:
        if random.random() < 0.5:
            return _rand_range(max_value + 0.1, max_value + max(1, (max_value - opt_value) * 0.6), digits)
        return _rand_range(max(0, min_value - max(1, (opt_value - min_value) * 0.6)), min_value - 0.1, digits)

    return _rand_range(
        opt_value - (opt_value - min_value) * 0.4,
        opt_value + (max_value - opt_value) * 0.4,
        digits
    )


def _save_alert(cursor, session_id, type_alerte, parametre, valeur_lue, valeur_seuil, niveau):
    message = f"{type_alerte}: {valeur_lue} / seuil {valeur_seuil}"
    cursor.execute("""
        INSERT INTO alertes
        (session_id, type_alerte, parametre, valeur_lue, valeur_seuil, niveau, message)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (session_id, type_alerte, parametre, valeur_lue, valeur_seuil, niveau, message))


@frontend_api_bp.route('/live-data', methods=['GET'])
def live_data():
    conn = get_db()
    cursor = conn.cursor()

    session_id, huile_id = _get_live_session(cursor)
    if not session_id:
        conn.close()
        return jsonify({'error': 'Monitoring non demarre'}), 409

    h = _load_session_limits(cursor, session_id, huile_id)
    temperature = _simulate_value(h[0], h[1], h[2], 1)
    pression = _simulate_value(h[3], h[4], h[5], 2)
    debit = _simulate_value(h[6], h[7], h[8], 1)
    rendement = _rand_range(max(0, h[10] - 16), min(100, h[10] + 2), 1) if random.random() < 0.14 else _rand_range(h[10] - 4, min(100, h[10] + 2), 1)

    statut = 'normal'
    if temperature > h[2] or pression > h[5] or debit > h[8]:
        statut = 'critique'
    elif temperature < h[0] or pression < h[3] or debit < h[6] or rendement < h[10] - 10:
        statut = 'alerte'

    cursor.execute("""
        INSERT INTO mesures_reacteur
        (session_id, temperature, pression, debit_h2, rendement, statut_global)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (session_id, temperature, pression, debit, rendement, statut))

    if temperature > h[2]:
        _save_alert(cursor, session_id, 'surchauffe', 'temperature', temperature, h[2], 'danger')
    if pression > h[5]:
        _save_alert(cursor, session_id, 'surpression', 'pression', pression, h[5], 'danger')
    if debit > h[8]:
        _save_alert(cursor, session_id, 'debit_eleve', 'debit_h2', debit, h[8], 'danger')
    if debit < h[6]:
        _save_alert(cursor, session_id, 'debit_faible', 'debit_h2', debit, h[6], 'warning')
    if rendement < h[10] - 10:
        _save_alert(cursor, session_id, 'rendement_bas', 'rendement', rendement, h[10] - 10, 'warning')

    stop_reason = None
    if temperature > h[2]:
        stop_reason = f"Temperature depasse le maximum DB ({temperature} > {h[2]})"
    elif pression > h[5]:
        stop_reason = f"Pression depasse le maximum DB ({pression} > {h[5]})"
    elif debit > h[8]:
        stop_reason = f"Debit H2 depasse le maximum DB ({debit} > {h[8]})"

    if stop_reason:
        cursor.execute("""
            UPDATE sessions_reacteur
            SET statut = 'termine', fin = GETDATE(), notes = ?
            WHERE id = ?
        """, (stop_reason, session_id))

    conn.commit()
    conn.close()

    return jsonify({
        'temperature': temperature,
        'pression': pression,
        'debit': debit,
        'rendement': rendement,
        'conversion': rendement,
        'status': statut,
        'session_id': session_id,
        'stopped': bool(stop_reason),
        'stop_reason': stop_reason
    }), 200


@frontend_api_bp.route('/monitoring/start', methods=['POST'])
def start_monitoring():
    data = request.get_json(silent=True) or {}
    selected_huile_id = data.get('huile_id')

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE sessions_reacteur
        SET statut = 'termine', fin = GETDATE()
        WHERE statut = 'en_cours'
    """)
    session_id, huile_id = _create_live_session(cursor, selected_huile_id)

    if not session_id:
        conn.close()
        return jsonify({'error': 'Aucune huile configuree'}), 404

    conn.commit()
    conn.close()
    return jsonify({'success': True, 'session_id': session_id, 'huile_id': huile_id}), 200


@frontend_api_bp.route('/monitoring/status', methods=['GET'])
def monitoring_status():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT TOP 1 s.id, s.huile_id, h.nom, s.debut, s.statut, s.notes
        FROM sessions_reacteur s
        JOIN huiles h ON s.huile_id = h.id
        WHERE s.statut = 'en_cours'
        ORDER BY s.debut DESC
    """)
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({'running': False}), 200

    return jsonify({
        'running': True,
        'session_id': row[0],
        'huile_id': row[1],
        'huile': row[2],
        'debut': str(row[3]),
        'statut': row[4],
        'notes': row[5]
    }), 200


@frontend_api_bp.route('/monitoring/stop', methods=['POST'])
def stop_monitoring():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE sessions_reacteur
        SET statut = 'termine', fin = GETDATE()
        WHERE statut = 'en_cours'
    """)
    stopped = cursor.rowcount
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'stopped': stopped}), 200


def _alerts_filters_from_request():
    session_id = request.args.get('session_id') or ''
    date_start = request.args.get('date_start') or ''
    date_end = request.args.get('date_end') or ''
    niveau = request.args.get('niveau') or ''
    status = request.args.get('status') or ''

    filters = []
    params = []
    if session_id:
        filters.append("a.session_id = ?")
        params.append(session_id)
    if date_start:
        filters.append("CAST(a.timestamp AS date) >= ?")
        params.append(date_start)
    if date_end:
        filters.append("CAST(a.timestamp AS date) <= ?")
        params.append(date_end)
    if niveau:
        filters.append("a.niveau = ?")
        params.append(niveau)
    if status == 'open':
        filters.append("a.resolue = 0")
    elif status == 'resolved':
        filters.append("a.resolue = 1")

    where_clause = "WHERE " + " AND ".join(filters) if filters else ""
    return where_clause, params


@frontend_api_bp.route('/alerts', methods=['GET'])
def alerts():
    where_clause, params = _alerts_filters_from_request()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT TOP 500
               a.id, a.session_id, h.nom, a.timestamp,
               a.type_alerte, a.parametre, a.valeur_lue,
               a.valeur_seuil, a.niveau, a.message,
               a.resolue, a.resolue_at, s.debut, s.fin, s.statut
        FROM alertes a
        JOIN sessions_reacteur s ON a.session_id = s.id
        JOIN huiles h ON s.huile_id = h.id
        {where_clause}
        ORDER BY a.timestamp DESC
    """, params)
    rows = cursor.fetchall()
    conn.close()

    return jsonify([{
        'id': r[0],
        'session_id': r[1],
        'huile': r[2],
        'timestamp': str(r[3]),
        'type_alerte': r[4],
        'parametre': r[5],
        'valeur_lue': r[6],
        'valeur_seuil': r[7],
        'niveau': r[8],
        'type': r[8],
        'message': r[9],
        'resolue': bool(r[10]),
        'resolue_at': str(r[11]) if r[11] else None,
        'session_debut': str(r[12]) if r[12] else None,
        'session_fin': str(r[13]) if r[13] else None,
        'session_statut': r[14]
    } for r in rows]), 200


@frontend_api_bp.route('/alerts/sessions', methods=['GET'])
def alert_sessions():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT TOP 200
               s.id, h.nom, s.debut, s.fin, s.statut, COUNT(a.id) AS nb_alertes
        FROM sessions_reacteur s
        JOIN huiles h ON s.huile_id = h.id
        LEFT JOIN alertes a ON a.session_id = s.id
        GROUP BY s.id, h.nom, s.debut, s.fin, s.statut
        ORDER BY s.debut DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    return jsonify([{
        'id': r[0],
        'huile': r[1],
        'debut': str(r[2]) if r[2] else None,
        'fin': str(r[3]) if r[3] else None,
        'statut': r[4],
        'nb_alertes': r[5]
    } for r in rows]), 200


def _pdf_escape(value):
    text = '' if value is None else str(value)
    return text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')


def _simple_pdf(title, lines):
    y = 800
    content = ["BT", "/F1 16 Tf", f"50 {y} Td", f"({_pdf_escape(title)}) Tj"]
    y -= 28
    content.extend(["/F1 9 Tf", f"50 {y} Td"])
    for line in lines[:70]:
        safe = _pdf_escape(line[:115])
        content.append(f"({safe}) Tj")
        content.append("0 -13 Td")
    content.append("ET")
    stream = "\n".join(content).encode('latin-1', 'replace')

    objects = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objects.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objects.append(b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream")

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode())
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    pdf.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        pdf.extend(f"{off:010d} 00000 n \n".encode())
    pdf.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode())
    return bytes(pdf)


def _fetch_alert_rows_for_report():
    where_clause, params = _alerts_filters_from_request()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT TOP 500 a.timestamp, a.session_id, h.nom, a.niveau, a.parametre,
               a.valeur_lue, a.valeur_seuil, a.message,
               CASE WHEN a.resolue = 1 THEN 'Traitee' ELSE 'Non traitee' END AS traitement
        FROM alertes a
        JOIN sessions_reacteur s ON a.session_id = s.id
        JOIN huiles h ON s.huile_id = h.id
        {where_clause}
        ORDER BY a.timestamp DESC
    """, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


@frontend_api_bp.route('/export/alerts/pdf', methods=['GET'])
def export_alerts_pdf():
    rows = _fetch_alert_rows_for_report()
    lines = [f"Nombre alertes: {len(rows)}", ""]
    lines += [
        f"{r[0]} | Reaction #{r[1]} | {r[2]} | {r[3]} | {r[4]} | valeur {r[5]} / seuil {r[6]} | {r[8]}"
        for r in rows
    ]
    pdf = _simple_pdf('Rapport des alertes HydroScan', lines)
    return Response(pdf, mimetype='application/pdf', headers={
        'Content-Disposition': 'attachment; filename=hydroscan_alertes.pdf'
    })


@frontend_api_bp.route('/export/alerts/print', methods=['GET'])
def export_alerts_print():
    rows = _fetch_alert_rows_for_report()
    body_rows = "".join([
        f"<tr><td>{r[0]}</td><td>Reaction #{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td><td>{r[4]}</td><td>{r[5]}</td><td>{r[6]}</td><td>{r[7] or ''}</td><td>{r[8]}</td></tr>"
        for r in rows
    ]) or "<tr><td colspan='9'>Aucune alerte</td></tr>"
    html = f"""<!doctype html>
<html lang='fr'>
<head>
  <meta charset='utf-8'>
  <title>Rapport alertes HydroScan</title>
  <style>
    body {{ font-family: Arial, sans-serif; color: #111; padding: 24px; }}
    h1 {{ margin: 0 0 4px; }}
    p {{ color: #555; margin-top: 0; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 12px; }}
    th, td {{ border: 1px solid #bbb; padding: 6px; text-align: left; }}
    th {{ background: #eef2f5; }}
    .actions {{ margin: 16px 0; }}
    .charts {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; page-break-inside: avoid; }}
    .chart {{ border: 1px solid #ccc; padding: 8px; margin-bottom: 10px; }}
    button {{ padding: 10px 14px; cursor: pointer; }}
    @media print {{ .actions {{ display: none; }} body {{ padding: 0; }} }}
  </style>
</head>
<body>
  <h1>Rapport des alertes HydroScan</h1>
  <p>{len(rows)} alerte(s) - utilisez Imprimer puis Save as PDF / Microsoft Print to PDF.</p>
  <div class='actions'><button onclick='window.print()'>Imprimer / PDF</button></div>
  <table>
    <thead><tr><th>Date</th><th>Reaction</th><th>Huile</th><th>Niveau</th><th>Parametre</th><th>Valeur</th><th>Seuil DB</th><th>Message</th><th>Traitement</th></tr></thead>
    <tbody>{body_rows}</tbody>
  </table>
</body>
</html>"""
    if request.args.get('autoprint') == '1':
        html = html.replace('</body>', "<script>window.addEventListener('load', function(){ setTimeout(function(){ window.print(); }, 300); });</script></body>")
    return Response(html, mimetype='text/html')


def _fetch_session_report(session_id):
    conn = get_db()
    cursor = conn.cursor()
    _ensure_session_limit_columns(cursor)
    cursor.execute("""
        SELECT s.id, h.nom, s.debut, s.fin, s.statut, s.notes,
               COALESCE(s.lim_temp_min, h.temp_min),
               COALESCE(s.lim_temp_opt, h.temp_opt),
               COALESCE(s.lim_temp_max, h.temp_max),
               COALESCE(s.lim_pression_min, h.pression_min),
               COALESCE(s.lim_pression_opt, h.pression_opt),
               COALESCE(s.lim_pression_max, h.pression_max),
               COALESCE(s.lim_debit_min, h.debit_min),
               COALESCE(s.lim_debit_opt, h.debit_opt),
               COALESCE(s.lim_debit_max, h.debit_max),
               COALESCE(s.lim_rendement_min, h.rendement_min),
               COALESCE(s.lim_rendement_opt, h.rendement_opt)
        FROM sessions_reacteur s
        JOIN huiles h ON s.huile_id = h.id
        WHERE s.id = ?
    """, (session_id,))
    session = cursor.fetchone()

    cursor.execute("""
        SELECT timestamp, temperature, pression, debit_h2, rendement, statut_global
        FROM mesures_reacteur
        WHERE session_id = ?
        ORDER BY timestamp ASC
    """, (session_id,))
    mesures = cursor.fetchall()

    cursor.execute("""
        SELECT timestamp, niveau, parametre, valeur_lue, valeur_seuil, message,
               CASE WHEN resolue = 1 THEN 'Traitee' ELSE 'Non traitee' END AS traitement
        FROM alertes
        WHERE session_id = ?
        ORDER BY timestamp ASC
    """, (session_id,))
    alertes = cursor.fetchall()
    conn.close()
    return session, mesures, alertes


@frontend_api_bp.route('/export/session/<int:session_id>/pdf', methods=['GET'])
def export_session_pdf(session_id):
    session, mesures, alertes = _fetch_session_report(session_id)
    if not session:
        return jsonify({'error': 'Session introuvable'}), 404

    lines = [
        f"Reaction #{session_id}",
        f"Huile: {session[1]}",
        f"Statut: {session[4]}",
        f"Debut: {session[2]}",
        f"Fin: {session[3] or ''}",
        f"Mesures: {len(mesures)} | Alertes: {len(alertes)}",
        "",
        "SEUILS",
        f"Temperature min/opt/max: {session[6]} / {session[7]} / {session[8]}",
        f"Pression min/opt/max: {session[9]} / {session[10]} / {session[11]}",
        f"Debit H2 min/opt/max: {session[12]} / {session[13]} / {session[14]}",
        f"Rendement min/opt: {session[15]} / {session[16]}",
        "",
        "MESURES"
    ]
    lines += [f"{m[0]} | T={m[1]} | P={m[2]} | D={m[3]} | R={m[4]} | {m[5]}" for m in mesures[:35]]
    lines += ["", "ALERTES"]
    lines += [f"{a[0]} | {a[1]} | {a[2]} | valeur {a[3]} / seuil {a[4]} | {a[6]}" for a in alertes[:20]]
    pdf = _simple_pdf(f'Rapport Batch Reaction #{session_id}', lines)
    return Response(pdf, mimetype='application/pdf', headers={
        'Content-Disposition': f'attachment; filename=hydroscan_reaction_{session_id}.pdf'
    })


@frontend_api_bp.route('/export/session/<int:session_id>/csv', methods=['GET'])
def export_session_csv(session_id):
    session, mesures, alertes = _fetch_session_report(session_id)
    if not session:
        return jsonify({'error': 'Session introuvable'}), 404

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['RAPPORT BATCH / REACTION', session_id])
    writer.writerow(['huile', session[1]])
    writer.writerow(['debut', session[2]])
    writer.writerow(['fin', session[3]])
    writer.writerow(['statut', session[4]])
    writer.writerow(['notes_arret', session[5] or ''])
    writer.writerow([])
    writer.writerow(['SEUILS DATABASE'])
    writer.writerow(['temperature_min', 'temperature_opt', 'temperature_max', session[6], session[7], session[8]])
    writer.writerow(['pression_min', 'pression_opt', 'pression_max', session[9], session[10], session[11]])
    writer.writerow(['debit_min', 'debit_opt', 'debit_max', session[12], session[13], session[14]])
    writer.writerow(['rendement_min', 'rendement_opt', session[15], session[16]])
    writer.writerow([])
    writer.writerow(['MESURES'])
    writer.writerow(['timestamp', 'temperature', 'pression', 'debit_h2', 'rendement', 'statut_global'])
    writer.writerows(mesures)
    writer.writerow([])
    writer.writerow(['ALERTES'])
    writer.writerow(['timestamp', 'niveau', 'parametre', 'valeur_lue', 'valeur_seuil', 'message', 'traitement'])
    writer.writerows(alertes)

    return Response(output.getvalue(), mimetype='text/csv', headers={
        'Content-Disposition': f'attachment; filename=hydroscan_reaction_{session_id}.csv'
    })


def _series_svg(title, values, color):
    values = [float(v) for v in values if v is not None]
    if not values:
        return f"<div class='chart'><strong>{title}</strong><p>Aucune donnee</p></div>"
    width, height, pad = 520, 140, 18
    min_v, max_v = min(values), max(values)
    span = max(max_v - min_v, 1)
    points = []
    for i, value in enumerate(values):
        x = pad if len(values) == 1 else pad + i * (width - 2 * pad) / (len(values) - 1)
        y = height - pad - ((value - min_v) / span) * (height - 2 * pad)
        points.append(f"{x:.1f},{y:.1f}")
    return f"""
    <div class='chart'>
      <strong>{title}</strong>
      <svg viewBox='0 0 {width} {height}' width='100%' height='{height}' role='img'>
        <rect x='0' y='0' width='{width}' height='{height}' fill='#f8fafc' stroke='#d0d7de'/>
        <polyline points='{' '.join(points)}' fill='none' stroke='{color}' stroke-width='3'/>
        <text x='12' y='22' font-size='12' fill='#555'>min {min_v:.2f}</text>
        <text x='{width - 90}' y='22' font-size='12' fill='#555'>max {max_v:.2f}</text>
      </svg>
    </div>
    """


@frontend_api_bp.route('/export/session/<int:session_id>/print', methods=['GET'])
def export_session_print(session_id):
    session, mesures, alertes = _fetch_session_report(session_id)
    if not session:
        return jsonify({'error': 'Session introuvable'}), 404

    mesure_rows = "".join([
        f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td><td>{r[4]}</td><td>{r[5]}</td></tr>"
        for r in mesures
    ]) or "<tr><td colspan='6'>Aucune mesure</td></tr>"
    charts_html = "".join([
        _series_svg('Temperature', [r[1] for r in mesures], '#d73a49'),
        _series_svg('Pression', [r[2] for r in mesures], '#0366d6'),
        _series_svg('Debit H2', [r[3] for r in mesures], '#22863a'),
        _series_svg('Rendement', [r[4] for r in mesures], '#6f42c1')
    ])
    alerte_rows = "".join([
        f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td><td>{r[4]}</td><td>{r[5] or ''}</td><td>{r[6]}</td></tr>"
        for r in alertes
    ]) or "<tr><td colspan='7'>Aucune alerte</td></tr>"

    html = f"""<!doctype html>
<html lang='fr'>
<head>
  <meta charset='utf-8'>
  <title>Rapport Reaction #{session_id}</title>
  <style>
    body {{ font-family: Arial, sans-serif; color: #111; padding: 24px; }}
    h1, h2 {{ margin-bottom: 6px; }}
    .meta {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin: 14px 0; }}
    .box {{ border: 1px solid #ccc; padding: 8px; }}
    .schema {{ border: 1px solid #bbb; padding: 12px; margin: 16px 0; page-break-inside: avoid; }}
    .schema-flow {{ align-items: center; display: grid; grid-template-columns: 1fr 120px 1fr; gap: 12px; text-align: center; }}
    .schema-box {{ border: 1px solid #aaa; background: #f8fafc; padding: 10px; }}
    .schema-reactor {{ border: 2px solid #0366d6; border-radius: 22px; padding: 24px 8px; font-weight: 700; }}
    .arrow {{ font-size: 22px; color: #0366d6; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 12px; margin-bottom: 18px; }}
    th, td {{ border: 1px solid #bbb; padding: 6px; text-align: left; }}
    th {{ background: #eef2f5; }}
    .actions {{ margin: 16px 0; }}
    .charts {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; page-break-inside: avoid; }}
    .chart {{ border: 1px solid #ccc; padding: 8px; margin-bottom: 10px; }}
    button {{ padding: 10px 14px; cursor: pointer; }}
    @media print {{ .actions {{ display: none; }} body {{ padding: 0; }} }}
  </style>
</head>
<body>
  <h1>Rapport Batch / Reaction #{session_id}</h1>
  <div class='actions'><button onclick='window.print()'>Imprimer / PDF</button></div>
  <div class='meta'>
    <div class='box'><strong>Huile:</strong> {session[1]}</div>
    <div class='box'><strong>Statut:</strong> {session[4]}</div>
    <div class='box'><strong>Debut:</strong> {session[2]}</div>
    <div class='box'><strong>Fin:</strong> {session[3] or ''}</div>
    <div class='box'><strong>Mesures:</strong> {len(mesures)}</div>
    <div class='box'><strong>Alertes:</strong> {len(alertes)}</div>
  </div>
  <div class='schema'>
    <h2>Schema du procede</h2>
    <div class='schema-flow'>
      <div class='schema-box'>Huile vegetale + Hydrogene H2</div>
      <div class='schema-reactor'>Reacteur<br>Hydrogenation</div>
      <div class='schema-box'>Huile hydrogenee<br>+ controle qualite</div>
    </div>
  </div>
  <h2>Seuils de la base de donnees</h2>
  <table>
    <thead><tr><th>Parametre</th><th>Min</th><th>Optimal</th><th>Max</th></tr></thead>
    <tbody>
      <tr><td>Temperature</td><td>{session[6]}</td><td>{session[7]}</td><td>{session[8]}</td></tr>
      <tr><td>Pression</td><td>{session[9]}</td><td>{session[10]}</td><td>{session[11]}</td></tr>
      <tr><td>Debit H2</td><td>{session[12]}</td><td>{session[13]}</td><td>{session[14]}</td></tr>
      <tr><td>Rendement</td><td>{session[15]}</td><td>{session[16]}</td><td>-</td></tr>
    </tbody>
  </table>
  <h2>Graphiques du batch</h2>
  <div class='charts'>{charts_html}</div>
  <h2>Mesures du batch</h2>
  <table>
    <thead><tr><th>Date</th><th>Temperature</th><th>Pression</th><th>Debit H2</th><th>Rendement</th><th>Statut</th></tr></thead>
    <tbody>{mesure_rows}</tbody>
  </table>
  <h2>Alertes du batch</h2>
  <table>
    <thead><tr><th>Date</th><th>Niveau</th><th>Parametre</th><th>Valeur</th><th>Seuil DB</th><th>Message</th><th>Traitement</th></tr></thead>
    <tbody>{alerte_rows}</tbody>
  </table>
</body>
</html>"""
    if request.args.get('autoprint') == '1':
        html = html.replace('</body>', "<script>window.addEventListener('load', function(){ setTimeout(function(){ window.print(); }, 300); });</script></body>")
    return Response(html, mimetype='text/html')


@frontend_api_bp.route('/alerts/<int:id>/resolve', methods=['PUT'])
def resolve_alert(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE alertes
        SET resolue = 1, resolue_at = GETDATE()
        WHERE id = ?
    """, (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True}), 200


@frontend_api_bp.route('/history', methods=['GET'])
def history():
    date_start = request.args.get('date_start') or ''
    date_end = request.args.get('date_end') or ''
    huile = request.args.get('huile') or ''
    statut = request.args.get('statut') or ''

    filters = []
    params = []
    if date_start:
        filters.append("CAST(m.timestamp AS date) >= ?")
        params.append(date_start)
    if date_end:
        filters.append("CAST(m.timestamp AS date) <= ?")
        params.append(date_end)
    if huile:
        filters.append("h.nom = ?")
        params.append(huile)
    if statut:
        db_statut = {'Normal': 'normal', 'Warning': 'alerte', 'Critique': 'critique'}.get(statut, statut)
        filters.append("m.statut_global = ?")
        params.append(db_statut)

    where_clause = "WHERE " + " AND ".join(filters) if filters else ""

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT TOP 300
               m.id, m.timestamp, h.nom,
               m.temperature, m.pression, m.debit_h2,
               m.rendement, DATEDIFF(minute, s.debut, m.timestamp),
               m.statut_global
        FROM mesures_reacteur m
        JOIN sessions_reacteur s ON m.session_id = s.id
        JOIN huiles h ON s.huile_id = h.id
        {where_clause}
        ORDER BY m.timestamp DESC
    """, params)
    rows = cursor.fetchall()
    conn.close()

    return jsonify([{
        'batch_id': f'B-{r[0]:04d}',
        'datetime': r[1].isoformat() if hasattr(r[1], 'isoformat') else str(r[1]),
        'huile': r[2],
        'temperature': r[3],
        'pression': r[4],
        'debit': r[5],
        'rendement': r[6],
        'conversion': r[6],
        'duree': r[7] or 0,
        'statut': {'normal': 'Normal', 'alerte': 'Warning', 'critique': 'Critique'}.get(r[8], r[8])
    } for r in rows]), 200


@frontend_api_bp.route('/thresholds', methods=['POST'])
def update_thresholds():
    data = request.get_json() or {}
    temp_max = data.get('temp_max')
    pression_max = data.get('pression_max')

    conn = get_db()
    cursor = conn.cursor()
    if temp_max:
        cursor.execute("UPDATE huiles SET temp_max = ? WHERE id = (SELECT TOP 1 id FROM huiles ORDER BY id)", (temp_max,))
    if pression_max:
        cursor.execute("UPDATE huiles SET pression_max = ? WHERE id = (SELECT TOP 1 id FROM huiles ORDER BY id)", (pression_max,))
    conn.commit()
    conn.close()
    return jsonify({'success': True}), 200


@frontend_api_bp.route('/export/csv', methods=['GET'])
def export_csv():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT TOP 500 timestamp, temperature, pression, debit_h2, rendement, statut_global
        FROM mesures_reacteur
        ORDER BY timestamp DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['timestamp', 'temperature', 'pression', 'debit_h2', 'rendement', 'statut'])
    writer.writerows(rows)
    return Response(output.getvalue(), mimetype='text/csv', headers={
        'Content-Disposition': 'attachment; filename=hydroscan_mesures.csv'
    })


@frontend_api_bp.route('/export/alerts/csv', methods=['GET'])
def export_alerts_csv():
    where_clause, params = _alerts_filters_from_request()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT a.timestamp, a.session_id, h.nom, a.niveau, a.parametre,
               a.valeur_lue, a.valeur_seuil, a.message,
               CASE WHEN a.resolue = 1 THEN 'resolue' ELSE 'ouverte' END AS traitement
        FROM alertes a
        JOIN sessions_reacteur s ON a.session_id = s.id
        JOIN huiles h ON s.huile_id = h.id
        {where_clause}
        ORDER BY a.timestamp DESC
    """, params)
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'timestamp', 'session_id', 'huile', 'niveau', 'parametre',
        'valeur_lue', 'valeur_seuil', 'message', 'traitement'
    ])
    writer.writerows(rows)
    return Response(output.getvalue(), mimetype='text/csv', headers={
        'Content-Disposition': 'attachment; filename=hydroscan_alertes.csv'
    })


@frontend_api_bp.route('/export/pdf', methods=['GET'])
def export_pdf():
    return jsonify({'message': 'Export PDF non configure pour le moment'}), 501
