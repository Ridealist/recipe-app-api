from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions
from rest_framework.authentication import CSRFCheck, TokenAuthentication
from rest_framework.authentication import get_authorization_header


def enforce_csrf(request):
    check = CSRFCheck()
    check.process_request(request)
    reason = check.process_view(request, None, (), {})
    if reason:
        raise exceptions.PermissionDenied("CSRF Failed: %s" % reason)


class CustomAuthentication(TokenAuthentication):
    """Overriding authenticate method"""

    def authenticate(self, request):
        auth = get_authorization_header(request).split()

        if auth:
            if auth[0].lower() != self.keyword.lower().encode():
                return None

            if len(auth) == 1:
                msg = _("Invalid token header. No credentials provided.")
                raise exceptions.AuthenticationFailed(msg)
            elif len(auth) > 2:
                msg = _(
                    "Invalid token header. \
                        Token string should not contain spaces."
                )
                raise exceptions.AuthenticationFailed(msg)

            try:
                token = auth[1].decode()
            except UnicodeError:
                msg = _(
                    "Invalid token header. \
                        Token string should not contain invalid characters."
                )
                raise exceptions.AuthenticationFailed(msg)

        else:
            token = (
                request.COOKIES.get(settings.AUTH_TOKEN["AUTH_COOKIE"]) or None
            )
            if token is None:
                return None

        enforce_csrf(request)
        return self.authenticate_credentials(token)
