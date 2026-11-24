import os
import sys
import traceback

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bookmyseat.settings")

try:
    from django.core.wsgi import get_wsgi_application
    _django_app = get_wsgi_application()

    def application(environ, start_response):
        try:
            return _django_app(environ, start_response)
        except Exception:
            err_tb = traceback.format_exc()
            status = '500 Internal Server Error'
            response_headers = [('Content-type', 'text/html; charset=utf-8')]
            start_response(status, response_headers)
            html = f"""<!doctype html>
            <html>
              <body style="font-family: monospace; background: #0f172a; color: #ef4444; padding: 25px;">
                <h2>Django Request Error on Vercel</h2>
                <pre style="color: #f8fafc; background: #1e293b; padding: 15px; border-radius: 6px; overflow-x: auto;">{err_tb}</pre>
              </body>
            </html>"""
            return [html.encode('utf-8')]

    app = application
except Exception:
    err_tb = traceback.format_exc()
    def error_app(environ, start_response):
        status = '500 Internal Server Error'
        response_headers = [('Content-type', 'text/html; charset=utf-8')]
        start_response(status, response_headers)
        html = f"""<!doctype html>
        <html>
          <body style="font-family: monospace; background: #0f172a; color: #ef4444; padding: 25px;">
            <h2>WSGI Startup Crash on Vercel</h2>
            <pre style="color: #f8fafc; background: #1e293b; padding: 15px; border-radius: 6px; overflow-x: auto;">{err_tb}</pre>
          </body>
        </html>"""
        return [html.encode('utf-8')]

    application = error_app
    app = error_app
