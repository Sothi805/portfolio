from django.db import migrations


TEMPLATES = [
    {
        'name': 'Developer Pro',
        'slug': 'developer',
        'description': 'A sleek dark terminal-style portfolio for developers and engineers.',
    },
    {
        'name': 'Minimalist',
        'slug': 'minimalist',
        'description': 'A clean, minimal layout that puts your work front and center.',
    },
    {
        'name': 'Creative Studio',
        'slug': 'creative',
        'description': 'A bold, expressive template for designers and creative professionals.',
    },
    {
        'name': 'Executive',
        'slug': 'executive',
        'description': 'A polished professional template for executives and researchers.',
    },
]


def seed_templates(apps, schema_editor):
    Template = apps.get_model('portfolios', 'Template')
    for data in TEMPLATES:
        Template.objects.get_or_create(slug=data['slug'], defaults=data)


def remove_templates(apps, schema_editor):
    Template = apps.get_model('portfolios', 'Template')
    Template.objects.filter(slug__in=[t['slug'] for t in TEMPLATES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('portfolios', '0003_add_education_experience'),
    ]

    operations = [
        migrations.RunPython(seed_templates, remove_templates),
    ]
