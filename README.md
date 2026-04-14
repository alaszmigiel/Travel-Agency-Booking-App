# Uruchomienie projektu 

Wymagania:
- Python 3.12+

## Windows 
1. Rozpakuj projekt
2. Uruchom plik `start.bat`
3. Wejdź w przeglądarce na: http://127.0.0.1:8000

## MacOS/Linux
1. Rozpakuj projekt
2. Uruchom plik `start.sh`
3. Wejdź w przeglądarce na: http://127.0.0.1:8000

### Ręczne uruchomienie: 

Windows:
```bash
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

MacOS/Linux:
```bash
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

