import graphene
import graphql_jwt

from graphapi.users.schema import UserSchema
from graphapi.users import mutation as user_mutation


class Queries(UserSchema, graphene.ObjectType):
    pass


class Mutations(graphene.ObjectType):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    register = user_mutation.Register.Field()
    reset_password = user_mutation.ForgotPassword.Field()
    reset_password_confirmation = user_mutation.ResetPasswordConfirm.Field()
    profile = user_mutation.UpdateProfile.Field()


schema = graphene.Schema(query=Queries, mutation=Mutations)
