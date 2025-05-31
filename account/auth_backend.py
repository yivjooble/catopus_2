from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from account.models import LoginCreds

import logging

logger = logging.getLogger('accounts')

class CustomUserAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = LoginCreds.objects.get(username=username)
            if user and check_password(password, user.hashed_password):
                return user
        except LoginCreds.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return LoginCreds.objects.get(pk=user_id)
        except LoginCreds.DoesNotExist:
            return None
