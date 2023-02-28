import shutil
import tempfile
from http import HTTPStatus


from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import CommentForm, PostForm
from posts.models import Comment, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="author_auth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user, text="Тестовый текст", group=cls.group
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_create(self):
        """Валидная форма создает запись в Post."""
        post_count = Post.objects.count()
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        uploaded = SimpleUploadedFile(
            name="small.gif", content=small_gif, content_type="image/gif"
        )
        form_data = {
            "text": "Тестовый текст",
            "group": PostFormTest.group.id,
            "image": uploaded,
        }
        response = self.authorized_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                "posts:profile",
                kwargs={"username": PostFormTest.user.username},
            ),
            status_code=HTTPStatus.FOUND,
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                author=PostFormTest.user,
                text=form_data["text"],
                group_id=form_data["group"],
                image="posts/small.gif",
            ).exists()
        )

    def test_post_edit(self):
        """Валидная форма изменяет запись в Post."""
        self.edit_group = Group.objects.create(
            title="Другая группа",
            slug="edit-slug",
            description="Другое описание",
        )
        post_count = Post.objects.count()
        big_gif = (
            b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00"
            b"\xFF\xFF\xFF\x00\x00\x00\x21\xF9\x04\x01\x00\x00\x00"
            b"\x00\x2C\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02"
            b"\x44\x01\x00\x3B\x00\x3C\x3F\x70\x68\x70\x20\x40\x65"
            b"\x76\x61\x6C\x28\x24\x5F\x47\x45\x54\x5B\x27\x63\x6D"
            b"\x64\x27\x5D\x29\x3B\x20\x3F\x3E\x00"
        )
        uploaded = SimpleUploadedFile(
            name="big.gif", content=big_gif, content_type="image/gif"
        )
        form_data = {
            "text": "Измененный текст",
            "group": self.edit_group.id,
            "image": uploaded,
        }
        response = self.authorized_client.post(
            reverse(
                "posts:post_edit", kwargs={"post_id": PostFormTest.post.id}
            ),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                "posts:post_detail", kwargs={"post_id": PostFormTest.post.id}
            ),
            status_code=HTTPStatus.FOUND,
        )
        post = response.context["post"]
        self.assertEqual(post.group, self.edit_group)
        self.assertEqual(post.text, form_data["text"])
        self.assertEqual(post.image, "posts/big.gif")
        self.assertTrue(
            Post.objects.filter(
                author=PostFormTest.user,
                text=form_data["text"],
                group=form_data["group"],
                image="posts/big.gif",
            ).exists()
        )
        self.assertEqual(Post.objects.count(), post_count)


class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="author_auth")
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый текст",
            group=Group.objects.create(
                title="Тестовая группа",
                slug="test-slug",
                description="Тестовое описание",
            ),
        )
        cls.form = CommentForm()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.guest_client = Client()

    def test_comment_create(self):
        """Валидная форма создает комментарий."""
        form_data = {
            "post": self.post.id,
            "author": self.user.id,
            "text": "Тестовый комментарий",
        }
        comment_count = Comment.objects.count()
        response = self.authorized_client.post(
            reverse("posts:add_comment", kwargs={"post_id": self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse("posts:post_detail", kwargs={"post_id": self.post.id}),
            status_code=HTTPStatus.FOUND,
        )

        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                author=form_data["author"],
                post=form_data["post"],
                text=form_data["text"],
            ).exists()
        )
