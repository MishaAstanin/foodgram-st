# Generated by Django 5.2.1 on 2025-05-17 17:35

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_alter_foodgramuser_email"),
    ]

    operations = [
        migrations.AlterField(
            model_name="foodgramuser",
            name="email",
            field=models.EmailField(
                max_length=254, unique=True, verbose_name="Адрес электронной почты"
            ),
        ),
        migrations.AlterField(
            model_name="foodgramuser",
            name="first_name",
            field=models.CharField(max_length=150, verbose_name="Имя"),
        ),
        migrations.AlterField(
            model_name="foodgramuser",
            name="last_name",
            field=models.CharField(max_length=150, verbose_name="Фамилия"),
        ),
        migrations.AlterField(
            model_name="foodgramuser",
            name="username",
            field=models.CharField(
                max_length=150,
                unique=True,
                validators=[django.core.validators.RegexValidator("^[\\w.@+-]+\\z")],
                verbose_name="Имя пользователя",
            ),
        ),
    ]
