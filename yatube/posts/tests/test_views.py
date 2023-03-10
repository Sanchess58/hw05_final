import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms.models import model_to_dict
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()

AMOUNT_RECORDS = 13
AMOUNT_FIRST_PAGE_RECORDS = 10
AMOUNT_NEXT_PAGE_RECORDS = 3
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PaginatorViewsTest(TestCase):
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
        for i in range(AMOUNT_RECORDS):
            cls.posts = Post.objects.bulk_create([
                Post(
                    text=f'Привет всем {i}',
                    group=cls.group,
                    author=cls.user_author,
                )
            ])
        cls.len_context = {
            reverse('posts:index'): [
                AMOUNT_FIRST_PAGE_RECORDS,
                AMOUNT_NEXT_PAGE_RECORDS
            ],
            reverse(
                'posts:group_list',
                kwargs={
                    'slug': cls.group.slug
                }
            ): [AMOUNT_FIRST_PAGE_RECORDS, AMOUNT_NEXT_PAGE_RECORDS],
            reverse(
                'posts:profile',
                kwargs={
                    'username': cls.posts[0].author
                }
            ): [AMOUNT_FIRST_PAGE_RECORDS, AMOUNT_NEXT_PAGE_RECORDS]
        }

    def setUp(self):
        cache.clear()

    def test_first_page_contains_ten_records(self):
        """Проверка, что на 1 странице 10 постов."""
        for reverse_name, leng in self.len_context.items():
            with self.subTest(reverse_name=reverse_name):
                responce = self.author_client.get(reverse_name)
                self.assertEqual(len(responce.context['page_obj']), leng[0])

    def test_second_page_contains_three_records(self):
        """Проверка, что на 2 странице находится 3 поста."""
        for reverse_name, leng in self.len_context.items():
            with self.subTest(reverse_name=reverse_name):
                responce = self.author_client.get(reverse_name + '?page=2')
                self.assertEqual(len(responce.context['page_obj']), leng[1])


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewTest(TestCase):
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
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Привет всем',
            group=cls.group,
            author=cls.user_author,
            image=cls.uploaded
        )
        cls.post_dict = model_to_dict(cls.post)
        cls.group_dict = model_to_dict(cls.group)
        cls.templates_dict = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={
                    'slug': cls.group.slug
                }
            ): 'posts/group_list.html',
            reverse(
                'posts:post_detail',
                kwargs={
                    'post_id': cls.post.pk
                }
            ): 'posts/post_detail.html',
            reverse(
                'posts:profile',
                kwargs={
                    'username': cls.post.author
                }
            ): 'posts/profile.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={
                    'post_id': cls.post.pk
                }
            ): 'posts/create_post.html',
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='Me')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_templates(self):
        """Проверка шаблонов."""
        for reverse_name, templates in self.templates_dict.items():
            with self.subTest(reverse_name=reverse_name):
                responce = self.author_client.get(reverse_name)
                self.assertTemplateUsed(responce, templates)

    def test_context_index(self):
        """Проверка передаваемого контекста на главную страницу."""
        response = self.author_client.get(reverse('posts:index'))
        first_object = model_to_dict(response.context['page_obj'][0])
        second_object = response.context['description']
        self.assertEqual(self.post_dict, first_object)
        self.assertEqual(second_object, "Последние обновления на сайте")

    def test_context_group(self):
        """Проверка передаваемого контекста
        на страницу с группами."""
        response = self.author_client.get(
            reverse(
                'posts:group_list',
                kwargs={
                    'slug': self.group.slug
                }
            )
        )
        first_object = model_to_dict(response.context['page_obj'][0])
        second_object = model_to_dict(response.context['group'])
        self.assertEqual(self.post_dict, first_object)
        self.assertEqual(self.group_dict, second_object)

    def test_context_profile(self):
        """Проверка передаваемого контекста в профиль."""
        response = self.author_client.get(
            reverse(
                'posts:profile',
                kwargs={
                    'username': self.post.author
                }
            )
        )
        author_object = response.context['author']
        check_context = model_to_dict(response.context['page_obj'][0])
        self.assertEqual(self.post_dict, check_context)
        self.assertEqual(author_object, self.user_author)

    def test_context_post_detail(self):
        """Проверка передаваемого контекста
        на страницу поста."""
        response = self.author_client.get(
            reverse(
                'posts:post_detail',
                kwargs={
                    'post_id': self.post.pk
                }
            )
        )
        first_object = model_to_dict(response.context['post'])
        self.assertEqual(self.post_dict, first_object)

    def test_context_post_create(self):
        """Проверка передаваемого контекста
        на страницу создания поста."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_context_post_edit(self):
        """Проверка передаваемого контекста
        на страницу изменения поста."""
        response = self.author_client.get(
            reverse(
                'posts:post_edit',
                kwargs={
                    'post_id': self.post.pk
                }
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertIn(response.context['is_edit'], response.context)
        self.assertEqual(response.context['is_edit'], True)

    def test_belongs_to_the_pages(self):
        """Проверка попадают ли посты на нужные страницы."""
        another_group = Group.objects.create(
            title='Не нужная группа',
            slug='lev_tolstoy1',
            description='Тестовое описание',
        )
        another_post = Post.objects.create(
            text='Привет всем, я не нужный',
            group=another_group,
            author=self.user_author,
        )
        check_posts = {
            reverse('posts:index'): another_post,
            reverse(
                'posts:group_list',
                kwargs={
                    'slug': another_group.slug
                }
            ): another_post,
            reverse(
                'posts:profile',
                kwargs={
                    'username': another_post.author
                }
            ): another_post

        }
        # Проверка, есть ли посты на нужных страницах
        for reverse_name, post in check_posts.items():
            with self.subTest(reverse_name=reverse_name):
                responce = self.authorized_client.get(reverse_name)
                self.assertIn(post, responce.context['page_obj'])
        # Проверка, нет ли поста на странице с другой группой
        responce = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={
                    'slug': self.group.slug
                }
            )
        )
        self.assertNotIn(another_post, responce.context['page_obj'])

    def test_image(self):
        """Проверка, что на страницах
        выводится нужная картинка у поста."""
        context_dict = {
            self.author_client.get(
                reverse('posts:index')
            ).context['page_obj'][0].image: self.post.image,
            self.author_client.get(
                reverse(
                    'posts:group_list',
                    kwargs={
                        'slug': self.group.slug
                    }
                )
            ).context['page_obj'][0].image: self.post.image,
            self.author_client.get(
                reverse(
                    'posts:profile',
                    kwargs={
                        'username': self.post.author
                    }
                )
            ).context['page_obj'][0].image: self.post.image,
            self.author_client.get(
                reverse(
                    'posts:post_detail',
                    kwargs={
                        'post_id': self.post.pk
                    }
                )
            ).context['post'].image: self.post.image
        }

        for reverse_name, image in context_dict.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertEqual(image, reverse_name)

    def test_cache(self):
        """Проверка кеша."""
        another_group = Group.objects.create(
            title='Не нужная группа',
            slug='lev_tolstoy1',
            description='Тестовое описание',
        )
        another_post = Post.objects.create(
            text='Привет всем, я не нужный',
            group=another_group,
            author=self.user,
        )
        response_first = self.author_client.get(reverse('posts:index'))
        before_len_delete = len(response_first.content)
        another_post.delete()
        response_second = self.author_client.get(reverse('posts:index'))
        after_len_delete = len(response_second.content)
        cache.clear()
        response_third = self.author_client.get(reverse('posts:index'))
        after_cache_delete = len(response_third.content)
        self.assertEqual(before_len_delete, after_len_delete)
        self.assertNotEqual(before_len_delete, after_cache_delete)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.follower1 = Client()
        cls.following1 = Client()
        cls.following2 = Client()
        cls.user_follower1 = User.objects.create_user(username='subscriber')
        cls.follower1.force_login(cls.user_follower1)
        cls.user_following1 = User.objects.create_user(username='avtor')
        cls.following1.force_login(cls.user_following1)
        cls.user_following2 = User.objects.create_user(username='avtor2')
        cls.following2.force_login(cls.user_following2)

    def test_following_user(self):
        """Проверка, что происходит подписка на автора."""
        count_followers = Follow.objects.count()
        self.follower1.get(
            reverse(
                'posts:profile_follow',
                kwargs={
                    'username': self.user_following1,
                }
            )
        )
        fol_1 = Follow.objects.filter(
            user=self.user_follower1,
            author=self.user_following1
        )
        if fol_1.exists():
            self.assertEqual(Follow.objects.count(), count_followers + 1)
        self.follower1.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={
                    'username': self.user_following1,
                }
            )
        )
        fol_2 = Follow.objects.filter(
            user=self.user_follower1,
            author=self.user_following1
        )
        if not fol_2.exists():
            self.assertEqual(Follow.objects.count(), count_followers)

    def test_check_post_user(self):
        """Проверка, что пост выдается тем,
        кто на него подписан."""
        group = Group.objects.create(
            title='Группа подписчики',
            slug='subscription',
            description='Тестовое описание',
        )
        author_post = Post.objects.create(
            text="Пост для подписчика",
            group=group,
            author=self.user_following1
        )
        self.follower1.get(
            reverse(
                'posts:profile_follow',
                kwargs={
                    'username': self.user_following1,
                }
            )
        )
        responce_follower = self.follower1.get(
            reverse('posts:follow_index')
        )
        responce_not_follower = self.following2.get(
            reverse('posts:follow_index')
        )
        self.assertIn(author_post, responce_follower.context['page_obj'])
        self.assertNotIn(
            author_post,
            responce_not_follower.context['page_obj']
        )

    def test_self_subscription(self):
        """Проверка подписки на самого себя."""
        count_followers = Follow.objects.count()
        self.follower1.get(
            reverse(
                'posts:profile_follow',
                kwargs={
                    'username': self.user_follower1,
                }
            )
        )
        self.assertEqual(Follow.objects.count(), count_followers)
