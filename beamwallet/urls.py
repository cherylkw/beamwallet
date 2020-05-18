from django.conf import settings
from django.urls import path,re_path
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from twofa import views as twofa_views
from phone_verification import views as verify_views
from wallet import views as wallet_views
from bank import views as bank_views
from django.contrib import admin
from django.conf.urls import url

urlpatterns = [
     path('login/', auth_views.LoginView.as_view(), name='login'),
     path('logout/', auth_views.LogoutView.as_view(), name='logout'),

     path('register/', twofa_views.register, name='register'),
     path('2fa/', twofa_views.twofa, name='2fa'),
     path('token/sms', twofa_views.token_sms, name='token-sms'),
     path('protected/', twofa_views.protected, name='protected'),

     path('verification/token/', verify_views.token_validation, name='token_validation'),

     path('activate/(<uidb64>[0-9A-Za-z_\-]+)/(<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/',
          twofa_views.activate, name='activate'),
     path('admin/', admin.site.urls),

     path('add_contact/',wallet_views.add_contact,name='add_contact'),
     path('payment_main/', wallet_views.payment_main,name='payment_main'),
     path('send_payment/<int:contact_id>', wallet_views.send_payment,name='send_payment'),

     path('add_bank/',wallet_views.add_bank,name='add_bank'),
     path('top_up/',wallet_views.top_up,name='top_up'),
     re_path(r'^(?P<amount>\d+\.\d+)$', bank_views.bank_api, name='bank_api'),

     path('add_merchant/',wallet_views.add_merchant,name='add_merchant'),
     path('pay_merchant_main/',wallet_views.pay_merchant_main,name='pay_merchant_main'),
     path('pay_merchant_qrcode/',wallet_views.pay_merchant_qrcode,name='pay_merchant_qrcode'),
     path('pay_merchant/',wallet_views.pay_merchant,name='pay_merchant'),

     path('retrieve_data_api/',wallet_views.retrieve_data_api,name="retrieve_data_api"),
     path('dashboard',wallet_views.dashboard,name="dashboard"),
     path('show_qrcode/',wallet_views.show_qrcode,name="show_qrcode"),
     path('customer_payrec/<int:customer_id>',wallet_views.customer_payrec,name="customer_payrec"),
     path('customer_list/',wallet_views.customer_list,name="customer_list"),
     path('', twofa_views.protected, name='protected'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
