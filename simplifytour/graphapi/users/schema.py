import graphene
import graphql_jwt

from simplifytour.graphapi.users.mutation import (
    Register, Activate, ResetPassword, ResetPasswordConfirm, UpdateProfile
)

from .query import Queries


class UserQueries(Queries):
    pass


class UserMutations(graphene.ObjectType):  # pylint: disable=too-few-public-methods
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    register = Register.Field()
    activate_user = Activate.Field()
    reset_password = ResetPassword.Field()
    reset_password_confirmation = ResetPasswordConfirm.Field()
    update_profile = UpdateProfile.Field()
