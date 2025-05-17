from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class FoodgramUser(AbstractUser):
    email = models.EmailField(
        max_length=254, unique=True, verbose_name='Адрес электронной почты')
    username = models.CharField(max_length=150, unique=True, validators=[
                                RegexValidator(r'^[\w.@+-]+\Z')], verbose_name='Имя пользователя')
    first_name = models.CharField(max_length=150, verbose_name='Имя')
    last_name = models.CharField(max_length=150, verbose_name='Фамилия')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'password']

    def __str__(self):
        return self.email
