from authy.api import AuthyApiClient
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Sum
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from django.contrib.auth import login, authenticate
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from twofa.tokens import account_activation_token
from django.contrib import messages
from tinyec import registry
import secrets
from decimal import Decimal

from twofa.models import TwoFAUser,Wallet,ContactList,Payment,Topup,BankList,Bank,Contract

from bank.models import WalletAccount
from twofa.views import generate_privatekey
from bank.views import bank_api
from django.db import transaction
import uuid
import requests
import json
from pyzbar.pyzbar import decode
from PIL import Image

# generate a public key by private key
# Param : privatekey - a private key
# Return : public key of the private key
def generate_publickey(privatekey):
    curve = registry.get_curve('brainpoolP256r1')
    public_key = privatekey * curve.g
    return public_key

# generate a shared key with private key and public key
# Param : private key - from user A
#         public key - from user B
# Return : a share key for user A and user B
def generate_sharedkey(privatekey,publickey):
    shared_key = privatekey*publickey
    return shared_key

# Generate a shared key for adding friend to Contact List
# check the shared key of user A and user B to
# verify their relationship
# Param : newcontact - the person who needs to be verified
# Return : the shared key if being verified
#          0 if failed to be verified
def get_sharedkey(request,newcontact):
    # retrieve private keys
    currentuser = Wallet.objects.get(user=request.user)
    userprkey = int(currentuser.private_key)
    newcontactuser = Wallet.objects.get(user=newcontact)
    newcontactprkey = int(newcontactuser.private_key)
    # generate public keys
    userpubkey = generate_publickey(userprkey)
    newcontactpubkey = generate_publickey(newcontactprkey)
    # get shared keys
    usersharedkey = generate_sharedkey(userprkey,newcontactpubkey)
    newcontactsharekey = generate_sharedkey(newcontactprkey,userpubkey)
    if usersharedkey == newcontactsharekey:
        return usersharedkey
    else:
        return "0"

# check and verify the user on Contact List
def validate_sharedkey(request,contact):
    # generate the shared key by both private keys
    getsharekey = get_sharedkey(request,contact)
    comparekey = str(getsharekey)
    # get the generated shared key and compare to the stored shared key
    sharedkey = ContactList.objects.get(user=request.user,person=contact)
    checkkey = str(sharedkey.shared_key)
    if comparekey == checkkey:
        return True
    else:
        return False

# email template
def send_email(request,recipient,subject,email_content,email_address):
    current_site = get_current_site(request)
    mail_subject = subject
    message = render_to_string('email_template.html', {
        'user': recipient,
        'domain': current_site.domain,
        'email_content': email_content,
    })
    to_email = email_address
    email = EmailMessage(
                mail_subject, message, to=[to_email]
    )
    email.send()
    return True

def payment_main(request):
    context = {
        "contactlist" : ContactList.objects.filter(user=request.user)
    }
    return render(request,"payment_main.html",context)

# Process Payment for Send to Contact and Pay to Merchant
# Param : sender - send the money
#         contact - on sender contact list and recieve payment
#         send_amount - amount to be transferred
#         description - if any message 
@transaction.atomic
def process_payment(request,sender,contact,send_amount,description):
        # take payment from sender wallet and update the balance
        sub_amount = sender.balance - send_amount
        Wallet.objects.filter(user=request.user).update(balance=sub_amount)
        # send payment to contact wallet and update the balance
        wallet_contact = Wallet.objects.get(user=contact)
        add_amount = wallet_contact.balance + send_amount
        Wallet.objects.filter(user=contact).update(balance=add_amount)
        # record the payment transaction
        trxid = uuid.uuid4()
        #print('trxid : ',trxid)
        payment = Payment(
                            trx_id = trxid,
                            credit_wallet = wallet_contact,
                            debit_wallet = sender,
                            description = description,
                            amount = send_amount,
                            pay_type = "C"
                        )
        payment.save()
        return

