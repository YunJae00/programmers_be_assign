from datetime import datetime

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from rest_framework_simplejwt.tokens import RefreshToken

from users.choices import ROLE_CHOICES
from users.exceptions import InvalidSignInInfo, InvalidCredentials


class UserManager(BaseUserManager):

    def create_user(self, email, password, name):
        if not email:
            raise ValueError('이메일은 필수입니다')

        email = self.normalize_email(email)
        user = User.objects.create(
            email=email,
            name=name,
            role='COMPANY'
        )

        if not password:
            raise ValueError('비밀번호는 필수입니다')

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

    def get_tokens_for_user(self, email, password):
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise InvalidSignInInfo()

        if user.check_password(password):
            refresh = RefreshToken.for_user(user)
        else:
            raise InvalidCredentials()

        exp = datetime.fromtimestamp(refresh.access_token.payload.get("exp"))

        return user, {
            "id": user.id,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "exp": exp,
        }


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        verbose_name="이메일",
        max_length=100,
        unique=True,)
    password = models.CharField(
        verbose_name="비밀 번호",
        max_length=255,
    )
    name = models.CharField(
        verbose_name="이름",
        max_length=255,)
    role = models.CharField(
        verbose_name='역할',
        max_length=10,
        choices=ROLE_CHOICES,
        default='company')

    is_staff = models.BooleanField(
        verbose_name="어드민 사용자 여부",
        default=False)
    is_superuser = models.BooleanField(
        verbose_name="슈퍼유저 여부",
        default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.email
