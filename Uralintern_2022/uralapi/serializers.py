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

        # Add custom claims
        token['email'] = user.email
        # ...

        return token


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True, validators=[UniqueValidator(queryset=User.objects.all())])
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    groups = serializers.StringRelatedField(many=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'password2', 'first_name', 'last_name', 'patronymic', 'image', 'groups')
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


class EvaluationCriteriaSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField()


class StageSerializer(serializers.ModelSerializer):
    evaluation_criteria = EvaluationCriteriaSerializer(many=True)

    class Meta:
        model = Stage
        fields = '__all__'


# class ProjectSerializer(serializers.Serializer):
#     id = serializers.IntegerField(read_only=True)
#     id_event = serializers.CharField()
#     title = serializers.CharField()
#     id_director = serializers.CharField()
#     start_date = serializers.DateField()
#     end_date = serializers.DateField()


class InternTeamSerializer(serializers.Serializer):
    id_team = serializers.CharField()
    id_intern = UserSerializer()
    role = serializers.CharField()


class TeamSerializer(serializers.ModelSerializer):
    id_project = serializers.StringRelatedField()
    id_tutor = serializers.StringRelatedField()

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