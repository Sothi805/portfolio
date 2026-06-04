import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='forumreply',
            name='parent',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='child_replies',
                to='forum.forumreply',
            ),
        ),
    ]