# Send payment to contact in contact list
# Send email Notification will be sent to both parties
# To secure and validate receiver is not hacked by 
# Elliptic-Curve Diffie-Hellman (ECDH) Key Exchange method :
#
#  1. take both private key to regenerate each public key
#  2. Regenerate shared keys using both parties's private key and public key
#  3. Validate the 2 regenerated shared key
#  4. Validate the regenerated shared key with stored shared key
#
# Param : Contact ID
@login_required
def send_payment(request,contact_id):
    if request.method == "POST":
        send_amount = request.POST["send_amount"]
        send_amount = Decimal(send_amount)
        description = request.POST["description"]
        # digital signature, validate the share key and prepare to sign the transcation
        contact = TwoFAUser.objects.get(pk=contact_id)
        result = validate_sharedkey(request,contact)
        if validate_sharedkey(request,contact):
            # check if sender has enough balance in wallet
            sender = Wallet.objects.get(user=request.user)
            sender_balance = sender.balance
            if sender_balance >= send_amount:
                # process payment
                process_payment(request,sender,contact,send_amount,description)
                #send notification email to sender
                recipient = request.user
                subject = 'Send Payment Notification'
                email_content = 'You have just sent $'+str(send_amount)+' to '+contact.username+'.'
                email_address = request.user.email
                sendemail = send_email(request,recipient,subject,email_content,email_address)
                #send notificaiton email to receiptant
                recipient = contact
                subject = 'Payment Receive Notification'
                email_content = 'You have just recieved a payment $'+str(send_amount)+' from '+request.user.username+'.'
                email_address = contact.email
                sendemail = send_email(request,recipient,subject,email_content,email_address)
                msg='Payment has been sent to '+contact.username
                messages.success(request,msg)
            else:
                messages.error(request,'Not enough balance, top up your wallet!')
            context = {
                "contactlist" : ContactList.objects.filter(user=request.user)
            }
            return render(request,"payment_main.html",context)
        else:
            messages.error(request,"Security issue : Payment not sent. Please contact support.")
            return render(request,'payment_main.html')
    else:
        context = {
            "contact" : TwoFAUser.objects.get(pk=contact_id)
        }
        return render(request,"send_payment.html",context)

# Check if contact is on the user contact list
# Param : newcontact - contact to be checked
# Return : result True or False
def is_contact(request,newcontact):
    # check if user has already built a contact list
    founduser = ContactList.objects.filter(user=request.user)
    if founduser.count() > 0 :
        person_count = ContactList.objects.filter(user=request.user,person=newcontact)
        if person_count.count() > 0 :
            return True
        else:
            return False
    else:
        return False

# Add contacts who are also registered in Beam Wallet
# Search by contact phone number
# Send email to contact to notify they are added
# Send email to user confirming the contact is added
@login_required
def add_contact(request):
    getcontact = ContactList.objects.filter(user=request.user)
    context = {
        "contactlist" : getcontact
    }
    if request.method == 'POST':
        phone_number=request.POST["phone_number"]
        try:
            # check if new contact is registered in Beam Wallet
            newcontact = TwoFAUser.objects.get(phone_number=phone_number,user_type="C")
        except TwoFAUser.DoesNotExist:
            messages.error(request, 'Contact is not found in Beam Wallet!')
        else:
            # check if new contact has already in user's contract list
            if is_contact(request,newcontact):
                messages.error(request, 'Contact already exist in your contact list!')
            else:
                if newcontact.phone_number == request.user.phone_number:
                    messages.error(request,'Cannot add yourself to your contact list!')
                else:
                    getsharedkey = get_sharedkey(request,newcontact)
                    #add to contactlist
                    contactlist = ContactList(user=request.user,person=newcontact,shared_key=getsharedkey)
                    print("user : ",request.user)
                    print("person : ",newcontact)
                    contactlist.save()
                    #send notificaiton email to user
                    recipient = request.user
                    subject = 'New Contact Notification'
                    email_content = 'New contact '+newcontact.username+' has been added to your contact list.'
                    email_address = request.user.email
                    sendemail = send_email(request,recipient,subject,email_content,email_address)
                    #send notificaiton email to new contact
                    recipient = newcontact
                    subject = 'New Contact Notification'
                    email_content = 'You are being added to the contact list of '+request.user.username+ ' . Login to your wallet to add '+request.user.username+' to your contact list.'
                    email_address = newcontact.email
                    sendemail = send_email(request,recipient,subject,email_content,email_address)
                    messages.success(request, 'Contact Added! A notification has been sent to you and your new contact')
    else:
        return render(request,'add_contact.html',context)
    return render(request,'add_contact.html',context)

