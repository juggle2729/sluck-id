from django.conf.urls import patterns, include, url


urlpatterns = patterns(
    '',
    url(r'^api/v1/', include('luckyapi.urls')),
    url(r'^api/v2/', include('luckyapi.urls_v2')),
    url(r'^admin/', include('luckyadmin.urls')),
)
