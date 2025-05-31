# Catopus 2.0

## General info
This is the next generation of a catopus project, created to gather all needed sources into one and create possibility to get data from them all.

```One Ring to rule them all, One Ring to find them, One Ring to bring them all, and in the darkness bind them```

## Setup
1. create virtal environment:
    - 
2. install django:
    - 
3. install needed libraries from requirements.txt:
    - 

## Usage:
1. start django server:
 - `gunicorn catopus.wsgi:application --bind <IP address>`
2. create .env file with credentials:
 - `connect to dwh postgresql: we use .env file`
 3. migrate to dwh db:
 -  `python manage.py makemigrations <app>`
 -  `python manage.py migrate`
 4. Queue managed by Redis and Celery:
 -  run celery: `celery -A catopus worker --loglevel=info`
 -  redis runs on WSL2, to start: `sudo service redis-server start`
 -  redis check: `redis-cli ping`
    