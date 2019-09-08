import graphene

from django.contrib.auth import get_user_model, authenticate, login
from django.core.exceptions import ValidationError
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_bytes
# from django.conf import settings
from graphql_jwt.decorators import login_required
from graphql_jwt.shortcuts import get_token
from graphql_jwt.utils import jwt_decode

from simplifytour.users.models import Profile
from .serializers import RegistrationSerializer, PasswordResetConfirmRetypeSerializer
from .utils import send_activation_email, send_reset_password_email
from .query import UserQuery, ProfileQuery
from .input import ProfileInput

User = get_user_model()


class Register(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        password_repeat = graphene.String(required=True)

    user = graphene.Field(UserQuery)
    token = graphene.String()
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @staticmethod
    def mutate(info, email, password, password_repeat):
        if password == password_repeat:
            try:
                serializer = RegistrationSerializer(data={'email': email, 'password': password, 'is_confirmed': False})
                print('#########Serializer########', serializer)
                if serializer.is_valid(raise_exception=True):
                    print('serializer is valid')
                    user = serializer.save()
                    print('###########User##########', user)
                    auth = authenticate(username=email, password=password)
                    login(info.context, auth)
                    print('###########get_token##########', get_token(auth))
                    context = {
                        'user': auth,
                        'request': info.context,
                        'email': email,
                        'token': get_token(auth)
                    }
                    send_activation_email(context)
                    return Register(success=True, user=user, token=get_token(auth))
                print('############serializer errors##########', serializer.errors)
                return Register(success=False, token=None, errors=[serializer.errors])
            except ValidationError as e:
                print("validation error", e)
                return Register(success=False, errors=[e])
        return Register(success=False, errors=['password', 'password is not matching'])


# Activate User
class Activate(graphene.Mutation):
    class Arguments:
        token = graphene.String(required=True)
        uid = graphene.String(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @staticmethod
    def mutate(info, token, uid):
        try:
            uid = force_bytes(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid)
        except(TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Activate(success=False, errors=['user', 'No such user found'])
        if user is not None and jwt_decode(token):
            user.is_confirmed = True
            user.save()
            login(info.context, user)
            return Activate(success=True)
        return Activate(success=False, errors=['user', 'User is invalid'])


# Forgot Password
class ResetPassword(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @staticmethod
    def mutate(info, email):
        try:
            user = User.objects.get(email=email)
            context = {
                'user': user,
                'request': info.context,
                'token': get_token(user)
            }
            send_reset_password_email(context)
        except User.DoesNotExist:
            return ResetPassword(success=False, errors=['email', 'User with that email does not exist'])


# ResetPasswordConfirm
class ResetPasswordConfirm(graphene.Mutation):
    class Arguments:
        uid = graphene.String(required=True)
        token = graphene.String(required=True)
        email = graphene.String(required=True)
        new_password = graphene.String(required=True)
        re_new_password = graphene.String(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @staticmethod
    def mutate(info, uid, token, email, new_password, re_new_password):
        print('###############################################')
        print(uid, token, email, new_password, re_new_password)
        serializer = PasswordResetConfirmRetypeSerializer(data={
            'uid': uid,
            'token': token,
            'email': email,
            'new_password': new_password,
            're_new_password': re_new_password,
        })
        if serializer.is_valid():
            serializer.user.set_password(serializer.data['new_password'])
            serializer.user.save()
            return ResetPasswordConfirm(success=True, errors=None)
        else:
            return ResetPasswordConfirm(
                success=False, errors=[serializer.errors])


class UpdateProfile(graphene.Mutation):
    class Arguments:
        input = ProfileInput()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    profile = graphene.Field(ProfileQuery)

    @staticmethod
    @login_required
    def mutate(info, input):
        avatar = info.context.FILES.get(input.pop('avatar', None))
        profile_instance = Profile.objects.get(user=info.context.user)
        for (key, value) in input.items():
            print('key', key, 'value', value)
            setattr(profile_instance, key, value)
            profile_instance.save()
        # profile_instance.update(**input)
        print("#############PROFILE INSTANCE#############", profile_instance)
        return UpdateProfile(success=True, profile=profile_instance)
