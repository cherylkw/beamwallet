# Generated by Django 2.2.10 on 2020-04-30 04:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bank', '0002_walletaccount_user_id'),
    ]

    operations = [
        migrations.RenameField(
            model_name='walletaccount',
            old_name='user_id',
            new_name='bank_user',
        ),
    ]