# Connect user bank account to user wallet so that they can top up their Beam Wallet
# In this project, since it has not connected to any real bank, a bank account will be created 
# in Bank App. 4 field values are to be created :
#   1. bank_user - user key of the bank, generated by uuid.uuid4()
#   2. user_key - private key which used to perform Elliptic-Curve Diffie-Hellman (ECDH) Key Exchange
#                 when transcation (Top up) need to be performed
#   3. wallet_api_token - in production level, it should be issued by bank so that they have acess to 
#                         send and recieve JSON data using api
#                       - in development level, I pre-entered the api-token for wallet by bank
# Above keys are the digital signature to identify their connection between wallet and bank during Top up
@login_required
def add_bank(request):
    if request.method == 'POST':
        bank_option = Bank.objects.get(id=request.POST["bank_option"])
        try:
            has_bank = BankList.objects.get(user=request.user,bank=bank_option)
        except BankList.DoesNotExist:
            print("has bank : ")
            bank_user = uuid.uuid4()
            genkey = generate_privatekey()
            print("bank option : ",bank_option)
            addbank = BankList(user=request.user,bank=bank_option,user_key=genkey,bank_user=bank_user)
            addbank.save()
            # assume that bank side has already a wallet account. A simple bank account created here because of testing
            wallet_acct = WalletAccount(bank_user=bank_user,user_key=genkey,wallet_api_token=bank_option.wallet_api_token,balance=10000)
            wallet_acct.save()
            messages.success(request,'Bank added. You can now topup your wallet.')
        else:
            print('has bank : ',has_bank)
            messages.error(request,'Bank has already added.')
    context = {
        'bank' : Bank.objects.all(),
        'banklist' : BankList.objects.filter(user=request.user)
    }
    return render(request,'add_bank.html',context)

# Top up use wallet from user bank account
# Call Bank APP to withdrawal funds and return JSON format data
# If withdrawal successed , a transcation ID and status code will be returned
# Update user wallet balance
# Record the transcation
@login_required
def top_up(request):
    if request.method == "POST":
        topup_amount = request.POST["amount"]
        bank_option = Bank.objects.get(id=request.POST["bank_option"])
        topup_bank = BankList.objects.get(user=request.user,bank=bank_option)
        # items for parameter pass to bank_api
        user_key = str(topup_bank.user_key)
        wallet_api_token = str(topup_bank.bank.wallet_api_token)
        bank_user = topup_bank.bank_user

        # get API data in JSON format for bank in other URL
        #   current_site = get_current_site(request)
        #   get_site = "http://"+str(current_site) +"/bank_api/"
        #   params = {"user_key": user_key, "wallet_api_token": wallet_api_token, "amount": amount}
        #   res = requests.get(get_site, params=params)

        # call function to get API JSON data in local Bank APP
        res = bank_api(request,bank_user=bank_user,user_key=user_key, wallet_api_token=wallet_api_token, amount=topup_amount)
        temp_res = res.content
        # convert data in bytes into json format
        my_json = temp_res.decode('utf8').replace("'",'"')
        data = json.loads(my_json)
        
        user_wallet = Wallet.objects.get(user=request.user)
        if data["status"] == "success":
            # update wallet balance and record the transcation
            newbalance = user_wallet.balance + Decimal(topup_amount)
            topup = Topup(trx_id=data["trx_id"],bank=bank_option,wallet=user_wallet,amount=Decimal(topup_amount))
            topup.save()
            Wallet.objects.filter(user=request.user).update(balance=newbalance)
            messages.success(request,"Top up success!")
        elif data["status"] == "fail":
            messages.success(request,data["message"])
    context = {
        'banklist' : BankList.objects.filter(user=request.user)
    }
    return render(request,'top_up.html',context)

