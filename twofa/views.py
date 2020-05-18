from authy.api import AuthyApiClient
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.db.models import Q

from django.contrib.auth import login, authenticate
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from .tokens import account_activation_token
from django.contrib import messages

from .decorators import twofa_required
from .forms import RegistrationForm, TokenVerificationForm
from .models import TwoFAUser,Wallet
from tinyec import registry
import secrets
import pyqrcode

# to api key to access twilio
authy_api = AuthyApiClient(settings.ACCOUNT_SECURITY_API_KEY)

def generate_privatekey():
    curve = registry.get_curve('brainpoolP256r1')
    private_key = secrets.randbelow(curve.field.n)
    return private_key

# Sign up Beam Wallet
# Send email activiation after created new user record
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            authy_user = authy_api.users.create(
                form.cleaned_data['email'],
                form.cleaned_data['phone_number'],
                form.cleaned_data['country_code'],
            )
            if authy_user.ok():
                twofa_user = TwoFAUser.objects.create_user(
                    form.cleaned_data['username'],
                    form.cleaned_data['email'],
                    authy_user.id,
                    form.cleaned_data['password'],
                    form.cleaned_data['phone_number'],
                    form.cleaned_data['country_code']
                )
                # send email activiation
                current_site = get_current_site(request)
                mail_subject = 'Activate your Beam Wallet account.'
                message = render_to_string('acc_active_email.html', {
                    'user': twofa_user,
                    'domain': current_site.domain,
                    'uid':urlsafe_base64_encode(force_bytes(twofa_user.pk)),
                    'token':account_activation_token.make_token(twofa_user),
                })
                to_email = form.cleaned_data['email']
                email = EmailMessage(
                            mail_subject, message, to=[to_email]
                )
                email.send()
                messages.success(request, 'A verification email has been sent. Please verify your account before login') 
                #login to account
                login(request, twofa_user)
                return redirect('token-sms')
            else:
                for key, value in authy_user.errors().items():
                    form.add_error(
                        None,
                        '{key}: {value}'.format(key=key, value=value)
                    )
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

# Token verification Form 
@login_required
def twofa(request):
    if request.method == 'POST':
        form = TokenVerificationForm(request.POST)
        if form.is_valid(request.user.authy_id):
            request.session['authy'] = True
            return redirect('protected')
    else:
        form = TokenVerificationForm()
    return render(request, '2fa.html', {'form': form})

# Send SMS with a token to register phone number after recieved, enter the token to login Beam Wallet 
@login_required
def token_sms(request):
    sms = authy_api.users.request_sms(request.user.authy_id, {'force': True})
    if sms.ok():
        return redirect('2fa')
    else:
        return HttpResponse('SMS request failed', status=503)

# After click the verification link in email, the account is verified.
# Create Wallet for new user
# Generate user qrcode for new user , store new user's private key in qrcode
def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = TwoFAUser.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        # create wallet for first login
        privatekey = generate_privatekey()
        newwallet = Wallet(user=user,private_key=privatekey)
        newwallet.save()
        # generate user qrcode for the use of merchant payment
        qr = pyqrcode.create(privatekey)
        qrcodename = request.user.username+str(request.user.phone_number)
        filename = './wallet/static/'+qrcodename+'.png'
        print('filename :',filename)
        qr.png(filename, scale=8)
        login(request, user)
        context = {
            "msg" : 'Thank you for your email confirmation. Now you can login your account.'
        }
        return render(request, 'message.html',context)
    else:
        context = {
            "msg" : 'Activation link is invalid!'
        }
        return render(request, 'message.html',context)

@twofa_required
def protected(request):
    return redirect('dashboard')

