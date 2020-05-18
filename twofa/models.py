from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from fernet_fields import EncryptedTextField
from datetime import datetime
import uuid

from .managers import TwoFAUserManager

USERTYPE_CHOICES = (
    ('C', 'Customer'),
    ('M', 'Merchant'),
    ('A', 'Admin')
)

PAYTYPE_CHOICES = (
    ('M', 'Merchant'),
    ('C', 'Customer')
)

# This page contains all models using in Beam Wallet except Bank Model
# All important data fields are encryted using Fernet symmetric encryption library

# User model
class TwoFAUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=42, unique=True)
    email = models.EmailField()
    authy_id = models.CharField(max_length=12, null=True, blank=True)
    phone_number = models.CharField(max_length=12, null=True, blank=True)
    country_code = models.CharField(max_length=5,null=True, blank=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    user_type = models.CharField(max_length=1, choices=USERTYPE_CHOICES,default='C')
    objects = TwoFAUserManager()

    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'

    def __str__(self):
        return f"{self.id} : {self.username} - {self.email} - {self.phone_number}"

# Bank model
class Bank(models.Model):
    name = models.CharField(max_length=50,null=False)
    wallet_api_token = EncryptedTextField(null=True)

    def __str__(self):
        return f"{self.id} : {self.name}"

# User Wallet for customer and merchant
class Wallet(models.Model):
    user = models.OneToOneField(TwoFAUser,on_delete=models.CASCADE,related_name="wallet_user")
    private_key = EncryptedTextField(null=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2,default=0.00)

    def __str__(self):
        return f"{self.id} : {self.user} - ${self.balance}"

# Contact list for customer to store friends contact and able to transfer payment
class ContactList(models.Model):
    user = models.ForeignKey(TwoFAUser,on_delete=models.CASCADE,related_name="contract_user")    
    person = models.ForeignKey(TwoFAUser,on_delete=models.CASCADE,related_name="person")
    shared_key = EncryptedTextField()
    created_date = models.DateTimeField(auto_now_add=True, auto_now=False)

    def __str__(self):
        return f"{self.id} : {self.user}"

# Bank list for customers to choose for top up
class BankList(models.Model):
    user = models.ForeignKey(TwoFAUser,on_delete=models.CASCADE,related_name="bank_user")    
    bank = models.ForeignKey(Bank,on_delete=models.CASCADE,related_name="bank")
    user_key = EncryptedTextField(null=True)
    bank_user = models.CharField(max_length=100, blank=True, unique=True, default=uuid.uuid4)
    created_date = models.DateTimeField(auto_now_add=True, auto_now=False)

    def __str__(self):
        return f"{self.id} : {self.user} - Bank: {self.bank}"

# Store Top up transcation record
class Topup(models.Model):
    trx_id = models.CharField(max_length=50,null=False)
    ref_id = models.IntegerField(default=0)
    wallet = models.ForeignKey(Wallet,on_delete=models.CASCADE,related_name="wallet")
    bank = models.ForeignKey(Bank,on_delete=models.CASCADE,related_name="topup_bank")
    amount = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
    description = EncryptedTextField()
    trx_date = models.DateTimeField(auto_now_add=True, auto_now=False)

    def clean(self):
        if self.amount < 0:
            raise ValidationError("Amount must be greater than 0")
        elif self.trx_id is None:
            raise ValidationError("Must provide a transcation ID")

    def save(self,*args,**kwargs):
        self.clean()

        super().save(*args,**kwargs)

    def __str__(self):
        return f"{self.id} : {self.wallet} - amount : {self.amount}"

# Store Payment records for friends payment and merchant payment
class Payment(models.Model):
    trx_id = models.CharField(max_length=100, blank=True, unique=True, default=uuid.uuid4)
    ref_id = models.IntegerField(default=0)
    credit_wallet = models.ForeignKey(Wallet,on_delete=models.CASCADE,related_name="credit_wallet")
    debit_wallet = models.ForeignKey(Wallet,on_delete=models.CASCADE,related_name="debit_wallet")
    description = EncryptedTextField()
    trx_date = models.DateTimeField(auto_now_add=True, auto_now=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
    pay_type = models.CharField(max_length=1, choices=PAYTYPE_CHOICES,default='C')

    def clean(self):
        if self.amount < 0:
            raise ValidationError("Amount must be greater than 0")
        elif self.credit_wallet == self.debit_wallet:
            raise ValidationError("Same wallet cannot perform transcation payment")

    def save(self,*args,**kwargs):
        self.clean()

        super().save(*args,**kwargs)

    def __str__(self):
        return f" credit wallet : {self.credit_wallet} debit wallet : {self.debit_wallet} amount : ${self.amount}"

# A contract establish between customer and merchant
class Contract(models.Model):
    user = models.ForeignKey(TwoFAUser,on_delete=models.CASCADE,related_name="merchant_user")
    merchant = models.ForeignKey(TwoFAUser,on_delete=models.CASCADE,related_name="merchant")
    shared_key = EncryptedTextField(null=True)
    sign_date = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return f"{self.user} : {self.merchant}"
