from authy.api import AuthyApiClient
from django.conf import settings
from django.shortcuts import render, redirect

from .forms import VerificationForm, TokenForm

authy_api = AuthyApiClient(settings.ACCOUNT_SECURITY_API_KEY)

def token_validation(request):
    if request.method == 'POST':
        form = TokenForm(request.POST)
        if form.is_valid():
            verification = authy_api.phones.verification_check(
                request.session['phone_number'],
                request.session['country_code'],
                form.cleaned_data['token']
            )
            if verification.ok():
                request.session['is_verified'] = True
                return redirect('verified')
            else:
                for error_msg in verification.errors().values():
                    form.add_error(None, error_msg)
    else:
        form = TokenForm()
    return render(request, 'token_validation.html', {'form': form})

