# Smart Hydrogenation Dashboard - HydroScan

Application Flask + SQL Server pour surveiller une reaction d'hydrogenation: dashboard, huiles, alertes, rapports CSV/PDF et gestion des utilisateurs.

## Installation rapide pour le groupe

1. Cloner le projet depuis GitHub.
2. Installer les dependances Python.
3. Ouvrir SQL Server Management Studio.
4. Executer `database/01_schema.sql`.
5. Executer `database/02_seed.sql`.
6. Lancer Flask avec `py app.py`.
7. Ouvrir `http://127.0.0.1:5000/login`.

## Comptes demo

- Admin: `admin@reactor.ma` / `admin123`
- Operateur: `operator@reactor.ma` / `admin123`

## Configuration SQL Server

Le fichier `config.py` utilise par defaut:

```text
SERVER=localhost
DATABASE=ReactorMonitorDB
Trusted_Connection=yes
ODBC Driver 17 for SQL Server
```

Si un membre du groupe utilise un autre nom de serveur SQL Server, il doit modifier seulement `SERVER` dans `config.py`.

## Important

Ne poussez pas les fichiers `.mdf` ou `.ldf` dans GitHub. Le code est partage via GitHub, mais la base de donnees se reconstruit avec les scripts SQL dans le dossier `database`.
