from django.contrib import admin
from .models import TwoFAUser,Bank,Wallet,BankList,Topup,Payment,Contract,ContactList

admin.site.register(TwoFAUser)
admin.site.register(Bank)
admin.site.register(Wallet)
admin.site.register(ContactList)
admin.site.register(BankList)
admin.site.register(Topup)
admin.site.register(Payment)
admin.site.register(Contract)

