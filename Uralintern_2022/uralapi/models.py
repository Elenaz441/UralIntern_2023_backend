import os

from django.db import models, connection
from django.contrib.auth.models import AbstractUser, Group
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.hashers import make_password
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from .functions import upload_to
from django.conf import settings
from django.core.mail import send_mail


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields) -> 'User':
        if email is None:
            raise TypeError('Users must have an email address.')
        user = self.model(email=self.normalize_email(email))
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields) -> 'User':
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        if password is None:
            raise TypeError('Superusers must have a password.')
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        user = self.create_user(email, password, **extra_fields)
        user.is_superuser = True
        user.is_staff = True
        user.save()
        return user


class User(AbstractUser):
    username = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(_('email address'), unique=True)
    patronymic = models.CharField(max_length=100, verbose_name='Отчество', null=True, blank=True)
    image = models.ImageField(upload_to=upload_to, null=True, blank=True, verbose_name='Фото')

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return f'{self.last_name} {self.first_name}'

    def save(self, *args, **kwargs):
        super(User, self).save(*args, **kwargs)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self._password = raw_password

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class UserInfo(models.Model):
    COURSES = (
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
        ('6', '6'),
        ('END', 'окончил')
    )
    id_user = models.OneToOneField(settings.AUTH_USER_MODEL, models.CASCADE, primary_key=True, verbose_name='Пользователь')
    educational_institution = models.CharField(max_length=200, null=True, blank=True, verbose_name='Университет')
    specialization = models.CharField(max_length=200, null=True, blank=True, verbose_name='Специальность')
    academic_degree = models.CharField(max_length=200, null=True, blank=True, verbose_name='Академическая степень')
    course = models.CharField(max_length=100, null=True, blank=True, verbose_name='Курс обучения', choices=COURSES)
    telephone = models.CharField(max_length=16, null=True, blank=True, verbose_name='Телефон', validators=[RegexValidator(regex=r"^\+?1?\d{8,15}$")])
    telegram = models.URLField(null=True, blank=True, verbose_name='Ссылка на телеграмм')
    vk = models.URLField(null=True, blank=True, verbose_name='Ссылка на VK')

    def __str__(self):
        return self.id_user.__str__()

    class Meta:
        verbose_name = 'Информация о пользователе'
        verbose_name_plural = 'Информация о пользователях'


class Estimation(models.Model):
    id_appraiser = models.ForeignKey(settings.AUTH_USER_MODEL, models.DO_NOTHING, verbose_name='Оценщик', related_name='appraiser')
    id_stage = models.ForeignKey('Stage', models.DO_NOTHING, verbose_name='Этап')
    id_evaluation_criteria = models.ForeignKey('EvaluationCriteria', models.DO_NOTHING, verbose_name='Критерий оценивания')
    id_intern = models.ForeignKey(settings.AUTH_USER_MODEL, models.DO_NOTHING, verbose_name='Стажёр', related_name='intern')
    time_voting = models.DateTimeField(verbose_name='Время голосования', auto_now=True)
    estimation = models.FloatField(verbose_name='Оценка', validators=[MinValueValidator(-1), MaxValueValidator(3)])

    class Meta:
        verbose_name = 'Собранная оценка'
        verbose_name_plural = 'Собранные оценки'
        unique_together = ('id_appraiser', 'id_stage', 'id_evaluation_criteria', 'id_intern')


class EvaluationCriteria(models.Model):
    title = models.CharField(max_length=100, verbose_name='Название критерия оценки')
    description = models.TextField(max_length=1000, verbose_name='Описание')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Критерий оценки'
        verbose_name_plural = 'Критерии оценки'


class EventUts(models.Model):
    title = models.CharField(max_length=100, verbose_name='Название мероприятия')
    start_date = models.DateField(null=True, blank=True, verbose_name='Дата начала')
    end_date = models.DateField(null=True, blank=True, verbose_name='Дата окончания')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Мероприятие'
        verbose_name_plural = 'Мероприятия'


