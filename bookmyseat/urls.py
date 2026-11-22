import sys
import traceback
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.http import HttpResponseServerError

def custom_500(request):
    exc_type, exc_value, exc_traceback = sys.exc_info()
    if exc_type is not None:
        tb = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    else:
        tb = "No exception info available."
    html = f"""<!doctype html>
    <html lang="en">
    <head>
      <title>500 Internal Server Error</title>
      <style>
        body {{ background: #0f172a; color: #f8fafc; font-family: monospace; padding: 30px; }}
        h1 {{ color: #ef4444; }}
        pre {{ background: #1e293b; padding: 20px; border-radius: 8px; border: 1px solid #334155; overflow-x: auto; color: #f1f5f9; }}
      </style>
    </head>
    <body>
      <h1>500 Internal Server Error</h1>
      <p>Diagnostic Traceback:</p>
      <pre>{tb}</pre>
    </body>
    </html>"""
    return HttpResponseServerError(html)

handler500 = custom_500

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('', include('users.urls')),
    path('movies/', include('movies.urls')),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
