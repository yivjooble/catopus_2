# Generated by Django 4.1.8 on 2023-04-06 15:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("search", "0006_alter_remotelogs_updated_on"),
    ]

    operations = [
        migrations.AlterField(
            model_name="searchresult",
            name="input_query",
            field=models.TextField(null=True),
        ),
    ]
