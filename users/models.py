from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from users.choices import ROLE_CHOICES


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('이메일은 필수입니다')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


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
