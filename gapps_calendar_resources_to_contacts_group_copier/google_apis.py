import httplib2
import sys

from apiclient.discovery import build
from oauth2client.client import SignedJwtAssertionCredentials

import gdata.contacts.client
from gdata.gauth import OAuth2TokenFromCredentials
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage

SERVICE_ACCOUNT_EMAIL = '573247622343-dm1dkn76ei4jqk4856jo7551ddvp6eke@developer.gserviceaccount.com'
SERVICE_ACCOUNT_PKCS12_FILE_PATH = 'service.p12'
GDATA_SERVICES = {'contacts': gdata.contacts.client.ContactsClient,}

def ensureOAuthCredentials(secrets_file='client_secrets.json',
        storage_file='a_credentials_file',
        redirect_uri='https://localhost:8000/oauth2callback',
        scopes=[]):
    storage = Storage(storage_file)
    credentials = storage.get()
    if not credentials:
        flow = flow_from_clientsecrets(filename=secrets_file,
                scope=scopes,
                redirect_uri=redirect_uri,)
        # Try to get refresh token in response. Taken from:
        # https://developers.google.com/glass/develop/mirror/authorization
        flow.params['approval_prompt'] = 'force'
        auth_uri = flow.step1_get_authorize_url()
        print auth_uri
        code = raw_input("Auth token: ")
        credentials = flow.step2_exchange(code)
        storage.put(credentials)
    return credentials

def get_service_account_credentials(scopes=[], user_email=''):
    with file(SERVICE_ACCOUNT_PKCS12_FILE_PATH, 'rb') as f:
        key = f.read()
    return SignedJwtAssertionCredentials(SERVICE_ACCOUNT_EMAIL,
        key,
        scope=scopes,
        sub=user_email)

def get_credentials(scopes, email, storage_file='a_credentials_file'):
    if email:
        credentials = get_service_account_credentials(scopes=scopes, user_email=email)
    else:
        credentials = ensureOAuthCredentials(scopes=scopes, storage_file=storage_file)
    return credentials

def get_gdata_api(name, credentials, domain='', extra_kw={}):
    client = GDATA_SERVICES[name](domain=domain, **extra_kw)
    token = OAuth2TokenFromCredentials(credentials)
    return token.authorize(client)

def get_discovery_api(name, version, credentials):
    http = httplib2.Http()
    http = credentials.authorize(http)
    return build(serviceName=name, version=version, http=http)

def calendar(email=None):
    return get_discovery_api(name='calendar',
            version='v3',
            credentials=get_credentials(scopes=[
                'https://www.googleapis.com/auth/calendar',
                'https://apps-apis.google.com/a/feeds/calendar/resource/',],
                email=email))

def contacts(email=None):
    return get_gdata_api(name='contacts',
            domain=options().domain,
            credentials=get_credentials(scopes=['https://www.google.com/m8/feeds'],
            email=email))

def admin(email=None):
    return get_discovery_api(name='admin',
            version='directory_v1',
            credentials=get_credentials(scopes=[
                'https://www.googleapis.com/auth/admin.directory.group',
                'https://www.googleapis.com/auth/admin.directory.user',],
                email=email))
