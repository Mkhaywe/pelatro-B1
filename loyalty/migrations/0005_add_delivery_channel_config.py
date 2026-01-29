# Generated manually to add DeliveryChannelConfig model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loyalty', '0004_add_channel_settings_to_campaign'),
    ]

    operations = [
        migrations.CreateModel(
            name='DeliveryChannelConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel', models.CharField(choices=[('email', 'Email'), ('sms', 'SMS'), ('push', 'Push Notification'), ('in_app', 'In-App')], max_length=20, unique=True)),
                ('is_enabled', models.BooleanField(default=True)),
                ('delivery_mode', models.CharField(choices=[('kafka', 'Kafka Topics'), ('api', 'Direct API Calls')], default='api', max_length=20)),
                ('kafka_topic', models.CharField(blank=True, help_text='Kafka topic name for this channel', max_length=255)),
                ('kafka_brokers', models.JSONField(blank=True, default=list, help_text='List of Kafka broker URLs')),
                ('kafka_config', models.JSONField(blank=True, default=dict, help_text='Additional Kafka producer config')),
                ('api_endpoint', models.URLField(blank=True, help_text='API endpoint URL for direct calls')),
                ('api_method', models.CharField(choices=[('POST', 'POST'), ('PUT', 'PUT'), ('PATCH', 'PATCH')], default='POST', max_length=10)),
                ('api_headers', models.JSONField(blank=True, default=dict, help_text='HTTP headers (e.g., Authorization)')),
                ('api_auth_type', models.CharField(blank=True, choices=[('none', 'None'), ('bearer', 'Bearer Token'), ('basic', 'Basic Auth'), ('api_key', 'API Key')], max_length=20)),
                ('api_auth_config', models.JSONField(blank=True, default=dict, help_text='Auth credentials (stored encrypted in production)')),
                ('channel_settings', models.JSONField(blank=True, default=dict, help_text='Channel-specific configuration (templates, defaults, etc.)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.CharField(blank=True, max_length=100)),
            ],
            options={
                'verbose_name': 'Delivery Channel Configuration',
                'verbose_name_plural': 'Delivery Channel Configurations',
                'ordering': ['channel'],
            },
        ),
    ]

