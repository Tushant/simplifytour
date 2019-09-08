import graphene

from simplifytour.core.file_upload import types


class ProfileInput(graphene.InputObjectType):
    username = graphene.String(description="display name")
    avatar = types.Upload(description='avatar')
    age = graphene.Int(description='Age')
    phone_number = graphene.String(description="Phone Number")
    country = graphene.String(description="Country")
    city = graphene.String(description='City')
    address = graphene.String(description='Address')
    zip_code = graphene.Int(description='Zip Code')
    slogan = graphene.String(description='Slogan')
    bio = graphene.String(description='Bio')
