import os
import django
from django.contrib.auth.hashers import make_password

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'catopus.settings')
django.setup()

from account.models import LoginCreds

def hash_existing_passwords():
    all_users = LoginCreds.objects.all()

    for user in all_users:
        hashed_password = make_password(user.password)
        user.hashed_password = hashed_password
        user.save()

if __name__ == '__main__':
    hash_existing_passwords()
