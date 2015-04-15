import json
import os
import re
import unittest
import yaml

from novaclient import client as testnovaclient 
from novaclient import exceptions
from mock import patch

from fake_request import fake_request

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
