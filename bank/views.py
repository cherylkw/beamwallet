from django.shortcuts import render
from django.http import JsonResponse
from .models import WalletAccount
from tinyec import registry
import uuid
import requests
from decimal import Decimal

# --------------------------------------------------------------------------
# bank_api:
#
# A simple bank app to demo interaction between wallet and bank when topping
# up the user Wallet. 
#
# The bank_api function will return JSON format data contain trx_id and status 
# if bank account balance has sufficient fund for topping up the user wallet.
# 
# Each user's bank account balance is 10000. 
# Bank balance will be deduced accordingly.
#
# Parameters:
# bank_user : bank user id
# user_key : a key which hold by wallet and bank to verify user identity
# wallet_api_token : issued by bank for Wallet App to verify Wallet identity
# amount : top up amount
#
# JSON data:
# trx_id : if withdrawal is successed, a transcation will be generated
#           stored in bank db. Pass it back to Wallet
# status : return signal to Wallet
#
# author : Cheryl Kwong
# --------------------------------------------------------------------------

def generate_publickey(privatekey):
    curve = registry.get_curve('brainpoolP256r1')
    public_key = privatekey * curve.g
    return public_key

def bank_api(request,bank_user,user_key,wallet_api_token,amount):
    try:
        wallet = WalletAccount.objects.get(bank_user=bank_user)
    except WalletAccount.DoesNotExist:
        return JsonResponse({"error": "Bank account not exist"},status=404)
    else:
        # generate parameter user key into public key format , generate stored key into public key
        # to compare both keys to authenicate user identity
        # check wallet API to authenicate Wallet identity
        # check sufficiate fund to withdrawn from bank account to top up the user wallet

        get_bank_user = generate_publickey(int(wallet.user_key))
        get_request_user = generate_publickey(int(user_key))
        if get_bank_user == get_request_user and wallet_api_token == str(wallet.wallet_api_token):
            topup_amount = Decimal(amount)
            if wallet.balance >= topup_amount :
                newbalance = wallet.balance - topup_amount
                WalletAccount.objects.filter(bank_user=bank_user).update(balance=newbalance)
                trx_id = uuid.uuid4()
                return JsonResponse({"trx_id": trx_id, "status": "success"},safe=False)
            else:
                return JsonResponse({"status": "fail","message": "Insufficant fund!"},safe=False)
        else:
            return JsonResponse({"status": "fail","message": "Security issue: Invalid user"},safe=False)
