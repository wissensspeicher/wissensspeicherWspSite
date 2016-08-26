from django.conf.urls import patterns, url
from django.views.generic import TemplateView

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()


urlpatterns = patterns('',
                       url('^search/', 'webpages.views.search', name='search'),
                       url('^impressum/', 'webpages.views.impressum', name='impressum'),
                       ('^$', 'webpages.views.hello_world'),
                       (r'^status/details', 'status.views.status_details'),
                       (r'^status/', 'status.views.status'),
                       (r'^robots\.txt$', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
                       )
