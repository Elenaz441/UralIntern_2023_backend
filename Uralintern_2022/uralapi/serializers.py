from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password
from .models import *
import datetime


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        us = UserSerializer(user)

        # Add custom claims
        token["groups"] = us.data["groups"]
        # token['email'] = user.email
        # ...

        return token


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True, validators=[UniqueValidator(queryset=User.objects.all())])
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    groups = serializers.StringRelatedField(many=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'password2', 'first_name', 'last_name', 'patronymic', 'image', 'groups')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            patronymic=validated_data['patronymic']
        )
        user.groups.set([Group.objects.get(name='стажёр')])
        user.set_password(validated_data['password'])
        user.save()

        return user


class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInfo
        fields = '__all__'


class InternTeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = InternTeam
        fields = '__all__'


class EvaluationCriteriaSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    description_minus_one = serializers.CharField()
    description_zero = serializers.CharField()
    description_one = serializers.CharField()
    description_two = serializers.CharField()
    description_three = serializers.CharField()


class StageSerializer(serializers.ModelSerializer):
    evaluation_criteria = EvaluationCriteriaSerializer(many=True)
    def create(self, validated_data):
        evaluation_criteria = validated_data.pop('evaluation_criteria')
        stage = Stage.objects.create(**validated_data)
        list_criteria = []
        for criteria in evaluation_criteria:
            list_criteria.append(criteria['id'])
        stage.evaluation_criteria.set(EvaluationCriteria.objects.filter(pk__in=list_criteria))
        stage.save()
        return stage

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.start_date = validated_data.get('start_date', instance.start_date)
        instance.end_date = validated_data.get('end_date', instance.end_date)
        instance.end_estimation_date = validated_data.get('end_estimation_date', instance.end_estimation_date)
        list_criteria = []
        for criteria in validated_data['evaluation_criteria']:
            list_criteria.append(criteria['id'])
        instance.evaluation_criteria.set(EvaluationCriteria.objects.filter(pk__in=list_criteria))
        instance.save()
        return instance

    class Meta:
        model = Stage
        fields = '__all__'


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'


class TeamSerializer(serializers.ModelSerializer):
    id_project = serializers.PrimaryKeyRelatedField(queryset = Project.objects.all())
    id_tutor = serializers.PrimaryKeyRelatedField(queryset = User.objects.all())
    interns = serializers.SerializerMethodField('get_interns')

    @staticmethod
    def get_interns(team):
        return InternTeamSerializer(InternTeam.objects.filter(id_team=team.id), many=True).data

    def create(self, validated_data):
        team =  Team.objects.create(id_project=validated_data['id_project'],
                                    title=validated_data['title'],
                                    id_tutor=validated_data['id_tutor'],
                                    team_chat=validated_data['team_chat'],
                                    teg=validated_data['teg'],)
        role = RoleInTeam.objects.filter(title='нет роли').first()
        for intern in self.initial_data['interns']:
            InternTeam.objects.create(id_team=team, id_intern=User.objects.get(pk=intern['id_intern']), role=role)
        return team

    def update(self, instance, validated_data):
        instance.id_project = Project.objects.get(pk=self.initial_data['id_project'])
        instance.title = validated_data.get('title', instance.title)
        instance.id_tutor = User.objects.get(pk=self.initial_data['id_tutor'])
        instance.team_chat = validated_data.get('team_chat', instance.team_chat)
        instance.teg = validated_data.get('teg', instance.teg)
        instance.save()
        role = RoleInTeam.objects.filter(title='нет роли').first()
        for intern in self.initial_data['interns']:
            if not InternTeam.objects.filter(id_team=instance, id_intern=User.objects.get(pk=intern['id_intern'])).exists():
                InternTeam.objects.create(id_team=instance, id_intern=User.objects.get(pk=intern['id_intern']), role=role)
        for intern in InternTeam.objects.filter(id_team=instance):
            if intern.id_intern.id not in [a_dict['id_intern'] for a_dict in self.initial_data['interns']]:
                intern.delete()
        return instance

    class Meta:
        model = Team
        fields = '__all__'


class EstimationSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        return Estimation.objects.create(**validated_data)

    def update(self, instance: Estimation, validated_data):
        # Далее, если в словаре есть такой ключ, перепишет данные в базе, либо оствит то, что было
        instance.estimation = validated_data.get('estimation', instance.estimation)
        instance.time_voting = datetime.datetime.now()
        instance.save()
        return instance

    class Meta:
        model = Estimation
        fields = '__all__'


class RoleInTeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleInTeam
        fields = '__all__'