import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blogicum.settings')
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import django
django.setup()
from django.test import Client
from django.contrib.auth import get_user_model
User = get_user_model()

# create user
u = User.objects.create_user(username='dbguser', password='pass', email='dbg@example.com', first_name='Dbg', last_name='User')
client = Client()
client.force_login(u)
resp = client.get('/profile/edit/')
print('status:', resp.status_code)
print('context keys:', list(resp.context.keys()) if resp.context else None)
if resp.context:
    for k,v in resp.context.items():
        print(k, type(v))
print(resp.content.decode('utf-8')[:1000])
