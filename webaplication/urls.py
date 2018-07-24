from webaplication import views

from django.urls import path

urlpatterns = [
    path('', views.index),
    #path('index', views.index_view),
    path('search',views.search),

]
