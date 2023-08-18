"""
URL configuration for server project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from server import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path('ping', views.ping, name='ping'),
    path('get_longterm_memory/<str:agent_id>', views.get_longterm_memory,
         name='get_longterm_memory'),
    path('update_longterm_memory/<str:agent_id>', views.update_longterm_memory,
         name='update_longterm_memory'),
    path('update_agent/<str:agent_id>',
         views.update_agent, name='update_agent'),
    path('get_agent/',
         views.get_agent, name='get_agent'),
    path('save_knowledge/<str:collection_name>',
         views.save_knowledge, name='save_knowledge'),
    path('search_commands/<str:collection_name>',
         views.search_commands, name='search_commands'),
    path('search_knowledge/<str:collection_name>',
         views.search_knowledge, name='search_knowledge'),
    path('get_recent_knowledge/<str:collection_name>',
         views.get_recent_knowledge, name='get_recent_knowledge'),
    path('search_kg/<str:collection_name>',
         views.search_kg, name='search_kg'),
    path('register_agent',
         views.register_agent, name='register_agent'),
    path('all_agents',
         views.all_agents, name='all_agents'),
    path('remove_knowledge',
         views.remove_knowledge, name='remove_knowledge'),
    path('remove_agent',
         views.remove_agent, name='remove_agent'),
    path('agent_exists/<str:agent_id>',
         views.agent_exists, name='agent_exists')
]
