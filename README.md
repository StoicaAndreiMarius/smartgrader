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



Pentru DB daca vrei local:

Instalare postgre: https://www.postgresql.org/download/

In pgAdmin:
Click dreapta pe Login/Group Roles -> general (name: nume_user), definition: (password: parola_ta), privileges (can login -> yes, inherit rights from  ... yes) - pentru a face un nou user de dev

Click dreapta pe Databases -> create: general (database: nume_db) (owner: nume_user_creat)

Pentru generare secret_key nou: 
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

In .env trebuie setate:
SECRET_KEY=
DEBUG=True
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=

python manage.py makemigrations
python manage.py migrate



Daca nu vrei local ci baza de date hostata gratis pe neon ceva:

in .env:
SECRET_KEY=
DEBUG=TRUE
DB_NAME=neondb
DB_USER=neondb_owner
DB_PASSWORD=npg_wGshT06eAcJM
DB_HOST=ep-morning-hall-a9jes6pw-pooler.gwc.azure.neon.tech
DB_PORT=5432
DB_SSL=require

in settings.py:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
        'OPTIONS': {
            'sslmode': config('DB_SSL', default='require'),
        }
    }
}
(BAZA DE DATE HOSTATA GRATIS ASTA E DOAR DE TEST)

python manage.py makemigrations
python manage.py migrate

