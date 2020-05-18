from django.db import models
from django.conf import settings
from fernet_fields import EncryptedTextField
import uuid

# A simple online bank account stores:
# bank user id issued by bank
# user key to verify user identity, generate when connect bank account with beam wallet
# beam wallet API issued by bank
# Initally 10000 and will allow beam wallet to withdrawn until the balance is empty
#
class WalletAccount(models.Model):
    bank_user = models.CharField(max_length=100, blank=True, unique=True, default=uuid.uuid4)
    user_key = EncryptedTextField()
    wallet_api_token = EncryptedTextField()
    balance = models.DecimalField(max_digits=10, decimal_places=2,default=0.00)


