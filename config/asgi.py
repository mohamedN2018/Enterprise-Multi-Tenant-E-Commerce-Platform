"""ASGI entrypoint (HTTP + WebSocket via Channels).

WebSocket routes are added to the ProtocolTypeRouter as realtime features land
(e.g. notifications in a later feature).
"""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

# Initialise Django ASGI application early to populate the app registry before
# importing anything that touches models / channel routing.
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        # "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
