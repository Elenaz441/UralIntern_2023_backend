from django.contrib import admin

from .forms import *
from .models import *
from django.contrib.auth.admin import UserAdmin, Group
from import_export import resources, fields, widgets
from import_export.admin import ImportExportActionModelAdmin
from django_rest_passwordreset.admin import ResetPasswordToken
from rest_framework_simplejwt.token_blacklist.admin import BlacklistedToken, OutstandingToken


admin.site.unregister(ResetPasswordToken)
admin.site.unregister(BlacklistedToken)
admin.site.unregister(OutstandingToken)
admin.site.unregister(Group)


@admin.register(MyGroup)
class MyGroupAdmin(admin.ModelAdmin):
    search_fields = ('name', )
    list_display = ('name', )
    filter_horizontal = ['permissions', ]


class UserResource(resources.ModelResource):
    class Meta:
        model = User
        fields = ('id', 'email', 'last_name', 'first_name', 'patronymic', 'password', 'groups')
        widgets = {'groups': {'field': 'name'}}

    def before_save_instance(self, instance, using_transactions, dry_run):
        if not instance.password:
            instance.set_password(generate_password())
        else:
            instance.set_password(instance.password)
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
    search_fields = ('last_name', 'first_name', 'patronymic', 'email')
    list_filter = ('groups', )


@admin.register(UserInfo)
class UserInfoAdmin(admin.ModelAdmin):
    list_display = ('id_user', )
    search_fields = ('id_user__last_name', 'id_user__first_name', 'id_user__patronymic')

    fieldsets = (
        (('Образование'), {
            'fields': ('educational_institution', 'specialization', 'academic_degree', 'course'),
        }),
        (('Контакты'), {
            'fields': ('telephone', 'telegram', 'vk')
        })
    )

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(EventUts)
class EventUtsAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date')
    search_fields = ('title', )
    list_filter = ('start_date', 'end_date')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'id_event', 'id_director', 'start_date', 'end_date')
    search_fields = ('title', 'id_event__title', 'id_director__last_name')
    list_filter = ('id_event', 'start_date', 'end_date')
    filter_horizontal = ['evaluation_criteria', ]

    def render_change_form(self, request, context, *args, **kwargs):
        context['adminform'].form.fields['id_director'].queryset = User.objects.filter(groups__in=[Group.objects.get(name='руководитель').id])
        return super(ProjectAdmin, self).render_change_form(request, context, *args, **kwargs)


class TeamResource(resources.ModelResource):

    class Meta:
        model = Team
        fields = ('id', 'id_project', 'title', 'id_tutor', 'teg')
        widgets = {'id_project': {'field': 'title'}, 'id_tutor': {'field': 'last_name'}}


@admin.register(Team)
class TeamAdmin(ImportExportActionModelAdmin):
    resource_class = TeamResource
    list_display = ('title', 'id_project', 'id_tutor')
    search_fields = ('title', 'id_project__title', 'id_tutor__last_name', 'id_tutor__first_name')

    def render_change_form(self, request, context, *args, **kwargs):
        context['adminform'].form.fields['id_tutor'].queryset = User.objects.filter(groups__in=[Group.objects.get(name='куратор').id])
        return super(TeamAdmin, self).render_change_form(request, context, *args, **kwargs)


@admin.register(InternTeam)
class InternTeamAdmin(admin.ModelAdmin):
    list_display = ('id_team', 'id_intern', 'role')
    search_fields = ('id_team__title', 'id_intern__last_name', 'role__title')
    list_filter = ('role', )
    autocomplete_fields = ('id_intern',)

    def render_change_form(self, request, context, *args, **kwargs):
        context['adminform'].form.fields['id_intern'].queryset = User.objects.filter(groups__in=[Group.objects.get(name='стажёр').id])
        return super(InternTeamAdmin, self).render_change_form(request, context, *args, **kwargs)


@admin.register(RoleInTeam)
class RoleInTeamAdmin(admin.ModelAdmin):
    list_display = ('title', )


@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ('title', 'id_team', 'start_date', 'end_date')
    search_fields = ('title', 'id_team__title')
    list_filter = ('start_date', 'end_date')
    filter_horizontal = ['evaluation_criteria', ]


@admin.register(EvaluationCriteria)
class EvaluationCriteriaAdmin(admin.ModelAdmin):
    list_display = ('title', 'description')
    search_fields = ('title', 'description')


@admin.register(Estimation)
class EstimationAdmin(admin.ModelAdmin):
    list_display = ('id_appraiser', 'id_stage', 'id_evaluation_criteria', 'id_intern', 'time_voting', 'estimation')
    list_filter = ('time_voting', 'id_evaluation_criteria',)
    search_fields = ('id_appraiser__last_name', 'id_appraiser__first_name', 'id_stage__title', 'id_intern__last_name', 'id_intern__first_name')
    readonly_fields = ('id_appraiser', 'id_stage', 'id_evaluation_criteria', 'id_intern', 'time_voting', 'estimation')

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    # def has_delete_permission(self, request, obj=None):
    #     return False
