"""Card URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from cardquery import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^login$',views.login),
    url(r'^$',views.oauth),
    url(r'^oauth',views.oauth),
    url(r'^api/index',views.api_index),
    url(r'^api/check$',views.api_check),
    url(r'^api/getNewData',views.api_getNewData),
    url(r'^api/getOneWeekData',views.api_getOneWeekData),
    url(r'^api/getOneMonthData',views.api_getOneMonthData),
    url(r'^addList1',views.addList1),
    url(r'^addList2',views.addList2),
    url(r'^addList3',views.addList3),


    # url(r'^index$',views.index),
    # url(r'^api/createCheck$',views.api_createCheck)
]
