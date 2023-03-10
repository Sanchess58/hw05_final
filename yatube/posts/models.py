from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models

from models import CheckConstraint, F, Q

User = get_user_model()

AMOUNT_SYMBOLS = 15


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name="Название"
    )
    slug = models.SlugField(
        unique=True,
        max_length=15,
        verbose_name="URL на латинице"
    )
    description = models.TextField(verbose_name="Описание")

    class Meta:
        verbose_name = "Группы"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        verbose_name="Текст",
        help_text="Напишите ваш текст"
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата и время"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="Автор",
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name="Группа",
        related_name="posts",
        help_text="Выберите группу",
    )
    image = models.ImageField(
        upload_to='posts/',
        blank=True,
        verbose_name="Картинка"
    )

    class Meta:
        verbose_name = "Посты"
        verbose_name_plural = verbose_name
        ordering = ["-pub_date"]

    def __str__(self):
        return self.text[:AMOUNT_SYMBOLS]


class Comment(models.Model):
    text = models.TextField(
        verbose_name="Текст",
        help_text="Напишите текст комментария"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Автор",
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Пост"
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата и время"
    )

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"

    def __str__(self):
        return self.text[:AMOUNT_SYMBOLS]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Подписчик"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Автор"
    )

    def clean(self):
        if self.user == self.author:
            raise ValidationError('Нельзя подписаться на себя самого')

    class Meta:
        verbose_name = "Подписчик"
        verbose_name_plural = "Подписчики"
        unique_together = ['user', 'author']
        constraints = [
            CheckConstraint(check=~Q(user=F('author')), name='not_self_sub'),
        ]

    def __str__(self):
        return f"{self.user} подписан на {self.author}"
