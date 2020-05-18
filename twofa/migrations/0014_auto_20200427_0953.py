# Generated by Django 2.2.10 on 2020-04-27 09:53

from django.db import migrations
import fernet_fields.fields


class Migration(migrations.Migration):

    dependencies = [
        ('twofa', '0013_auto_20200427_0405'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bank',
            name='bank_code',
        ),
        migrations.RemoveField(
            model_name='banklist',
            name='api_key',
        ),
        migrations.AddField(
            model_name='bank',
            name='wallet_api_token',
            field=fernet_fields.fields.EncryptedTextField(null=True),
        ),
        migrations.DeleteModel(
            name='Topup',
        ),
    ]
