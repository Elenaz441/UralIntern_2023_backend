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


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'password2', 'first_name', 'last_name')
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
            last_name=validated_data['last_name']
        )

        user.set_password(validated_data['password'])
        user.save()

        return user


class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField()
    surname = serializers.CharField()
    firstname = serializers.CharField()
    patronymic = serializers.CharField(allow_null=True)
    role_director = serializers.BooleanField()
    role_tutor = serializers.BooleanField()
    role_intern = serializers.BooleanField()
    educational_institution = serializers.CharField(allow_null=True)
    specialization = serializers.CharField(allow_null=True)
    academic_degree = serializers.CharField(allow_null=True)
    course = serializers.CharField(allow_null=True)
                                   # validators=[MinValueValidator(1), MaxValueValidator(6)])
    telephone = serializers.CharField(allow_null=True, validators=[RegexValidator(regex=r"^\+?1?\d{8,15}$")])
    telegram = serializers.URLField(allow_null=True)
    vk = serializers.URLField(allow_null=True)
    image = serializers.ImageField(allow_null=True)


class UserSerializerUpdate(serializers.Serializer):
    educational_institution = serializers.CharField(allow_null=True)
    specialization = serializers.CharField(allow_null=True)
    academic_degree = serializers.CharField(allow_null=True)
    course = serializers.IntegerField(allow_null=True)
                                      # validators=[MinValueValidator(1), MaxValueValidator(6)])
    telephone = serializers.CharField(allow_null=True, validators=[RegexValidator(regex=r"^\+?1?\d{8,15}$")])
    telegram = serializers.URLField(allow_null=True)
    vk = serializers.URLField(allow_null=True)

    def update(self, instance, validated_data):
        instance.educational_institution = validated_data.get('educational_institution', instance.educational_institution)
        instance.specialization = validated_data.get('specialization', instance.specialization)
        instance.academic_degree = validated_data.get('academic_degree', instance.academic_degree)
        instance.course = validated_data.get('course', instance.course)
        instance.telephone = validated_data.get('telephone', instance.telephone)
        instance.telegram = validated_data.get('telegram', instance.telegram)
        instance.vk = validated_data.get('vk', instance.vk)
        instance.save()
        return instance


class InternsSerializer(serializers.Serializer):
    id = UserSerializer()


class TutorSerializer(serializers.Serializer):
    id = UserSerializer()


class DirectorSerializer(serializers.Serializer):
    id = UserSerializer()


class EvaluationCriteriaSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField()


class StageSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    id_team = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    evaluation_criteria = EvaluationCriteriaSerializer(many=True)
    status = serializers.CharField()


class ProjectSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    id_event = serializers.CharField()
    title = serializers.CharField()
    id_director = DirectorSerializer()
    start_date = serializers.DateField()
    end_date = serializers.DateField()


class TeamSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    id_project = ProjectSerializer()
    title = serializers.CharField()
    id_tutor = TutorSerializer()
    # interns = InternsSerializer(many=True)
    team_chat = serializers.URLField(allow_null=True)


class ReportSerializer(serializers.Serializer):
    id_appraiser = serializers.CharField()
    id_stage = serializers.CharField()
    id_evaluation_criteria = serializers.CharField()
    id_intern = serializers.CharField()
    time_voting = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    estimation = serializers.FloatField(allow_null=True, validators=[MinValueValidator(-1), MaxValueValidator(3)])


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
        fields = ('id_appraiser',
                  'id_stage',
                  'id_evaluation_criteria',
                  'id_intern',
                  'time_voting',
                  'estimation',)