# Add Merchant to user wallet so that user can purchase using wallet
# Create a contract and shared key as digital signature
@login_required
def add_merchant(request):
    getmerchant = Contract.objects.filter(user=request.user)
    if request.method == 'POST':
        merchant_option = TwoFAUser.objects.get(id=request.POST["merchant_option"])
        try:
            has_added = Contract.objects.get(user=request.user,merchant=merchant_option)
            messages.error(request,'Merchant has already added.')
        except Contract.DoesNotExist:
            sharedkey = get_sharedkey(request,merchant_option)
            addmerchant = Contract(user=request.user,merchant=merchant_option,shared_key=sharedkey)
            addmerchant.save()
            messages.success(request,'Merchant added.')
    context = {
        "getmerchant" : getmerchant,
        'merchantlist' : TwoFAUser.objects.filter(user_type='M')
    }
    return render(request,'add_merchant.html',context)

# Pay merchant page
@login_required
def pay_merchant_main(request):
    context = {
        'customerlist' : Contract.objects.filter(merchant=request.user)
    }
    return render(request,'pay_merchant_main.html',context)

# Display user qrcode for scanner (if any implemented) on user wallet side
@login_required
def show_qrcode(request):
    pathname = str(request.user.username) + str(request.user.phone_number) + ".png"
    print("path : ",pathname)
    context = {
        "filename" : pathname
    }
    return render(request,"show_qrcode.html",context)

# Display user qrcode for payment scanning on merchant side
# Merchant find user on their contact list and open the qrcode
@login_required
def pay_merchant_qrcode(request):
    customer = TwoFAUser.objects.get(id=request.POST["customer_option"])
    print("username : ",customer.username)
    pathname = customer.username + str(customer.phone_number) + ".png"
    context = {
        "type" : "I",
        "customer_name" : customer.username,
        "customer_id" : request.POST["customer_option"],
        "filename" : pathname
    }
    return render(request,'pay_merchant_qrcode.html',context)

# Pay merchant using qrcode on merchant side
# Since don't have any scanner device can be implemented in development stage
# the functional design:
#  front end
#   1. search customers on contact list
#   2. open the qrcode (at this stage can directly scan the code if have scanner connected)
#   3. Enter the amount and any reference
#   4. Press the button scan to stimulate the scanner function
#  Back end
#   1. verify customer identity by qrcode data (private key)
#   2. verify customer wallet balance
#   3. credit Merchant Wallet and debit user wallet
#   4. record the payment transcation
#   5. Send email notification to user
@login_required
def pay_merchant(request):
    # read qrcode data
    pathname = "./wallet/static/" + request.POST["filename"]
    qrcode = decode(Image.open(pathname))
    private_key=qrcode[0].data.decode('ascii')
    # prepare data to record
    customer = TwoFAUser.objects.get(id=request.POST["customer_id"])
    customer_wallet = Wallet.objects.get(user=customer)
    merchant = TwoFAUser.objects.get(id=request.user.id)
    merchant_wallet = Wallet.objects.get(user=merchant)
    # if qrcode belongs to customer and customer balance has enough to pay
    if private_key == customer_wallet.private_key and customer_wallet.balance > Decimal(request.POST["amount"]):
        # debit customer and credit merchant balance
        credit_amt = Decimal(request.POST["amount"]) + merchant_wallet.balance
        debit_amt = customer_wallet.balance - Decimal(request.POST["amount"])
        Wallet.objects.filter(user=customer).update(balance = debit_amt)
        Wallet.objects.filter(user=merchant).update(balance = credit_amt)
        # record this payment transcation
        trx_id = uuid.uuid4()
        newpayment=Payment(
            trx_id=trx_id,
            credit_wallet=merchant_wallet,
            debit_wallet=customer_wallet,
            description=request.POST["description"],
            amount = Decimal(request.POST["amount"]),
            pay_type = "M"
        )
        newpayment.save()
        #send payment notificaiton email to customer
        recipient = customer
        subject = 'Payment Notification'
        email_content = 'You have just paid '+merchant.username+' '+'$'+str(request.POST["amount"])+'. '
        email_address = customer.email
        sendemail = send_email(request,recipient,subject,email_content,email_address)
        messages.success(request,"Payment success!")
    else:
        messages.error(request,"Payment transcation failed. Either customer account not linked or insufficent fund.")
    context = {
    "type" : "R",
    "trx_id" : trx_id
    }
    return render(request,'pay_merchant_qrcode.html',context)

