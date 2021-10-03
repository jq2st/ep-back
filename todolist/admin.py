from django.contrib import admin

from todolist.models import Task, TasksTag, User

admin.site.register(User)
admin.site.register(Task)
admin.site.register(TasksTag)
