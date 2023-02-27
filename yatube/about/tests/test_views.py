from http import HTTPStatus
from django.test import Client, TestCase
from django.urls import reverse


class StaticViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_pages_accessible_by_name(self):
        """Общедоступные страницы about доступны любому пользователю."""
        about_names = {
            reverse("about:tech"): HTTPStatus.OK,
            reverse("about:author"): HTTPStatus.OK,
        }
        for reverse_name, status in about_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(response.status_code, status)

    def test_about_pages_uses_correct_template(self):
        """При запросе к адресам about по имени
        применяется соответствующий html шаблон."""
        templates_pages_names = {
            reverse("about:tech"): "about/tech.html",
            reverse("about:author"): "about/author.html",
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(template=template):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