# Retrieve and display customer payment transcation records for Merchant
@login_required
def customer_payrec(request,customer_id):
    customer = TwoFAUser.objects.get(pk=customer_id)
    customer_wallet = Wallet.objects.get(user=customer)
    merchant_wallet = Wallet.objects.get(user=request.user)
    try:
        get_record = Payment.objects.filter(debit_wallet=customer_wallet,credit_wallet=merchant_wallet,pay_type="M").order_by("trx_date")
    except Payment.DoesNotExist:
        get_total = 0
        get_record = ""
    else:
        get_total = get_record.aggregate(Sum('amount'))
    context = {
        "record" : get_record,
        "total" : get_total["amount__sum"],
        "customer_name" : customer.username,
        "customer_id" : customer.id
    }
    return render(request,"customer_payrec.html",context)

# display customer list for Merchant
@login_required
def customer_list(request):
    try:
        customer_list = Contract.objects.filter(merchant=request.user).order_by('user')
    except Contract.DoesNotExist:
        messages.error("No customers exist.")
        customer_list = ""
    context = {
        "customer_list" : customer_list
    }
    return render(request,'customer_list.html',context)

# pass spending analysis data to c3.js donut chart on user dashboard
# using api Json format
# data reflect the spending behavior of user, calculation base on balance proportion on
# top up, send money to contacts , pay merchant and recieve money from contacts
@login_required
def retrieve_data_api(request):
    # Get the total of different kinds of spending
    user_wallet = Wallet.objects.get(user=request.user)
    # get initial fund
    try:
        get_top=Topup.objects.filter(wallet=user_wallet)
    except Topup.DoesNotExist :
        top_up_total = 0
    else:
        top_up_total = Topup.objects.filter(wallet=user_wallet).order_by('id')[0]
        top_up_total = top_up_total.amount
        # retrieve the other top up amount
        top_up_rest = Topup.objects.filter(wallet=user_wallet).aggregate(Sum('amount'))
        if top_up_rest["amount__sum"] is None :
            top_up_rest = 0
            top_up = 0
        else:
            # if there are top up other than the initial fund, then calculate %
            top_up_rest = top_up_rest["amount__sum"]
            top_up_cal = top_up_rest - top_up_total
            if top_up_cal == 0:
                top_up = 1
            else:
                top_up = (top_up_cal / top_up_total) * 100
                top_up = round(top_up,2)
        # receive from friends on list
        receive_total = Payment.objects.filter(credit_wallet=user_wallet).aggregate(Sum('amount'))
        if receive_total["amount__sum"] is None or receive_total["amount__sum"] == 0 :
            receive_total = 0
            receive = 0
        else:
            receive_total = receive_total["amount__sum"]
            receive = (receive_total / top_up_total) * 100
            receive = round(receive,2)
        # send to friends on list
        sent_total =  Payment.objects.filter(debit_wallet=user_wallet,pay_type='C').aggregate(Sum('amount'))
        if sent_total["amount__sum"] is None or sent_total["amount__sum"] == 0 :
            sent_total = 0
            sent = 0
        else:
            sent_total = sent_total["amount__sum"]
            sent = (sent_total / top_up_total) * 100
            sent = round(sent,2)
        # paid to merchant
        paid_total = Payment.objects.filter(debit_wallet=user_wallet,pay_type='M').aggregate(Sum('amount'))
        if paid_total["amount__sum"] is None or paid_total["amount__sum"] == 0  :
            paid_total = 0
            json_paid = 0
        else:
            paid_total = paid_total["amount__sum"]
            json_paid = (paid_total / top_up_total) * 100
            json_paid = round(json_paid,2)
        
    return JsonResponse({"Paid": json_paid,"Receive": receive,"Send": sent,"Top UP": top_up},safe=False)

