from django.contrib.auth.password_validation import validate_password
from django.core.validators import MaxLengthValidator
from django.db import IntegrityError, transaction
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.utils import get_md5_hash_password

from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=1024)
    password_confirm = serializers.CharField(
        write_only=True, trim_whitespace=False, max_length=1024
    )

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'password',
            'password_confirm',
            'phone',
            'address',
            'bio',
            'city',
            'language',
            'currency',
        )

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        candidate = User(
            **{
                key: value
                for key, value in attrs.items()
                if key not in ('password', 'password_confirm')
            }
        )
        validate_password(attrs['password'], user=candidate)
        return attrs

    def validate_email(self, value):
        normalized = User.objects.normalize_email(value).strip().lower()
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return normalized

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        try:
            with transaction.atomic():
                return User.objects.create_user(**validated_data)
        except IntegrityError:
            # Validation and insertion are separate operations. The database
            # arbitrates concurrent registrations; report the winning account
            # as an ordinary field error instead of returning a server error.
            if User.objects.filter(email__iexact=validated_data['email']).exists():
                raise serializers.ValidationError(
                    {
                        'email': 'A user with this email already exists.',
                    }
                ) from None
            if User.objects.filter(username=validated_data['username']).exists():
                raise serializers.ValidationError(
                    {
                        'username': 'A user with that username already exists.',
                    }
                ) from None
            raise


class UserProfileSerializer(serializers.ModelSerializer):
    social_identities = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'phone',
            'address',
            'bio',
            'city',
            'language',
            'currency',
            'loyalty_points',
            'is_staff',
            'date_joined',
            'social_identities',
        )
        read_only_fields = ('id', 'email', 'loyalty_points', 'is_staff', 'date_joined')

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        # A concurrent password or permission update must never be overwritten
        # by the account snapshot loaded when this profile request began.
        if validated_data:
            instance.save(update_fields=tuple(validated_data))
        return instance

    def get_social_identities(self, obj):
        return [
            {
                'provider': identity.provider,
                'email': identity.email,
                'email_verified': identity.email_verified,
            }
            for identity in obj.social_identities.all()
        ]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=1024)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=1024)
    new_password_confirm = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        max_length=1024,
    )

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': 'Passwords do not match.'})
        validate_password(attrs['new_password'], user=self.context['request'].user)
        return attrs

    @transaction.atomic
    def save(self, **kwargs):
        user = User.objects.select_for_update().get(pk=self.context['request'].user.pk)
        if not user.is_active or not user.check_password(self.validated_data['old_password']):
            raise serializers.ValidationError({'old_password': 'Current password is incorrect.'})
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[self.username_field].max_length = 254
        self.fields[self.username_field].validators.append(MaxLengthValidator(254))
        self.fields['password'].max_length = 1024
        self.fields['password'].trim_whitespace = False
        self.fields['password'].validators.append(MaxLengthValidator(1024))

    def validate(self, attrs):
        # Registration and OAuth already compare email identities without case.
        # Resolve the stored spelling so existing mixed-case admin accounts can
        # use the same login rule without rewriting their account data.
        stored_email = (
            User.objects.filter(
                email__iexact=attrs[self.username_field].strip(),
            )
            .values_list('email', flat=True)
            .first()
        )
        if stored_email is not None:
            attrs[self.username_field] = stored_email
        data = super().validate(attrs)
        data['user'] = UserProfileSerializer(self.user).data
        return data


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    refresh = serializers.CharField(max_length=16384, trim_whitespace=False)

    @transaction.atomic
    def validate(self, attrs):
        token = self.token_class(attrs['refresh'])
        user_id = token.get(api_settings.USER_ID_CLAIM)
        try:
            user = User.objects.select_for_update().get(**{api_settings.USER_ID_FIELD: user_id})
        except (User.DoesNotExist, ValueError, TypeError):
            raise AuthenticationFailed('This sign-in session is no longer available.') from None
        if not api_settings.USER_AUTHENTICATION_RULE(user) or token.get(
            api_settings.REVOKE_TOKEN_CLAIM
        ) != get_md5_hash_password(user.password):
            raise AuthenticationFailed('This sign-in session is no longer available.')
        # The parent revalidates the blacklist while the account is locked, so
        # concurrent refresh requests cannot both rotate the same credential.
        return super().validate(attrs)


class OAuthExchangeSerializer(serializers.Serializer):
    code = serializers.CharField(
        max_length=128,
        allow_blank=False,
        trim_whitespace=False,
    )
