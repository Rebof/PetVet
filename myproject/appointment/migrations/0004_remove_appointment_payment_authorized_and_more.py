# Generated by Django 5.1.2 on 2025-03-29 10:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('appointment', '0003_appointment_payment_authorized_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='appointment',
            name='payment_authorized',
        ),
        migrations.RemoveField(
            model_name='appointment',
            name='payment_captured',
        ),
        migrations.RemoveField(
            model_name='appointment',
            name='payment_token',
        ),
    ]
