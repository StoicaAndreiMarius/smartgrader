# smartgrader
Linux:
Creează venv
python3 -m venv venv

Activează venv
source venv/bin/activate

Instalare Dependințe
pip install -r requirements.txt

Windows:

Creează venv
python -m venv venv

Activează venv (Command Prompt)
venv\Scripts\activate.bat

SAU activează venv (PowerShell)
venv\Scripts\Activate.ps1

Instalare Dependințe
pip install -r requirements.txt



Pentru DB:

Instalare postgre: https://www.postgresql.org/download/

In pgAdmin:
Click dreapta pe Login/Group Roles -> general (name: nume_user), definition: (password: parola_ta), privileges (can login -> yes, inherit rights from  ... yes) - pentru a face un nou user de dev

Click dreapta pe Databases -> create: general (database: nume_db) (owner: nume_user_creat)

In .env trebuie setate:

DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=

In proiectul django:

python manage.py makemigrations
python manage.py migrate