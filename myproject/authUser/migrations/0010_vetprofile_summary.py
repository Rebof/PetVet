# Generated by Django 5.1.2 on 2025-04-12 18:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authUser', '0009_remove_petownerprofile_pet_image_pet_review'),
    ]

    operations = [
        migrations.AddField(
            model_name='vetprofile',
            name='summary',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
    ]
