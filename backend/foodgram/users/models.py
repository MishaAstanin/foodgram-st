from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class FoodgramUser(AbstractUser):
    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name="Адрес электронной почты",
        help_text="Уникальный адрес, не более 254 символов",
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[RegexValidator(r"^[\w.@+-]+\Z")],
        verbose_name="Имя пользователя",
        help_text="Уникальное имя, не более 150 символов",
    )
    first_name = models.CharField(
        max_length=150, verbose_name="Имя", help_text="Имя, не более 150 символов"
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name="Фамилия",
        help_text="Фамилия, не более 150 символов",
    )
    avatar = models.ImageField(
        upload_to="users_images", blank=True, null=True, verbose_name="Аватар"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "password"]

    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["id"]

    def __str__(self):
        return self.username


class Follow(models.Model):
    # Кто подписан.
    user = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Подписчик",
    )
    # На кого подписан.
    following = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Автор",
    )

    class Meta:
        verbose_name = "подписка"
        verbose_name_plural = "Подписки"
        ordering = ["id"]

    def __str__(self):
        return f"{self.user.get_username()} - {self.following.get_username()}"
