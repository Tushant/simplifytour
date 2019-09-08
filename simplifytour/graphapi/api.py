import graphene

from simplifytour.graphapi.users.schema import UserMutations, UserQueries


class Query(UserQueries):
    node = graphene.Node.Field()


class Mutations(UserMutations):
    pass


schema = graphene.Schema(Query, Mutations)
