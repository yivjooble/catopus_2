# Generated by Django 4.1.7 on 2023-04-05 09:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("search", "0002_searchresult_select_query_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="searchresult",
            old_name="select_query",
            new_name="input_query",
        ),
    ]
