# Generated by Django 2.2.6 on 2023-02-11 21:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("posts", "0005_auto_20230124_2043"),
    ]

    operations = [
        migrations.AlterField(
            model_name="post",
            name="group",
            field=models.ForeignKey(
                blank=True,
                help_text="Выберите группу",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="groups",
                to="posts.Group",
                verbose_name="Группа",
            ),
        ),
        migrations.AlterField(
            model_name="post",
            name="text",
            field=models.TextField(
                help_text="Напишите ваш текст", verbose_name="Текст"
            ),
        ),
    ]
