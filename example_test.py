import json
import os
import re
import requests
import unittest
import yaml

from novaclient import client as testnovaclient 
from novaclient import exceptions
from mock import patch
from requests.api import sessions

def fake_request(method, url, **kwargs):
    """Constructs and sends a :class:`Request <Request>`.
    :param method: method for the new :class:`Request` object.
    :param url: URL for the new :class:`Request` object.
    :param params: (optional) Dictionary or bytes to be sent in the query string for the :class:`Request`.
    :param data: (optional) Dictionary, bytes, or file-like object to send in the body of the :class:`Request`.
    :param json: (optional) json data to send in the body of the :class:`Request`.
    :param headers: (optional) Dictionary of HTTP Headers to send with the :class:`Request`.
    :param cookies: (optional) Dict or CookieJar object to send with the :class:`Request`.
    :param files: (optional) Dictionary of ``'name': file-like-objects`` (or ``{'name': ('filename', fileobj)}``) for multipart encoding upload.
    :param auth: (optional) Auth tuple to enable Basic/Digest/Custom HTTP Auth.
    :param timeout: (optional) How long to wait for the server to send data
        before giving up, as a float, or a (`connect timeout, read timeout
        <user/advanced.html#timeouts>`_) tuple.
    :type timeout: float or tuple
    :param allow_redirects: (optional) Boolean. Set to True if POST/PUT/DELETE redirect following is allowed.
    :type allow_redirects: bool
    :param proxies: (optional) Dictionary mapping protocol to the URL of the proxy.
    :param verify: (optional) if ``True``, the SSL cert will be verified. A CA_BUNDLE path can also be provided.
    :param stream: (optional) if ``False``, the response content will be immediately downloaded.
    :param cert: (optional) if String, path to ssl client cert file (.pem). If Tuple, ('cert', 'key') pair.
    :return: :class:`Response <Response>` object
    :rtype: requests.Response
    Usage::
      >>> import requests
      >>> req = requests.request('GET', 'http://httpbin.org/get')
      <Response [200]>
    """

    session = sessions.Session()
    response = session.request(method=method, url=url, **kwargs)
    # By explicitly closing the session, we avoid leaving sockets open which
    # can trigger a ResourceWarning in some cases, and look like a memory leak
    # in others.
    session.close()

    # begin test patch
    inject_flag_file='./clientinject.dat'
    if os.path.exists(inject_flag_file):
        # open, read and inject data
        replace_data=True
        with open(inject_flag_file) as infile:
            fake_response_data = yaml.load(infile)
            print fake_response_data
        if fake_response_data['url']: # we want to re.match the given url
            replace_data=False # only replace on match
            if re.match(fake_response_data['url'], response.url):
                replace_data=True
        if replace_data:
            # replace resp[value] w/ the fake data
            print "Fake response data: %s" % fake_response_data
            for key, value in fake_response_data['data'].items():
                setattr(response, key, value)
            print 'Altered response values:'
            for key, value in vars(response).items():
                print "%s: %s" %(key, value)
    # end test patch

    return response



class ClientTestCase(unittest.TestCase):
    """Test case for the client methods."""

    def setUp(self):
        user = os.environ['OS_USERNAME']
        pw = os.environ['OS_PASSWORD']
        auth_url = os.environ['OS_AUTH_URL']
        project = os.environ['OS_TENANT_NAME']
        self.inject_file_path='./clientinject.dat'
        self.patcher = patch('requests.request', fake_request)
        self.patcher.start()
        self.client = testnovaclient.Client(2, user, pw, project, auth_url) 


    def tearDown(self):
        self.patcher.stop()
        if os.path.exists(self.inject_file_path): 
            self.remove_inject_file()

    
    def write_inject_file(self, data):
        with open(self.inject_file_path, 'w') as outfile:
            yaml.dump(data, outfile, default_flow_style=False)


    def remove_inject_file(self):
        os.remove(self.inject_file_path)


    def test_request(self):
        """Test a simple request."""
        test_sets = [#{'url':"http://.*:8774/.*/flavors/detail", 'data':{'candy':'yum!'}},
                     {'url':"http://.*:8774/.*/flavors/detail", 'data':{'status_code': 90210, '_content': json.dumps({'error':{'message':'Old Gregg did not like you being in his waters!', 'detail':'Mmmm...creamy.'}})}, 'exception':exceptions.ClientException},
                    ]
        for test_set in test_sets:
            response = ''
            cm = None
            self.write_inject_file(test_set)
            exp_exception = test_set.get('exception')
            if exp_exception:
                with self.assertRaises(exp_exception) as cm:
                    print 'Expected exception: %s' %exp_exception
                    response = self.client.flavors.list()
            else:
                response = self.client.flavors.list()
            if cm:
                print 'Exception info: %s' % vars(cm.exception)
                self.assertEqual(test_set['data']['status_code'], cm.exception.code)
            print 'Test response: %s' %response
            self.remove_inject_file()
            print '#'*80
