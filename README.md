# CTF website with integrated writeup submission system

Individualized challenges per user.

## Installing

Hopefully reasonably complete instructions.

1. Set up a container registry to push your containers to
    1. Push the `examproxy` container there
    1. Push your other containers
2. Set up a nice VM somewhere
    1. Install:
        * poetry (probably via pip3 or docs if your distro doesn't package it)
        * Docker (via Docker documentation instructions if your distro doesn't package a recent version)
        * nginx
        * certbot
        * postgresql
        * uwsgi  (if using `apt`, install `uwsgi-plugin-python3`)
        * psycopg2
    2. Disable ASLR
        * `kernel.randomize_va_space = 0` in `/etc/sysctl.conf` or your favourite method.
2. Run ``poetry config virtualenvs.create false`` as root
3. Add a user ``django``  (``useradd -m django``)
3. Make sure the `django` user can download your containers.
    * Add to ``docker`` group (``gpasswd -a docker django``)
    * For Google Artifact Registry, e.g. run ``gcloud auth configure-docker europe-west4-docker.pkg.dev`` to set up the pulling.
      Google Compute Engine VMs should have access (or you may have to set it up in IAM)
4. Create a database for django (errors about changing directory may be ignored)
    1. ``sudo -u postgres createuser django``
    1. ``sudo -u postgres createdb -O django django``
5. Set up TLS through certbot via your favourite method.
   * You may need to mess with NGINX to do validation, or use DNS validation with something like the Cloudflare-dns plugin.
6. Clone this repo into the `/home/django/ctfexam` folder
7. Put the nginx config from `resources` in the right place
    * on Debian-y hosts `/etc/nginx/sites-enabled/` is the place to go
    * You may need to get rid of `/etc/nginx/sites-enabled/default`.
    * You will need the TLS certs; use `sudo nginx -t` for troubleshooting.
8. ``poetry install --no-dev`` as root in `/home/django/ctfexam`
9. Copy ``resources/uwsgi/django.ini`` to ``/home/django``
10. Fill in your environment variables in ``/home/django/django.ini`` at the bottom
    * `SECRET_KEY` should be a decently random, long-enough string.
    * `SENTRY_DSN` is related to what's mentioned below. If you comment it out, Sentry isn't used.
11. From `resources/django`, copy ``production_settings.py`` and ``students.py`` to ``ctfexam/ctfexam``
    * These settings suggest using [Sentry](https://sentry.io) for debug/error logging and alerting, free tier is available (Github Pack upgrade exists as well).
    * The SMTP settings (password resets!) suggest using [Sendgrid](https://sendgrid.net); you might also consider setting up a temporary Gmail account with SMTP.
12. Set the settings and ``students.py`` according to your preferences.
13. Set up the docker config from ``resources/docker`` by copying it to ``/etc/docker``.
    * Restart Docker by running `systemctl restart docker`.
14. Copy the systemd files from `resources/systemd` to `/etc/systemd/system`
15. Enable the systemd units
16. Run this as user django: ``SECRET_KEY=foo ./manage.py migrate``  (actual value of `SECRET_KEY` does not matter for any of these)
17. ``SECRET_KEY=foo ./manage.py createsuperuser``
18. ``SECRET_KEY=foo ./manage.py collectstatic``
