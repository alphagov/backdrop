from logging import getLogger
from flask import redirect, json
from admin_ui_helper import url_for
from rauth import OAuth2Service, service

log = getLogger(__name__)


class Signonotron2(object):
    def __init__(self, client_id, client_secret, base_url,
                 backdrop_admin_ui_host):
        self.signon = OAuth2Service(
            client_id=client_id,
            client_secret=client_secret,
            name="backdrop",
            authorize_url="%s/oauth/authorize" % base_url,
            access_token_url="%s/oauth/token" % base_url,
            base_url=base_url
        )
        self.backdrop_admin_ui_host = backdrop_admin_ui_host

    def __redirect_uri(self):
        return url_for(self.backdrop_admin_ui_host, "oauth_authorized")

    def __json_access_token(self, something):
        return json.loads(something)

    def authorize(self):
        params = {
            "response_type": "code",
            "redirect_uri": self.__redirect_uri()
        }
        return redirect(self.signon.get_authorize_url(**params))

    def exchange(self, code):
        data = dict(
            grant_type='authorization_code',
            redirect_uri=self.__redirect_uri(),
            code=code
        )
        response = self.signon.get_raw_access_token('POST', data=data)
        access_token = None

        if response.status_code in [200, 201]:
            try:
                access_token = service.process_token_request(
                    response, self.__json_access_token, 'access_token')[0]
            except KeyError as e:
                log.warn('Could not parse token from response :' + str(e))

        return access_token

    def user_details(self, access_token):
        if access_token is None:
            return None, None

        session = self.signon.get_session(access_token)
        user_details_response = session.get('user.json')
        if user_details_response.status_code in [200, 201]:
            _user_details = user_details_response.json()
            user_details = _user_details, \
                "signin" in _user_details["user"]["permissions"]
        else:
            user_details = None, None
        return user_details
