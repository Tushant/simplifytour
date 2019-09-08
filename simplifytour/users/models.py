from django.contrib.auth.models import AbstractUser, BaseUserManager
from phonenumber_field.modelfields import PhoneNumberField
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **kwargs):
        '''
        creates and saves user in database
        :param email:
        :param password:
        :param kwargs:
        :return: user
        '''
        if not email:
            raise ValueError(_('Users must have an email address'))
        user = self.model(email=self.normalize_email(email), **kwargs)
        user.set_password(password)
        '''
         This is simply there to optionally override it in case you have e.g. multiple databases and you want your
         manger/queryset to operate on a specific one.
        '''
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **kwargs):
        user = self.create_user(email, password=password, **kwargs)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractUser):
    username = None
    email = models.EmailField(_('Email Address'), unique=True)
    is_confirmed = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        db_table = 'auth_user'

    def __str__(self):
        return self.email

    # def has_perm(self, perm, obj=None):
    #     "Does the user have a specific permission?"
    #     # Simplest possible answer: Yes, always
    #     return True
    #
    # def has_module_perms(self, app_label):
    #     "Does the user have permissions to view the app `app_label`?"
    #     # Simplest possible answer: Yes, always
    #     return True
    #
    # @property
    # def is_staff(self):
    #     "Is the user a member of staff?"
    #     # Simplest possible answer: All admins are staff
    #     return self.is_staff


class Profile(models.Model):
    '''
    Profile table common to all kinds of users
    '''
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=100, blank=True, null=True)
    avatar = models.ImageField(blank=True, null=True, upload_to="avatar/")
    age = models.PositiveSmallIntegerField(blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=100, blank=True, null=True)
    phone_number = PhoneNumberField(blank=True, null=True)
    zip_code = models.PositiveIntegerField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def __str__(self):
        return f"{self.user.__str__()}"


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()


'''
AbstractUser is a full User model, complete with fields, as an abstract class so that you can inherit from it and add
your own profile fields and methods. AbstractBaseUser only contains the authentication functionality, but no actual
fields: you have to supply them when you subclass.
'''

'''
There are two ways to extend the default User model without substituting your own model. If the changes you need are purely
behavioral, and don’t require any change to what is stored in the database, you can create a proxy model based on User.
This allows for any of the features offered by proxy models including default ordering, custom managers, or custom model methods.

If you wish to store information related to User, you can use a OneToOneField to a model containing the fields for additional
information. This one-to-one model is often called a profile model, as it might store non-auth related information about a site user. 
'''
