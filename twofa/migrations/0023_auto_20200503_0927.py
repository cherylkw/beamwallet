# Generated by Django 2.2.10 on 2020-05-03 09:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('twofa', '0022_contract'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='pay_type',
            field=models.CharField(choices=[('M', 'Merchant'), ('C', 'Customer')], default='C', max_length=1),
        ),
    ]
