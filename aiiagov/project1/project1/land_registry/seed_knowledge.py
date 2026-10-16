import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'land_registry.settings')
django.setup()

from registry.models import KnowledgeCategory

categories = [
    {
        'name': 'Major Decisions',
        'description': 'Archives of board and executive decisions that shape organizational direction.',
        'icon': 'fas fa-gavel'
    },
    {
        'name': 'Operational Policies',
        'description': 'Internal rules and guidelines for day-to-day land registry operations.',
        'icon': 'fas fa-file-contract'
    },
    {
        'name': 'Legal Guidance',
        'description': 'Interpretations of land laws and judicial precedents relevant to our mandates.',
        'icon': 'fas fa-balance-scale'
    },
    {
        'name': 'Administrative Circulars',
        'description': 'Internal memos and directives issued to all staff.',
        'icon': 'fas fa-bullhorn'
    }
]

for cat_data in categories:
    cat, created = KnowledgeCategory.objects.get_or_create(name=cat_data['name'], defaults=cat_data)
    if created:
        print(f"Created category: {cat.name}")
    else:
        print(f"Category already exists: {cat.name}")
