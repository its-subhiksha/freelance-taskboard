# Generated by Django 5.2 on 2025-05-03 18:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Tasks', '0003_alter_task_client'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invitation',
            name='status',
            field=models.CharField(choices=[(1, 'Pending'), (2, 'Accepted'), (3, 'Rejected'), (4, 'Expired')], default=1, max_length=20),
        ),
    ]
