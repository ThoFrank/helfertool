# Generated by Django 3.2.14 on 2022-07-10 13:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("news", "0009_alter_person_validated"),
    ]

    operations = [
        migrations.AddField(
            model_name="person",
            name="mail_failed",
            field=models.CharField(blank=True, default=None, max_length=512, null=True),
        ),
    ]
