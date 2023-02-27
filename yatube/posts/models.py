from django.contrib.auth import get_user_model
from django.db import models

from core.models import CreatedModel

User = get_user_model()
TEXT_SYMBOLS = 15


class Post(models.Model):
    text = models.TextField(
        verbose_name="Текст поста", help_text="Напишите текст поста"
    )
    pub_date = models.DateTimeField(
        verbose_name="Дата публикации", auto_now_add=True, db_index=True
    )
    author = models.ForeignKey(
        User,
        verbose_name="Автор",
        on_delete=models.CASCADE,
        related_name="posts",
    )
    group = models.ForeignKey(
        "Group",
        verbose_name="Группа",
        help_text="Нажмите, чтобы выбрать группу",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="posts",
    )
    image = models.ImageField("Картинка", upload_to="posts/", blank=True)

    def __str__(self):
        return self.text[:TEXT_SYMBOLS]

    class Meta:
        ordering = ("-pub_date",)
        verbose_name = "Пост"
        verbose_name_plural = "Посты"


class Group(models.Model):
    title = models.CharField(verbose_name="Группа", max_length=200)
    slug = models.SlugField(
        verbose_name="Уникальное название группы", unique=True
    )
    description = models.TextField(verbose_name="Описание группы")

    def __str__(self):
        return self.title


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        verbose_name="Комментарий",
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        User,
        verbose_name="Автор",
        on_delete=models.CASCADE,
        related_name="comments",
    )
    text = models.TextField(
        verbose_name="Комментарий", help_text="Напишите комментарий"
    )

    def __str__(self):
        return self.text[:TEXT_SYMBOLS]

    class Meta:
        ordering = ("-created",)
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"


class Follow(CreatedModel):
    user = models.ForeignKey(
        User,
        verbose_name="Подписчик",
        on_delete=models.CASCADE,
        related_name="follower",
    )
    author = models.ForeignKey(
        User,
        verbose_name="Автор",
        on_delete=models.CASCADE,
        related_name="following",
    )

    def __str__(self):
        return f"{self.user} подписан на {self.author}"

    class Meta:
        ordering = ("-created",)
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
