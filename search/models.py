from django.db import models
from account.models import LoginCreds


class SearchResult(models.Model):
    identifier = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(LoginCreds, on_delete=models.CASCADE)
    search_results_file = models.FileField(upload_to='search_results/')
    created_at = models.DateTimeField(auto_now_add=True)
    sql_query = models.TextField(null=True)
    countries_list = models.CharField(max_length=50, null=True)
    countries = models.CharField(max_length=8192, null=True)

    class Meta:
        managed = True
        db_table = '"dwh_system"."cat_search_result"'


class RemoteLogs(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(LoginCreds, on_delete=models.CASCADE)
    status = models.CharField(max_length=10)
    sql_query = models.TextField()
    step = models.CharField(max_length=255, null=True)
    table_name_created = models.CharField(max_length=50, null=True)
    log_field = models.TextField(null=True)
    countries_list = models.CharField(max_length=50, null=True)
    countries = models.CharField(max_length=255)
    run_on = models.DateTimeField(auto_now=True)
    updated_on = models.DateTimeField(null=True)


    class Meta:
        managed = True
        db_table = '"dwh_system"."cat_remote_logs"'


class SavedScripts(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(LoginCreds, on_delete=models.CASCADE)
    sql_query = models.TextField()
    countries_list = models.CharField(max_length=50, null=True)
    countries = models.CharField(max_length=255)
    saved_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(null=True)
    deleted_on = models.DateTimeField(null=True)

    class Meta:
        managed = True
        db_table = '"dwh_system"."cat2_saved_scripts"'