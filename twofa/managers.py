from django.contrib.auth.models import BaseUserManager

# custom made the User Models
class TwoFAUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, username, email, authy_id, password, phone_number,country_code,is_active,is_staff,user_type,
                     **extra_fields):
        if not username:
            raise ValueError('The given username must be set')
        email = self.normalize_email(email)
        username = self.model.normalize_username(username)
        user = self.model(username=username, email=email,
                          authy_id=authy_id, phone_number=phone_number,country_code=country_code, is_active=is_active,is_staff=is_staff, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, authy_id=None, password=None, phone_number=None,
                    country_code=None, is_active=False,is_staff=False,
                    user_type='C',**extra_fields):
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(
            username,
            email,
            authy_id,
            password,
            phone_number,
            country_code,
            is_active,
            is_staff,
            user_type,
            **extra_fields
        )

    def create_superuser(self, username, password, email=None, authy_id=None, phone_number=None,country_code=None, is_active=True,is_staff=True,
                    user_type='A',**extra_fields):
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(
            username,
            email,
            authy_id,
            password,
            phone_number,
            country_code,
            is_active,
            is_staff,
            user_type,
            **extra_fields
        )
