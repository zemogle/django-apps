from django.conf.urls import url
from django.conf import settings

from . import views

urlpatterns = [
    url(r'^$', views.ActivityListView.as_view(), name='list'),
    url(r'^feed/$', views.ActivityFeed(), name='feed'),
    url(r'^(?P<code>\d{4})/$', views.detail_by_code),
    url(r'^(?P<code>\d{4})/print-preview/$', views.ActivityDetailPrintView.as_view(), name='print-preview'),

    # for PDF generator I need first page separated from other pages
    url(r'^(?P<code>\d{4})/first-page-print-preview/$', views.ActivityDetailFirstPagePrintView.as_view(), name='print-preview-header'),
    url(r'^(?P<code>\d{4})/content-print-preview/$', views.ActivityDetailContentPrintView.as_view(), name='print-preview-content'),

    # url(r'^(?P<code>\d{4})/print/$', views.activity_pdf, name='print'),
    url(r'^(?P<code>\d{4})/(?P<slug>.+)?/$', views.ActivityDetailView.as_view(), name='detail'),
    url(r'^(?P<slug>.+)?/$', views.ActivityDetailBySlug.as_view()),  # old style astroEDU URL
]

if settings.SHORT_NAME == 'spaceawe':
    urlpatterns += [
        url(r'^category/(?P<category>\w+)/$', views.ActivityListView.as_view(), name='list_by_category'),
        #url(r'^level/(?P<level>\w+)/$', views.ActivityListView.as_view(), name='list_by_level'),
        url(r'^category/(?P<category>\w+)/level/(?P<level>\w+)/$', views.ActivityListView.as_view(), name='list_combine'),
    ]
