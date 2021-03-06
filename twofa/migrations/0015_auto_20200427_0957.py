# Generated by Django 2.2.10 on 2020-04-27 09:57

from django.db import migrations, models
import django.db.models.deletion
import fernet_fields.fields


class Migration(migrations.Migration):

    dependencies = [
        ('twofa', '0014_auto_20200427_0953'),
    ]

    operations = [
        migrations.AddField(
            model_name='banklist',
            name='user_key',
            field=fernet_fields.fields.EncryptedTextField(null=True),
        ),
        migrations.CreateModel(
            name='Topup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('trx_id', models.CharField(max_length=50)),
                ('ref_id', models.IntegerField(default=0)),
                ('amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('description', fernet_fields.fields.EncryptedTextField()),
                ('trx_date', models.DateTimeField(auto_now_add=True)),
                ('bank', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='topup_bank', to='twofa.Bank')),
                ('wallet', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='wallet', to='twofa.Wallet')),
            ],
        ),
    ]
