Activate Redis - sudo service redis-server restart
Activate Virtual environment 'freelancenv'
Open 3 command promp 
Runserver - python manage.py runserver
Activate Celery worker -   celery -A freelance_taskboard.celery worker --pool=solo -l info
Activate Celery beat -     celery -A freelance_taskboard.celery beat -l info
