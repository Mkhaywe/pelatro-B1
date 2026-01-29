# Generated manually to add channel_settings field to Campaign model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loyalty', '0003_add_journey_structure_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaign',
            name='channel_settings',
            field=models.JSONField(blank=True, default=dict, help_text='Channel-specific configuration (email subject, SMS template, push title, etc.)'),
        ),
    ]

