from django.contrib.auth import get_user_model
from rest_framework import serializers

from app.role.models import Role


class SuperAdminUserCreateSerializer(serializers.ModelSerializer):
    """ Serializer: Create a new user """

    password = serializers.CharField(write_only=True)

    class Meta:
        model = get_user_model()
        fields = (
            'pk',
            'email',
            'first_name',
            'last_name',
            'password',
            'role'
        )

    def validate_email(self, value):
        # Custom email validation logic
        email = value.strip()
        if get_user_model().objects.filter(email=email,is_active=True).exists():
            raise serializers.ValidationError("Email already in use")
        return email

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = get_user_model().objects.create_user(password=password, **validated_data)
        return user

class UserCreateSerializer(serializers.ModelSerializer):
    """ Serializer: Create a new user """

    password = serializers.CharField(write_only=True)
    resume_file = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = get_user_model()
        fields = (
            'pk',
            'email',
            'first_name',
            'last_name',
            'password',
            'linkedin_url',
            'github_url',
            'resume_file',
            'role'
        )

    def validate_email(self, value):
        # Custom email validation logic
        email = value.strip()
        if get_user_model().objects.filter(email=email, is_active=True).exists():
            raise serializers.ValidationError("Email already in use")
        return email

    def validate_resume_file(self, value):
        if value:
            allowed_types = ['application/pdf',
                             'application/msword',
                             'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
            if value.content_type not in allowed_types:
                raise serializers.ValidationError("Resume must be a PDF or Word document.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = get_user_model().objects.create_user(password=password, **validated_data)
        return user

class RoleDisplaySerializer(serializers.ModelSerializer):
    """ Serializer: Display user details """

    class Meta:
        model = Role
        fields = ('pk', 'name')


class UserDisplaySerializer(serializers.ModelSerializer):
    """ Serializer: Display user details """
    role = RoleDisplaySerializer(read_only=True)

    class Meta:
        model = get_user_model()
        fields = (
            'pk',
            'email',
            'first_name',
            'last_name',
            'is_active',
            'role'
        )


class UserListFilterDisplaySerializer(serializers.ModelSerializer):
    """ Serializer: Display user details """

    class Meta:
        model = get_user_model()
        fields = (
            'pk',
            'email',
            'first_name',
            'last_name',
            'created',
            'is_active',
            'linkedin_url',
            'github_url'


        )


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = (
            'pk',
            'email',
            'first_name',
            'last_name',
            'role'
        )

    def validate_email(self, value):
        # Custom email validation logic
        email = value.strip()
        if get_user_model().objects.filter(email=email, is_active=True).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("Email already in use")
        return email
