# Generated by Django 5.2 on 2025-05-12 11:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Tasks', '0009_remove_task_attachement_files_taskattachment'),
    ]

    operations = [
        migrations.AddField(
            model_name='taskattachment',
            name='original_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='taskattachment',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='tasks/attachments/'),
        ),
    ]
