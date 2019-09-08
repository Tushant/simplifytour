import graphene

from graphene_django.filter.fields import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType
from graphql_jwt.decorators import login_required

from simplifytour.users.models import User, Profile


class UserQuery(DjangoObjectType):
    class Meta: # pylint: disable=too-few-public-methods
        model = User
        filter_fields = {
            'email': ['exact', ]
        }
        exclude_fields = ('password', 'is_superuser', )
        interfaces = (graphene.relay.Node, )


class ProfileQuery(DjangoObjectType):
    class Meta: # pylint: disable=too-few-public-methods
        model = Profile
        filter_fields = {
            'username': ['exact', ]
        }
        interfaces = (graphene.relay.Node, )


class Queries(graphene.ObjectType):
    users = DjangoFilterConnectionField(UserQuery)
    user = graphene.Field(UserQuery)

    profile = graphene.Field(ProfileQuery)

    @staticmethod
    @login_required
    def resolve_user(info):
        return info.context.user

    @staticmethod
    @login_required
    def resolve_profile(info):
        return Profile.objects.get(user=info.context.user)