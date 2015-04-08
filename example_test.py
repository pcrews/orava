import json
import os
import re
import requests
import unittest
from urlparse import urlparse
import yaml

from novaclient import client as testnovaclient 
from novaclient import exceptions
from mock import patch


def fake_request(self, url, method, inject_flag_file='./clientinject.dat', **kwargs):
    kwargs.setdefault('headers', kwargs.get('headers', {}))
    kwargs['headers']['User-Agent'] = self.USER_AGENT
    kwargs['headers']['Accept'] = 'application/json'
    if 'body' in kwargs:
        kwargs['headers']['Content-Type'] = 'application/json'
        kwargs['data'] = json.dumps(kwargs['body'])
        del kwargs['body']
    if self.timeout is not None:
        kwargs.setdefault('timeout', self.timeout)
    kwargs['verify'] = self.verify_cert

    self.http_log_req(method, url, kwargs)

    request_func = requests.request
    session = self._get_session(url)
    if session:
        request_func = session.request

    resp = request_func(
        method,
        url,
        **kwargs)

    # begin test patch
    if os.path.exists(inject_flag_file):
        # open, read and inject data
        replace_data=True
        with open(inject_flag_file) as infile:
            fake_response_data = yaml.load(infile)
        if fake_response_data['url']: # we want to re.match the given url
            replace_data=False # only replace on match
            if re.match(fake_response_data['url'], resp.url):
                replace_data=True
        if replace_data:
            # replace resp[value] w/ the fake data
            print "Fake response data: %s" % fake_response_data
            for key, value in fake_response_data['data'].items():
                setattr(resp, key, value)
            print 'Altered response values:'
            for key, value in vars(resp).items():
                print "%s: %s" %(key, value)
    # end test patch

    self.http_log_resp(resp)

    if resp.text:
        # TODO(dtroyer): verify the note below in a requests context
        # NOTE(alaski): Because force_exceptions_to_status_code=True
        # httplib2 returns a connection refused event as a 400 response.
        # To determine if it is a bad request or refused connection we need
        # to check the body.  httplib2 tests check for 'Connection refused'
        # or 'actively refused' in the body, so that's what we'll do.
        if resp.status_code == 400:
            if ('Connection refused' in resp.text or
                    'actively refused' in resp.text):
                raise exceptions.ConnectionRefused(resp.text)
        try:
            body = json.loads(resp.text)
        except ValueError:
            body = None
    else:
        body = None
    if resp.status_code >= 400:
        raise exceptions.from_response(resp, body, url, method)

    return resp, body

class ClientTestCase(unittest.TestCase):
    """Test case for the client methods."""

    def setUp(self):
        user = os.environ['OS_USERNAME']
        pw = os.environ['OS_PASSWORD']
        auth_url = os.environ['OS_AUTH_URL']
        project = os.environ['OS_TENANT_NAME']
        self.inject_file_path='./clientinject.dat'
        self.patcher = patch('novaclient.client.HTTPClient.request', fake_request)
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
