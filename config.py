import pyodbc

CONNECTION_STRING = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=localhost;'
    'DATABASE=ReactorMonitorDB;'
    'Trusted_Connection=yes;'
    'Encrypt=no;'
)

def get_db():
    try:
        conn = pyodbc.connect(CONNECTION_STRING)
        return conn
    except Exception as e:
        print(f'Erreur connexion DB: {e}')
        return None

def test_connexion():
    conn = get_db()
    if conn:
        print('Connexion SQL Server OK!')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM huiles")
        count = cursor.fetchone()[0]
        print(f'{count} huiles dans la base')
        conn.close()
        return True
    else:
        print('Connexion echouee!')
        return False

if __name__ == '__main__':
    test_connexion()