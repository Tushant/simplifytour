# from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.core.mail import EmailMessage
# from django.utils import six


# class TokenGenerator(PasswordResetTokenGenerator):
#     def _make_hash_value(self, user, timestamp):
#         return (
#             six.text_type(user.pk) + six.text_type(timestamp) +
#             six.text_type(user.is_active)
#         )
#
#
# account_activation_token = TokenGenerator()


# def send_activation_email(context):
#     user = context.user
#     current_site = get_current_site(context.request)
#     mail_subject = 'Activate your account.'
#     message = render_to_string('email/activation.html', {
#         'user': user,
#         'domain': current_site.domain,
#         'uid': urlsafe_base64_encode(force_bytes(user.pk)),
#         'token': context.token,
#     })
#     email = EmailMessage(
#         mail_subject, message, to=[context.email]
#     )
#     email.send()
#
#
# def send_reset_password_email(context):
#     user = context.user
#     current_site = get_current_site(context.request)
#     mail_subject = 'Reset your password'
#     message = render_to_string('email/password_reset.html', {
#         'user': user,
#         'domain': current_site.domain,
#         'uid': urlsafe_base64_encode(force_bytes(user.pk)),
#         'token': context.token,
#     })
#     email = EmailMessage(
#         mail_subject, message, to=[context.email]
#     )
#     email.send()

from djoser.compat import get_user_email
from djoser.email import ActivationEmail, PasswordResetEmail


def send_activation_email(context):
    print("######## send_activation_email user ##############", context.user)
    to = [get_user_email(context.user)]
    ActivationEmail(context.request, {'user': context.user}).send(to)


def send_reset_password_email(context):
    user = context['user']
    to = [get_user_email(user)]
    PasswordResetEmail(context['request'], {'user': user}).send(to)
