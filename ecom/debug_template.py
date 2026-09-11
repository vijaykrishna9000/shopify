import os
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecom.settings')

try:
    import django
    django.setup()
    from django.test import Client

    c = Client()
    response = c.get('/')
    print('STATUS', response.status_code)
    print('TEMPLATES', [t.name for t in response.templates])
    if response.status_code != 200:
        print('CONTENT PREVIEW')
        print(response.content.decode('utf-8', errors='ignore')[:2000])
except Exception:
    traceback.print_exc()
