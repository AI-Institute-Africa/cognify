# Confluence Nexus

Enterprise-grade Confluence Nexus built with Django and Django REST Framework.

## Architecture

- Python 3.13
- Django 5.x
- Django REST Framework
- Bootstrap 5 + HTMX-ready templates
- SQLite development / MySQL production compatible

## Project layout

- `config/`: Django project settings and entrypoints
- `core/`: shared abstractions, base models, utilities
- `apps/`: enterprise apps and business modules

## Getting started

1. Create a Python 3.13 virtual environment
2. Install dependencies: `pip install -r requirements.txt`
3. Set `DJANGO_SETTINGS_MODULE=config.settings`
4. Run migrations: `python manage.py migrate`
5. Create a superuser: `python manage.py createsuperuser`
6. Run development server: `python manage.py runserver`
