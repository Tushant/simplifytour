from django.views.decorators.csrf import csrf_exempt
from graphql_jwt.decorators import jwt_cookie
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib import admin
from django.conf import settings

from simplifytour.core.file_upload.views import FileUploadGraphQLView
from simplifytour.graphapi.api import schema

urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql', jwt_cookie(csrf_exempt(FileUploadGraphQLView.as_view(schema=schema, graphiql=settings.DEBUG)))),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns

