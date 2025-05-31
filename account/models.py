from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models



class LoginCredsManager(BaseUserManager):
    def get_by_natural_key(self, username):
        return self.get(username=username)
    

class LoginCreds(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=255)
    username = models.CharField(max_length=255, primary_key=True)
    password = models.CharField(max_length=255)
    hashed_password = models.CharField(max_length=255)
    last_login = models.DateTimeField()

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = LoginCredsManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    class Meta:
        managed = False
        db_table = 'dwh_system\".\"cat_login_creds'

    def __str__(self):
        return self.username