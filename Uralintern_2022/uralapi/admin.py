from django.contrib import admin

from .forms import *
from .models import *
from .functions import generate_password
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin
from import_export.admin import ImportExportActionModelAdmin
from import_export import resources

# admin.site.unregister(Group)
# Group._meta.db_table = 'Role'


class UserResource(resources.ModelResource):
    class Meta:
        # TODO refactor import-export
        model = User
        fields = ('id', 'surname', 'firstname', 'patronymic', 'email', 'unhashed_password', 'role_director', 'role_tutor', 'role_intern')

    def before_save_instance(self, instance, using_transactions, dry_run):
        if not instance.unhashed_password:
            instance.set_password(generate_password())
        else:
            instance.set_password(instance.unhashed_password)
        instance.save()
        return instance


@admin.register(User)
class UserAdmin(UserAdmin, ImportExportActionModelAdmin):
    add_form = MyUserCreationForm
    form = CustomUserChangeForm
    resource_class = UserResource
    model = User
    fieldsets = (
        (None, {'fields': ('email', 'last_name', 'first_name', 'patronymic', 'groups', 'password')}),
        (('Права'), {
            'fields': ('is_active', 'is_superuser', 'is_staff'),
        }),
        (('Фото'), {
            'fields': ('image',)
        })
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'last_name', 'first_name', 'patronymic', 'groups', 'password1', 'password2', 'is_random_password'),
        }),
    )

    list_display = ('id', 'last_name', 'first_name', 'patronymic', 'email')
    list_display_links = ('id', 'last_name')
    search_fields = ('last_name', 'first_name', 'patronymic')
    list_filter = ('groups', )


@admin.register(UserInfo)
class UserInfoAdmin(admin.ModelAdmin):
    list_display = ('id_user', )
    search_fields = ('last_name', 'first_name', 'patronymic')

    fieldsets = (
        (('Образование'), {
            'fields': ('educational_institution', 'specialization', 'academic_degree', 'course'),
        }),
        (('Контакты'), {
            'fields': ('telephone', 'telegram', 'vk')
        })
    )


# @admin.register(Group)
# class GroupAdmin(admin.ModelAdmin):
#     list_display = ('name', )


@admin.register(EventUts)
class EventUtsAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date')
    search_fields = ('title', )
    list_filter = ('start_date', 'end_date')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'id_event', 'id_director', 'start_date', 'end_date')
    search_fields = ('title',)
    list_filter = ('id_event', 'id_director', 'start_date', 'end_date')

    def render_change_form(self, request, context, *args, **kwargs):
        context['adminform'].form.fields['id_director'].queryset = User.objects.filter(groups__in=[Group.objects.get(name='руководитель').id])
        return super(ProjectAdmin, self).render_change_form(request, context, *args, **kwargs)


class TeamResource(resources.ModelResource):

    class Meta:
        model = Team
        fields = ('id', 'id_project', 'title', 'id_tutor', 'interns')
        widgets = {'interns': {'field': 'id'}}


@admin.register(Team)
class TeamAdmin(ImportExportActionModelAdmin):
    resource_class = TeamResource
    list_display = ('title', 'id_project', 'id_tutor')
    search_fields = ('title',)
    list_filter = ('id_project', 'id_tutor')

    def render_change_form(self, request, context, *args, **kwargs):
        context['adminform'].form.fields['id_tutor'].queryset = User.objects.filter(groups__in=[Group.objects.get(name='куратор').id])
        return super(TeamAdmin, self).render_change_form(request, context, *args, **kwargs)


@admin.register(InternTeam)
class InternTeamAdmin(admin.ModelAdmin):
    list_display = ('id_team', 'id_intern', 'role')
    search_fields = ('id_team', 'id_intern', 'role')
    list_filter = ('id_team', 'role')


@admin.register(RoleInTeam)
class RoleInTeamAdmin(admin.ModelAdmin):
    list_display = ('title', )


@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ('title', 'id_team', 'start_date', 'end_date')
    search_fields = ('title',)
    list_filter = ('id_team',)
    filter_horizontal = ['evaluation_criteria', ]


@admin.register(EvaluationCriteria)
class EvaluationCriteriaAdmin(admin.ModelAdmin):
    list_display = ('title', 'description')
    search_fields = ('title', 'description')
    list_filter = ('title',)


@admin.register(Estimation)
class EstimationAdmin(admin.ModelAdmin):
    list_display = ('id_appraiser', 'id_stage', 'id_evaluation_criteria', 'id_intern', 'time_voting', 'estimation')
    list_filter = ('time_voting', )
    # readonly_fields = ('id_appraiser', 'id_stage', 'id_evaluation_criteria', 'id_intern', 'time_voting', 'estimation')

    # def has_add_permission(self, request, obj=None):
    #     return False
    #
    # def has_change_permission(self, request, obj=None):
    #     return False
    #
    # def has_delete_permission(self, request, obj=None):
    #     return False
