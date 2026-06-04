from django.db import migrations


CATEGORIES = [
    {
        'name': 'General Discussion',
        'slug': 'general',
        'description': 'Talk about anything related to portfolios and professional growth.',
        'icon': 'forum',
    },
    {
        'name': 'Career Advice',
        'slug': 'career-advice',
        'description': 'Share tips, ask questions, and get guidance on career development.',
        'icon': 'work',
    },
    {
        'name': 'Design',
        'slug': 'design',
        'description': 'Discuss UI/UX, visual design, branding, and creative direction.',
        'icon': 'design_services',
    },
    {
        'name': 'Development',
        'slug': 'development',
        'description': 'All things code — web, mobile, backend, tools, and more.',
        'icon': 'code',
    },
    {
        'name': 'Showcase',
        'slug': 'showcase',
        'description': 'Share your portfolio or project and get community feedback.',
        'icon': 'star',
    },
]


def seed_categories(apps, schema_editor):
    ForumCategory = apps.get_model('forum', 'ForumCategory')
    for data in CATEGORIES:
        ForumCategory.objects.get_or_create(slug=data['slug'], defaults=data)


def remove_categories(apps, schema_editor):
    ForumCategory = apps.get_model('forum', 'ForumCategory')
    ForumCategory.objects.filter(slug__in=[c['slug'] for c in CATEGORIES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0003_forumreply_parent'),
    ]

    operations = [
        migrations.RunPython(seed_categories, remove_categories),
    ]
