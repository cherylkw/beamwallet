import phonenumbers

from authy.api import AuthyApiClient
from django import forms
from django.conf import settings
from phonenumbers.phonenumberutil import NumberParseException

from .models import TwoFAUser


authy_api = AuthyApiClient(settings.ACCOUNT_SECURITY_API_KEY)

# Create Sign Up form and SMS Token Verification Form
class BootstrapInput(forms.TextInput):
    def __init__(self, placeholder, size=12, *args, **kwargs):
        self.size = size
        super(BootstrapInput, self).__init__(attrs={
            'class': 'form-control input-sm',
            'placeholder': placeholder
        })

    def bootwrap_input(self, input_tag):
        classes = 'col-xs-{n} col-sm-{n} col-md-{n}'.format(n=self.size)

        return '''<div class="{classes}">
                    <div class="form-group">{input_tag}</div>
                  </div>
               '''.format(classes=classes, input_tag=input_tag)

    def render(self, *args, **kwargs):
        input_tag = super(BootstrapInput, self).render(*args, **kwargs)
        return self.bootwrap_input(input_tag)


class BootstrapPasswordInput(BootstrapInput):
    input_type = 'password'
    template_name = 'django/forms/widgets/password.html'


class RegistrationForm(forms.ModelForm):
    class Meta:
        model = TwoFAUser
        fields = ('username', 'email', 'password')
        widgets = {
            'username': BootstrapInput('User Name'),
            'email': BootstrapInput('Email Address'),
            'password': BootstrapPasswordInput('Password', size=6),
        }

    country_code = forms.CharField(
        widget=BootstrapInput('Country Code', size=6))
    phone_number = forms.CharField(
        widget=BootstrapInput('Phone Number', size=6))
    confirm_password = forms.CharField(
        widget=BootstrapPasswordInput('Confirm Password', size=6))

    def clean_username(self):
        username = self.cleaned_data['username']
        if TwoFAUser.objects.filter(username=username).exists():
            self.add_error('username', 'Username is already taken')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if TwoFAUser.objects.filter(email=email).exists():
            self.add_error('email', 'Email is already registered')
        return email

    def clean_country_code(self):
        country_code = self.cleaned_data['country_code']
        if not country_code.startswith('+'):
            country_code = '+' + country_code
        return country_code

    def clean(self):
        data = self.cleaned_data
        if data['password'] != data['confirm_password']:
            self.add_error(
                'password',
                'Password and confirmation did not match'
            )

        phone_number = data['country_code'] + data['phone_number']
        try:
            phone_number = phonenumbers.parse(phone_number, None)
            if not phonenumbers.is_valid_number(phone_number):
                self.add_error('phone_number', 'Invalid phone number')
        except NumberParseException as e:
            self.add_error('phone_number', e)


class TokenVerificationForm(forms.Form):
    token1 = forms.CharField(widget=forms.TextInput(attrs={'size': '1','min': '0', 'max': '9','pattern' : '[0-9]{1}'}))
    token2 = forms.CharField(widget=forms.TextInput(attrs={'size': '1','min': '0', 'max': '9','pattern' : '[0-9]{1}'}))
    token3 = forms.CharField(widget=forms.TextInput(attrs={'size': '1','min': '0', 'max': '9','pattern' : '[0-9]{1}'}))
    token4 = forms.CharField(widget=forms.TextInput(attrs={'size': '1','min': '0', 'max': '9','pattern' : '[0-9]{1}'}))
    token5 = forms.CharField(widget=forms.TextInput(attrs={'size': '1','min': '0', 'max': '9','pattern' : '[0-9]{1}'}))
    token6 = forms.CharField(widget=forms.TextInput(attrs={'size': '1','min': '0', 'max': '9','pattern' : '[0-9]{1}'}))
    token7 = forms.CharField(widget=forms.TextInput(attrs={'size': '1','min': '0', 'max': '9','pattern' : '[0-9]{1}'}))

    def is_valid(self, authy_id):
        self.authy_id = authy_id
        return super(TokenVerificationForm, self).is_valid()

    def clean(self):
        token1 = self.cleaned_data['token1']
        token2 = self.cleaned_data['token2']
        token3 = self.cleaned_data['token3']
        token4 = self.cleaned_data['token4']
        token5 = self.cleaned_data['token5']
        token6 = self.cleaned_data['token6']
        token7 = self.cleaned_data['token7']
        
        token = token1+token2+token3+token4+token5+token6+token7

        verification = authy_api.tokens.verify(self.authy_id, token)
        if not verification.ok():
            self.add_error('token', 'Invalid token')
