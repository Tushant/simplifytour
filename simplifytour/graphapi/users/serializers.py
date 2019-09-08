from djoser.serializers import UidAndTokenSerializer, PasswordRetypeSerializer
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from rest_framework import serializers
from djoser import utils


User = get_user_model()


class UidAndDerivedTokenSerializer(UidAndTokenSerializer):

    def validate_uid(self, value):
        try:
            uid = utils.decode_uid(value)
            self.user = User.objects.get(pk=uid)
        except (
                User.DoesNotExist,
                ValueError,
                TypeError,
                OverflowError
        ) as error:
            raise serializers.ValidationError(
                self.error_messages['invalid_uid'])
        return value

    def validate(self, attrs):
        self.validate_uid(attrs['uid'])
        if not default_token_generator.check_token(self.user, attrs['token']):
            raise serializers.ValidationError(
                self.error_messages['invalid_token'])
        return attrs


class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'is_active', 'is_confirmed', 'password',)

    def create(self, validated_data):
        print('###################', validated_data)
        user = User.objects.create(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


class PasswordResetConfirmRetypeSerializer(UidAndDerivedTokenSerializer, PasswordRetypeSerializer):
    def validate(self, attrs):
        attrs = super(PasswordResetConfirmRetypeSerializer, self)\
            .validate(attrs)
        if attrs['new_password'] != attrs['re_new_password']:
            raise serializers.ValidationError(
                self.error_messages['password_mismatch'])
        return attrs


