import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase, override_settings

from ..models import Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_client = Client()
        cls.user_author = User.objects.create_user(username='admin2')
        cls.author_client.force_login(cls.user_author)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='lev_tolstoy',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            group=cls.group,
            text='Тестовый пост',
        )
        cls.available_to_authorized = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.post.author}/': 'posts/profile.html',
            f'/posts/{cls.post.pk}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
        }
        cls.status_codes = {
            '/': HTTPStatus.OK.value,
            f'/group/{cls.group.slug}/': HTTPStatus.OK.value,
            f'/profile/{cls.post.author}/': HTTPStatus.OK.value,
            f'/posts/{cls.post.pk}/': HTTPStatus.OK.value,
            '/create/': [HTTPStatus.OK.value, HTTPStatus.FOUND.value],
            '/unexisting_page/': HTTPStatus.NOT_FOUND.value,
            f'/posts/{cls.post.pk}/edit/': [
                HTTPStatus.OK.value,
                HTTPStatus.FOUND.value
            ],
            f'posts/{cls.post.pk}/comment/': HTTPStatus.FOUND.value,
            '/follow/': HTTPStatus.OK.value,
            f'/profile/{cls.post.author}/follow/': HTTPStatus.FOUND.value,
            f'/profile/{cls.post.author}/unfollow/': HTTPStatus.FOUND.value,
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_template_and_url(self):
        """Проверка шаблонов для автора."""
        for address, template in self.available_to_authorized.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_status_code_guest(self):
        """Проверка доступности страниц для любого пользователя."""
        for address, status in self.status_codes.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                if (
                    address == '/create/'
                    or address == f'/posts/{self.post.pk}/edit/'
                ):
                    self.assertEqual(response.status_code, status[1])

    def test_status_code_authorized(self):
        """Проверка доступности страниц для авторизованного пользователя."""
        for address, status in self.status_codes.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                if address == '/create/':
                    self.assertEqual(response.status_code, status[0])
                if (address == f'/posts/{self.post.pk}/edit/'):
                    self.assertEqual(response.status_code, status[1])

    def test_post_edit_url_responce_author(self):
        """Страница /posts/post_id/edit/ доступна автору
        и открывается верный шаблон."""
        responce = self.author_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertEqual(responce.status_code, 200)
        self.assertTemplateUsed(responce, 'posts/create_post.html')

    @override_settings(DEBUG=False)
    def test_custom_page(self):
        """Проверка кастомной страницы ошибки."""
        responce = self.author_client.get('/unexisting_page/')
        self.assertTemplateUsed(responce, 'core/404.html')
