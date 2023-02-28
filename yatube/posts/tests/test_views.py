import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()
CREATE_POST_QUANTITY: int = 13
PAGINATOR_FIRST_PAGE_POSTS_QUANTITY: int = 10
PAGINATOR_SECOND_PAGE_POSTS_QUANTITY: int = 3


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username="author_auth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        cls.small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.uploaded = SimpleUploadedFile(
            name="small.gif", content=cls.small_gif, content_type="image/gif"
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text="Тестовый пост больше 15 символов для проверки",
            group=cls.group,
            image=cls.uploaded,
        )
        cls.wrong_group = Group.objects.create(
            title="Неправильная группа",
            slug="wrong-slug",
            description="Тестовое описание неправильной группы",
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user_author)
        self.not_author = User.objects.create_user(username="NotAuthor_auth")
        self.authorized_client_not_author = Client()
        self.authorized_client_not_author.force_login(self.not_author)

    def test_pages_uses_correct_template(self):
        """View функция использует соответствующий шаблон."""
        templates_pages_names = {
            reverse("posts:index"): "posts/index.html",
            reverse(
                "posts:group_list", kwargs={"slug": PostViewsTest.group.slug}
            ): "posts/group_list.html",
            reverse(
                "posts:profile",
                kwargs={"username": PostViewsTest.user_author.username},
            ): "posts/profile.html",
            reverse(
                "posts:post_detail", kwargs={"post_id": PostViewsTest.post.id}
            ): "posts/post_detail.html",
            reverse("posts:post_create"): "posts/create_post.html",
            reverse(
                "posts:post_edit", kwargs={"post_id": PostViewsTest.post.id}
            ): "posts/create_post.html",
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(template=template):
                response = self.authorized_client_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def context_tests(self, response, post_detailed=False):
        """Проверка контекста отображения поста."""
        if not post_detailed:
            object = response.context["page_obj"][0]
        elif post_detailed:
            object = response.context["post"]
            post_id = object.id
            self.assertEqual(object, PostViewsTest.post)
            self.assertEqual(post_id, PostViewsTest.post.id)
        post_author = object.author
        post_text = object.text
        post_group = object.group.title
        post_image = object.image
        self.assertEqual(post_author, PostViewsTest.user_author)
        self.assertEqual(post_text, PostViewsTest.post.text)
        self.assertEqual(post_group, PostViewsTest.group.title)
        self.assertEqual(post_image, "posts/small.gif")

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client_author.get(reverse("posts:index"))
        index_caption = response.context["caption"]
        index_title = response.context["title"]
        self.assertEqual(index_caption, "Последние обновления на сайте")
        self.assertEqual(index_title, "Последние обновления на сайте")
        self.context_tests(response)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client_author.get(
            reverse(
                "posts:group_list", kwargs={"slug": PostViewsTest.group.slug}
            )
        )
        group_object = response.context["group"]
        group_title = group_object.title
        group_description = group_object.description
        group_slug = group_object.slug
        self.assertEqual(group_title, PostViewsTest.group.title)
        self.assertEqual(group_description, PostViewsTest.group.description)
        self.assertEqual(group_slug, PostViewsTest.group.slug)
        self.context_tests(response)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client_author.get(
            reverse(
                "posts:profile",
                kwargs={"username": PostViewsTest.user_author.username},
            )
        )
        author = response.context["author"].username
        self.assertEqual(author, PostViewsTest.post.author.username)
        self.context_tests(response)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client_author.get(
            reverse(
                "posts:post_detail", kwargs={"post_id": PostViewsTest.post.id}
            )
        )
        self.context_tests(response, post_detailed=True)

    def post_create_or_post_edit_support_func(self, response):
        """Вспомогательная функции для проверки правильного контекста
        шаблонов для создания и редактирования постов."""
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
            "image": forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client_author.get(
            reverse("posts:post_create")
        )
        self.post_create_or_post_edit_support_func(response)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client_author.get(
            reverse(
                "posts:post_edit", kwargs={"post_id": PostViewsTest.post.id}
            )
        )
        is_edit = response.context["is_edit"]
        self.assertIs(is_edit, True)
        self.post_create_or_post_edit_support_func(response)

    def test_post_was_added_correctly(self):
        """Проверка, что пост добавлен на главную страницу,
        на странице выбранной группы и в профайле пользователя.
        """
        response_index = self.authorized_client_author.get(
            reverse("posts:index")
        )
        response_group_list = self.authorized_client_author.get(
            reverse(
                "posts:group_list", kwargs={"slug": PostViewsTest.group.slug}
            )
        )
        response_profile = self.authorized_client_author.get(
            reverse(
                "posts:profile",
                kwargs={"username": PostViewsTest.user_author.username},
            )
        )
        self.assertIn(PostViewsTest.post, response_index.context["page_obj"])
        self.assertIn(PostViewsTest.post, response_profile.context["page_obj"])
        self.assertIn(
            PostViewsTest.post, response_group_list.context["page_obj"]
        )

    def test_post_not_in_wrong_group(self):
        """Проверка, что пост не попал в неправильную группу."""
        response_group_list = self.authorized_client_author.get(
            reverse(
                "posts:group_list",
                kwargs={"slug": PostViewsTest.wrong_group.slug},
            )
        )
        self.assertNotIn(
            PostViewsTest.post, response_group_list.context["page_obj"]
        )

    def test_cache_after_post_delete(self):
        """Проверка, что при удалении записи из базы, она остаётся в
        response.content главной страницы до тех пор, пока кэш не будет
        очищен принудительно"""
        post = Post.objects.create(
            author=PostViewsTest.user_author,
            text="Тестовый пост для проверки кеша",
            group=PostViewsTest.group,
        )
        response = self.authorized_client_author.get(reverse("posts:index"))
        check_post = response.context["page_obj"][0]
        self.assertEqual(check_post, post)
        post.delete()
        response_2 = self.authorized_client_author.get(reverse("posts:index"))
        self.assertEqual(response_2.content, response.content)
        cache.clear()
        response_3 = self.authorized_client_author.get(reverse("posts:index"))
        self.assertNotEqual(response_3.content, response.content)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="test_user")
        cls.group = Group.objects.create(
            title="Тестовый группа",
            slug="test-slug",
            description="Тестовое описание группы",
        )
        cls.some_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.uploaded = SimpleUploadedFile(
            name="some.gif", content=cls.some_gif, content_type="image/gif"
        )
        posts = []
        for i in range(CREATE_POST_QUANTITY):
            posts.append(
                Post(
                    text=f"Тестовый пост {i}",
                    author=cls.user,
                    group=cls.group,
                    image=cls.uploaded,
                )
            )
        Post.objects.bulk_create(posts)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        response = self.client.get(reverse("posts:index"))
        self.assertEqual(
            len(response.context["page_obj"]),
            PAGINATOR_FIRST_PAGE_POSTS_QUANTITY,
        )

    def test_second_page_contains_three_records(self):
        response = self.client.get(reverse("posts:index") + "?page=2")
        self.assertEqual(
            len(response.context["page_obj"]),
            PAGINATOR_SECOND_PAGE_POSTS_QUANTITY,
        )


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

    def check_post_for_following(self):
        """Создания поста для теста подписок"""
        check_post = Post.objects.create(
            text="Тестовый пост проверки кеша",
            author=FollowersTests.user,
            group=FollowersTests.group,
        )
        return check_post

    def test_post_author_visible_in_followers_list(self):
        """Проверка, что пост автора отображается в листе подписок."""
        Follow.objects.create(
            user=FollowersTests.user_2, author=FollowersTests.user
        )
        check_post = self.check_post_for_following()
        response = self.follower.get(reverse("posts:follow_index"))
        post_list = response.context["page_obj"]
        self.assertIn(check_post, post_list)

    def test_post_author_not_visible_in_followers_list(self):
        """Проверка, что пост автора не отображается у тех кто не подписан."""
        check_post = self.check_post_for_following()
        response = self.follower.get(reverse("posts:follow_index"))
        post_list = response.context["page_obj"]
        self.assertNotIn(check_post, post_list)
