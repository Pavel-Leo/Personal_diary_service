from http import HTTPStatus
from django.test import Client, TestCase


class AboutURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_url_exists_at_desired_location(self):
        """Общедоступные страницы about доступны любому пользователю."""
        about_url = {
            "/about/tech/": HTTPStatus.OK,
            "/about/author/": HTTPStatus.OK,
        }
        for address, status in about_url.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status)

    def test_about_urls_uses_correct_template(self):
        """URL-адрес приложения about использует соответствующий шаблон."""
        templates_url = {
            "/about/tech/": "about/tech.html",
            "/about/author/": "about/author.html",
        }
        for address, template in templates_url.items():
            with self.subTest(template=template):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
