# Travel Agency Booking App

Web application for browsing travel offers, managing bookings, and completing purchases with online payment integration.

## Overview

This project is a travel agency booking system built with Django and Python.

The application allows users to browse, filter, and purchase travel offers through a complete booking flow, including cart management, multi-step checkout, and payment processing. 

The system follows a modular architecture based on Django apps and includes a service layer to handle business logic such as cart operations, order creation, and payment integration.

## Academic Context

This project was developed as part of an engineering thesis titled: **"Design and Implementation of a System Supporting the Management of Personalized Travel Agency Offers"**

## Documentation

The repository includes selected diagrams and design materials created during the analysis and design phase of the system.

Available in the `docs/` directory:
- UML diagrams
- BPMN process diagrams
- database models
- functional requirements
- use case specifications

## Implemented Features
- User registration and authentication
- User profile setup and preferences
- Travel offer browsing, search, filtering, and sorting
- Shopping cart management
- Multi-step checkout process
- Order creation
- PayU API integration (sandbox environment)
- Payment status updates via webhook notifications

## Planned Improvements
- Advanced offer personalization  
- Employee/admin module  
- Recommendation system  

## Project Structure
```
travel-agency-booking-app/
├── accounts/        # Authentication, registration, and user profile management
├── docs/            # Project documentation, diagrams, and specifications
├── offers/          # Travel offers, business logic, and browsing
├── orders/          # Order management and persistence
├── shop/            # Cart, checkout flow, and PayU payment integration
├── templates/       # HTML templates (accounts, offers, checkout)
├── static/          # Static assets (CSS, images)
├── media/           # Uploaded media files
├── travel_agency/   # Django project configuration (settings, URLs)
├── manage.py        # Django entry point
├── requirements.txt # Dependencies
├── start.bat        # Windows startup script
├── start.sh         # MacOS/Linux startup script
└── .gitignore       # Ignored files
```
## Technologies Used
- Python
- Django (ORM, authentication, sessions)
- SQLite
- HTML / CSS
- JavaScript
- PayU API

## Technical Requirements

- Python 3.12 or higher
- Additional dependencies listed in requirements.txt

## Installation & Usage

### 1. Clone the repository:
```sh
git clone https://github.com/alaszmigiel/Travel-Agency-Booking-App.git
cd Travel-Agency-Booking-App
```
### 2. Create a virtual environment:
```sh
python -m venv venv
```
### 3. Activate the environment:

**Windows:**
```sh
venv\Scripts\activate
```

**MacOS/Linux:**
```sh
source venv/bin/activate
```

### 4. Install dependencies:
``` sh
pip install -r requirements.txt
```

### 5. Apply migrations and load data:
``` sh
python manage.py migrate
python manage.py loaddata fixtures/demo_data.json
```

### 6. Run the server:
``` sh
python manage.py runserver
```

### 7. Open in browser:
Visit http://127.0.0.1:8000 in your browser.


