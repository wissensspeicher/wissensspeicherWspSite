from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

#from wsp_site.views import hello_world, search

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'wsp_frontend.views.home', name='home'),
    # url(r'^wsp_frontend/', include('wsp_frontend.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)

urlpatterns = patterns('',
    ('^search/', 'webpages.views.search'),
    ('^$', 'webpages.views.hello_world')
)