# Generated by Django 2.2.4 on 2020-04-16 09:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('twofa', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='twofauser',
            name='phone_number',
            field=models.CharField(blank=True, max_length=12, null=True),
        ),
    ]
