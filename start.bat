@echo off
setlocal

if not exist venv (
  python -m venv venv
)

call venv\Scripts\activate

python -m pip install --upgrade pip
pip install -r requirements.txt

python manage.py migrate

echo.
echo Starting server at http://127.0.0.1:8000
python manage.py runserver

pause