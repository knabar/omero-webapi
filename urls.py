from django.conf.urls.defaults import *

import views

urlpatterns = patterns('',
    url( r'^mpu/(?P<objectname>.+)$', views.MultiPartUpload.as_view(), name="webapi_mpu" ),
    url( r'^mpu_cleanup/$', views.clean_incomplete_mpus, name='webapi_mpu_cleanup' ),
)
