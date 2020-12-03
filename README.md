# CTF website with integrated writeup submission system

Individualized challenges per user.

## Installing

Hopefully reasonably complete instructions.

1. Set up a container registry to push your containers to
    1. Push the examproxy container ther
    1. Push your other containers
2. Set up a nice VM somewhere
    1. Install:
        * poetry
        * Docker
        * nginx
        * certbot
        * postgresql
        * uwsgi
        * pyscopg2
2. Run ``poetry config virtualenvs.create false``
3. Add a user ``django``
3. Make sure the `django` user can download your containers.
4. Create a database for django
    1. ``sudo -u postgres createuser django``
    1. ``sudo -u postgres createdb -O django django``
5. Set up SSL through certbot
6. Put the nginx config from resources in the right place
7. Clone this repo into the `/home/django/ctfexam` folder
8. ``poetry install`` as root
8. Copy ``resources/uwsgi/django.ini`` to ``/home/django``
9. Set your environment variables in ``django.ini``
10. Copy ``production_settings.py`` and ``students.py`` to ``ctfexam/ctfexam``
11. Set the settings and ``students.py`` according to your preferences.
16. Set up the docker config from ``resources/docker`` by copying it to ``/etc/docker``
12. Copy the systemd files to `/etc/systemd/system`
13. Enable the systemd units
14. ``SECRETKEY=foo ./manage.py migrate``
15. ``SECRETKEY=foo ./manage.py createsuperuser``
15. ``SECRETKEY=foo ./manage.py collectstatic``