# Perpare data to display on user and merchant dashboard
@login_required
def dashboard(request):
    user_wallet = Wallet.objects.get(user=request.user)
    if request.user.user_type == "C":
        # Get the total of different kinds of spending
        top_up_total = Topup.objects.filter(wallet=user_wallet).aggregate(Sum('amount'))
        if top_up_total["amount__sum"] is None :
            top_up_total = 0
        else:
            # format amount with 2 decimal place
            top_up_total = "{:10.2f}".format(top_up_total["amount__sum"])

        receive_total = Payment.objects.filter(credit_wallet=user_wallet).aggregate(Sum('amount'))
        if receive_total["amount__sum"] is None :
            receive_total = 0
        else:
            # format amount with 2 decimal place
            receive_total = "{:10.2f}".format(receive_total["amount__sum"])

        sent_total =  Payment.objects.filter(debit_wallet=user_wallet,pay_type='C').aggregate(Sum('amount'))
        if sent_total["amount__sum"] is None :
            sent_total = 0
        else:
            # format amount with 2 decimal place
            sent_total = "{:10.2f}".format(sent_total["amount__sum"])

        paid_total = Payment.objects.filter(debit_wallet=user_wallet,pay_type='M').aggregate(Sum('amount'))
        if paid_total["amount__sum"] is None :
            paid_total = 0
        else:
            # format amount with 2 decimal place
            paid_total = "{:10.2f}".format(paid_total["amount__sum"])

        # retrieve transcation record of different kind of spending
        top_up = Topup.objects.filter(wallet=user_wallet).order_by("-trx_date")
        receive = Payment.objects.filter(credit_wallet=user_wallet).order_by("-trx_date")
        sent = Payment.objects.filter(debit_wallet=user_wallet,pay_type='C').order_by("-trx_date")
        paid = Payment.objects.filter(debit_wallet=user_wallet,pay_type='M').order_by("-trx_date")

        context = {
            "totalbalance" : user_wallet.balance,
            "top_up_total" : top_up_total,
            "receive_total" : receive_total,
            "sent_total" : sent_total,
            "paid_total" : paid_total,
            "topup_list" : top_up,
            "receive_list" : receive,
            "sent_list" : sent,
            "paid_list" : paid
        }

        return render(request,"dashboard.html",context)
    elif request.user.user_type == "M":
        try:
            customer_list = Contract.objects.filter(merchant=request.user).order_by("sign_date")
        except Contract.DoesNotExist:
            customer_list = ""
        try:
            receive_trans = Payment.objects.filter(credit_wallet=user_wallet,pay_type='M')
        except Payment.DoesNotExist:
            context = {
                "totalbalance" : 0,
                "receive_trans" : "",
                "customer_list" : customer_list
            }
        else:
            receive_trans = Payment.objects.filter(credit_wallet=user_wallet,pay_type='M').order_by("-trx_date")
            context = {
                "totalbalance" : user_wallet.balance,
                "receive_trans" : receive_trans,
                "customer_list" : customer_list
            }
            return render(request,"merchant_dashboard.html",context)


