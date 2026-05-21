import random
import time
import threading
import requests

API = 'http://localhost:5000/api'

def simuler_mesure(huile_params, session_id):
    """يولد mesure واحدة بناءً على paramètres الزيت"""
    temp_opt  = huile_params['temperature']['opt']
    press_opt = huile_params['pression']['opt']
    debit_opt = huile_params['debit_h2']['opt']
    rend_opt  = huile_params['rendement']['opt']

    # simulation بـ bruit عشوائي
    spike = random.random() < 0.05  # 5% فرصة spike

    return {
        'session_id' : session_id,
        'temperature': round(temp_opt  + random.uniform(-8, 15 if spike else 8), 1),
        'pression'   : round(press_opt + random.uniform(-0.5, 1.5 if spike else 0.5), 2),
        'debit_h2'   : round(debit_opt + random.uniform(-5, 5), 1),
        'rendement'  : round(rend_opt  + random.uniform(-5, 3), 1)
    }


def run_simulation(session_id, huile_id, interval=2):
    """يشغل simulation في background thread"""

    # جيب paramètres الزيت
    res    = requests.get(f'{API}/huiles/{huile_id}')
    huile  = res.json()

    print(f'Simulation démarrée — Session {session_id} — {huile["nom"]}')

    while True:
        # تحقق واش session مازالت active
        res = requests.get(f'{API}/sessions/active?user_id=0')
        # ولد mesure
        mesure = simuler_mesure(huile, session_id)

        # سجل في DB عبر API
        requests.post(f'{API}/mesures', json=mesure)

        time.sleep(interval)


def start_simulation_thread(session_id, huile_id):
    """شغل simulation في thread منفصل"""
    t = threading.Thread(
        target=run_simulation,
        args=(session_id, huile_id),
        daemon=True
    )
    t.start()
    return t