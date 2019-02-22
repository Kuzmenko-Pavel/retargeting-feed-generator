# retargeting-feed-generator

- Create a Python virtual environment.

    virtualenv --no-site-packages -p python3.5 env

- Upgrade packaging tools.

    env/bin/pip install --upgrade pip setuptools

- Install the project in editable mode with its testing requirements.

    env/bin/pip install -e "."
    
celery worker -A pyramid_celery.celery_app --ini development.ini
celery beat -A pyramid_celery.celery_app --ini development.ini