class InternTeam(models.Model):
    id_team = models.ForeignKey('Team', models.CASCADE, verbose_name='Команда')
    id_intern = models.ForeignKey(User, models.CASCADE, verbose_name='Стажёр')
    role = models.ForeignKey('RoleInTeam', models.DO_NOTHING, verbose_name='Роль')

    class Meta:
        verbose_name = 'Стажёр_Команда'
        verbose_name_plural = 'Стажёры_Команды'
        unique_together = ('id_team', 'id_intern')


class RoleInTeam(models.Model):
    title = models.CharField(max_length=100, verbose_name='Название')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Роль в команде'
        verbose_name_plural = 'Роли в команде'


class Project(models.Model):
    id_event = models.ForeignKey(EventUts, models.CASCADE, verbose_name='Название мероприятия')
    title = models.CharField(max_length=100, verbose_name='Название проекта')
    id_director = models.ForeignKey(User, models.DO_NOTHING, verbose_name='Руководитель')
    evaluation_criteria = models.ManyToManyField(EvaluationCriteria, verbose_name='Критерии оценки', blank=True)
    start_date = models.DateField(null=True, blank=True, verbose_name='Дата начала')
    end_date = models.DateField(null=True, blank=True, verbose_name='Дата окончания')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'


class Stage(models.Model):
    id_team = models.ForeignKey('Team', models.CASCADE, verbose_name='Название команды')
    title = models.CharField(max_length=100, verbose_name='Название этапа')
    description = models.TextField(max_length=1000, verbose_name='Описание', null=True, blank=True)
    evaluation_criteria = models.ManyToManyField(EvaluationCriteria, verbose_name='Критерии оценки', blank=True)
    is_active = models.BooleanField(verbose_name='Активный этап', default=True)
    start_date = models.DateField(verbose_name='Дата начала', default='1970-01-01')
    end_date = models.DateField(verbose_name='Дата окончания', default='1970-01-01')
    end_estimation_date = models.DateField(verbose_name='Дата окончания оценки', default='1970-01-01')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Этап оценивания'
        verbose_name_plural = 'Этапы оценивания'


class Team(models.Model):
    id_project = models.ForeignKey(Project, models.CASCADE, verbose_name='Название проекта')
    title = models.CharField(max_length=200, verbose_name='Название команды')
    id_tutor = models.ForeignKey(settings.AUTH_USER_MODEL, models.DO_NOTHING, verbose_name='Куратор')
    team_chat = models.URLField(null=True, blank=True, verbose_name='Ссылка на чат')
    teg = models.CharField(max_length=200, unique=True, verbose_name='Тег')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Команда'
        verbose_name_plural = 'Команды'


@receiver(pre_save, sender=User)
def pre_save_user(sender, instance, *args, **kwargs):
    """ instance old image file will delete from os and send email"""
    ext = str(instance.image).split('.')[-1]
    old_img = os.path.join(settings.BASE_DIR, f'media/photos/user{instance.id}.{ext}')
    if os.path.exists(old_img) and str(instance.image) != f'photos/user{instance.id}.{ext}':
        os.remove(old_img)
    if (instance._password):
        send_mail(
            'Личный кабинет стажёра Uralintern',
            f"Привет! Вы были зарегестрированы или выши данные были изменены." \
            f"\nВот ваши логин и пароль для входа в личный кабинет для оценки по стажёрским компетециям." \
                          f"\nЛогин -  {instance.email}" \
                          f"\nПароль - {instance._password}" \
                          f"\nПожалуйста, сохраните данные для входа!" \
                          f"\nОценки можно давать через веб-приложение",
            settings.EMAIL_HOST_USER,
            [f'{instance.email}'],
        )


@receiver(post_save, sender=User)
def post_save_user(sender, instance, *args, **kwargs):
    if not UserInfo.objects.filter(id_user=instance).exists():
        UserInfo.objects.create(id_user=instance)
