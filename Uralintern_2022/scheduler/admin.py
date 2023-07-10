from django.contrib import admin
from .models import *


class SimpleView(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(Role)
class RoleAdmin(SimpleView):
    pass


@admin.register(Status)
class StatusAdmin(SimpleView):
    pass


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'parent_id', 'name', 'status_id', 'is_on_kanban')
    list_filter = ('project_id', )


@admin.register(Executor)
class ExecutorAdmin(admin.ModelAdmin):
    list_display = ('id', 'task_id', 'user_id')


@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ('id', 'task_id', 'description')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'task_id', 'user_id', 'message')

