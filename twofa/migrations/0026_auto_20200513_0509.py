# Generated by Django 2.2.10 on 2020-05-13 05:09

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('twofa', '0025_contract_sign_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contactlist',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contract_user', to=settings.AUTH_USER_MODEL),
        ),
    ]
