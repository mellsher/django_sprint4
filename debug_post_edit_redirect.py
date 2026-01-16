import sys, pathlib, os
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blogicum.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
from django.test import Client
from blog.models import Post, Category, Location
from django.utils import timezone

User = get_user_model()
# create user and post
u = User.objects.create_user(username='ptest', password='pwd', email='p@test')
cat = Category.objects.filter(is_published=True).first() or Category.objects.create(title='c', description='d', slug='c')
loc = Location.objects.filter(is_published=True).first() or Location.objects.create(name='L')
post = Post.objects.create(title='t', text='x', pub_date=timezone.now(), author=u, location=loc, category=cat, is_published=True)

unlogged = Client()
# attempt to post edit as anonymous
resp = unlogged.post(f'/posts/{post.id}/edit/', data={'title':'new','text':'x','pub_date':timezone.now().strftime('%Y-%m-%dT%H:%M'),'location':loc.id,'category':cat.id,'is_published':True}, follow=True)
print('status', resp.status_code)
print('redirect_chain', resp.redirect_chain)
print('final_url', getattr(resp, 'request', {}).get('PATH_INFO'))
print(resp.content.decode()[:500])
