import requests
from datetime import datetime, timedelta
from vehicle import Vehicle

TESLA_API_BASE_URL = 'https://owner-api.teslamotors.com/'
TOKEN_URL = TESLA_API_BASE_URL + 'oauth/token'
API_URL = TESLA_API_BASE_URL + 'api/1'

OAUTH_CLIENT_ID = '81527cff06843c8634fdc09e8ac0abefb46ac849f38fe1e431c2ef2106796384'
OAUTH_CLIENT_SECRET = 'c7257eb71a564034f9419ee651c7d0e5f7aa6bfbd18bafb5c5c033b093bb2fa3'


class TeslaClient:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.token = None

    def get_new_token(self):
        request_data = {'grant_type': 'password',
                        'client_id': OAUTH_CLIENT_ID,
                        'client_secret': OAUTH_CLIENT_SECRET,
                        'email': self.email,
                        'password': self.password}
        response = requests.post(TOKEN_URL, data=request_data)
        response_json = response.json()
        print(response_json)

        if 'response' in response_json:
            raise AuthenticationError(response_json['response'])

        return response_json

    def refresh_token(self, refresh_token):
        request_data = {'grant_type': 'refresh_token',
                        'client_id': OAUTH_CLIENT_ID,
                        'client_secret': OAUTH_CLIENT_SECRET,
                        'refresh_token': refresh_token}
        response = requests.post(TOKEN_URL, data=request_data)
        response_json = response.json()
        # print(response_json)

        if 'response' in response_json:
            raise AuthenticationError(response_json['response'])

        return response_json

    def authenticate(self):
        if not self.token:
            self.token = self.get_new_token()

        expiry_time = timedelta(seconds=self.token['expires_in'])
        expiration_date = datetime.fromtimestamp(self.token['created_at']) + expiry_time

        if datetime.utcnow() >= expiration_date:
            self.token = self.refresh_token(self.token['refresh_token'])

    def get_headers(self):
        return {'Authorization': f'Bearer {self.token["access_token"]}'}

    def get(self, endpoint):
        self.authenticate()

        response = requests.get(f'{API_URL}/{endpoint}', headers=self.get_headers())
        response_json = response.json()

        if 'error' in response_json:
            raise ApiError(response_json['error'])

        return response_json['response']

    def post(self, endpoint, data={}):
        self.authenticate()

        response = requests.post(f'{API_URL}/{endpoint}', headers=self.get_headers(), data=data)
        response_json = response.json()

        if 'error' in response_json:
            raise ApiError(response_json['error'])

        return response_json['response']

    def get_vehicles(self):
        vehicles = self.get('vehicles')
        print(vehicles)
        return [Vehicle(self, vehicle) for vehicle in vehicles]


class AuthenticationError(Exception):
    def __init__(self, error):
        super().__init__('Authentication to the Tesla API failed: {}'.format(error))


class ApiError(Exception):
    def __init__(self, error):
        super().__init__('Tesla API call failed: {}'.format(error))