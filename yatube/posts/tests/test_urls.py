from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from ..models import Comment, Follow, Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username="noname")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test_slug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text="Тестовый пост больше 15 символов для проверки",
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user_author)
        self.not_author = User.objects.create_user(username="NotAuthor_auth")
        self.authorized_client_not_author = Client()
        self.authorized_client_not_author.force_login(self.not_author)

    def test_public_url_exists_at_desired_location(self):
        """Общедоступные страницы доступны любому пользователю."""
        public_pages_url_names = {
            "/": HTTPStatus.OK,
            f"/profile/{PostURLTests.user_author}/": HTTPStatus.OK,
            f"/posts/{PostURLTests.post.id}/": HTTPStatus.OK,
            f"/group/{PostURLTests.group.slug}/": HTTPStatus.OK,
            "/unexisting_page/": HTTPStatus.NOT_FOUND,
        }
        for address, status in public_pages_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status)

    def test_not_auth_user_can_not_create_posts(self):
        """Неавторизованный пользователь не может создать посты
        и происходит редирект на страницу login.
        """
        response = self.guest_client.get("/create/", follow=True)
        self.assertRedirects(response, "/auth/login/?next=/create/")

    def test_auth_url_exists_at_desired_location(self):
        """Доступные страницы для авторизованного пользователя."""
        response = self.authorized_client_not_author.get("/create/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_auth_author_can_edit_own_post(self):
        """Авторизованный пользователь автор может редактировать свой пост"""
        response = self.authorized_client_author.get(
            f"/posts/{PostURLTests.post.id}/edit/"
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_auth_can_nott_edit_others_posts(self):
        """Авторизованный пользователь не может редактировать чужие посты."""
        response = self.authorized_client_not_author.get(
            f"/posts/{PostURLTests.post.id}/edit/"
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            "/": "posts/index.html",
            f"/group/{PostURLTests.group.slug}/": "posts/group_list.html",
            f"/profile/{PostURLTests.user_author}/": "posts/profile.html",
            f"/posts/{PostURLTests.post.id}/": "posts/post_detail.html",
            f"/posts/{PostURLTests.post.id}/edit/": "posts/create_post.html",
            "/create/": "posts/create_post.html",
            "/unexisting_page/": "core/404.html",
        }
        for address, template in templates_url_names.items():
            with self.subTest(template=template):
                response = self.authorized_client_author.get(address)
                self.assertTemplateUsed(response, template)

    def test_guest_not_create_comment(self):
        """Неавторизованный пользователь не может создать комментарий."""
        form_data = {
            "post": self.post.id,
            "author": self.user_author.id,
            "text": "Тестовый комментарий",
        }
        comment_count = Comment.objects.count()
        self.guest_client.post(
            reverse("posts:add_comment", kwargs={"post_id": self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), comment_count)


class FollowersTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="author")
        cls.user_2 = User.objects.create_user(username="follower")
        cls.group = Group.objects.create(
            title="Тестовый группа",
            slug="test-slug",
            description="Тестовое описание группы",
        )

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(FollowersTests.user)
        self.follower = Client()
        self.follower.force_login(FollowersTests.user_2)

    def test_follow_author(self):
        """Проверка, что пользователь может подписаться на другого
        пользователя.
        """
        follow_list = Follow.objects.count()
        self.follower.get(
            reverse(
                "posts:profile_follow",
                kwargs={"username": FollowersTests.user.username},
            )
        )
        self.assertEqual(follow_list + 1, Follow.objects.count())

    def test_unfollow_author(self):
        """Проверка, что пользователь может отписаться от другого
        пользователя.
        """
        self.follower.get(
            reverse(
                "posts:profile_follow",
                kwargs={"username": FollowersTests.user.username},
            )
        )
        follow_list = Follow.objects.count()
        self.follower.get(
            reverse(
                "posts:profile_unfollow",
                kwargs={"username": FollowersTests.user.username},
            )
        )
        self.assertEqual(follow_list - 1, Follow.objects.count())
