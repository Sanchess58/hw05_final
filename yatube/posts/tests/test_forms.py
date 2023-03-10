import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostTestForm(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_client = Client()
        cls.user_author = User.objects.create_user(username='admin2')
        cls.author_client.force_login(cls.user_author)
        cls.user = User.objects.create_user(username='leo')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.guest_client = Client()
        cls.group = Group.objects.create(
            title="Группа такая-то",
            slug="takaya-to",
            description="Описание такое-то"
        )
        cls.post = Post.objects.create(
            text="Текст поста такой",
            group=cls.group,
            author=cls.user_author,
        )
        cls.comment = Comment.objects.create(
            text="Комментарий текст",
            author=cls.user,
            post=cls.post
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Проверка на добавление поста и редирект."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст написал',
            'group': self.group.id,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user_author})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data.get('text'),
                group=form_data.get('group'),
            ).exists()
        )

    def test_edit_post(self):
        """Проверка на изменение поста и редирект."""
        posts_count = Post.objects.count()
        form_data = {
            'text': "Текст поста изменил",
            'group': self.group.id,
        }

        response = self.author_client.post(
            reverse(
                'posts:post_edit',
                kwargs={
                    'post_id': self.post.pk
                }
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertEqual(response.context['post'].text, form_data.get('text'))

    def test_create_post_image(self):
        """Проверка на добавление поста с картинкой и редирект."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Текст написал',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user_author})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data.get('text'),
                group=form_data.get('group'),
                image='posts/small.gif'
            ).exists()
        )

    def test_create_comment(self):
        """Проверка на добавление комментария."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Новый комментарий',
        }
        response = self.authorized_client.post(reverse(
            'posts:add_comment',
            kwargs={
                'post_id': self.post.pk
            }
        ),
            data=form_data,
            follow=True
        )
        self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={
                    'post_id': self.post.pk
                }
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertNotEqual(Comment.objects.count(), comments_count + 2)
        self.assertTrue(
            Comment.objects.filter(
                text=form_data.get('text'),
            ).exists()
        )
