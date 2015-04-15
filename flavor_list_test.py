import json
import os
import re
import unittest
import yaml

from novaclient import client as testnovaclient 
from mock import patch

from fake_request import fake_request

class ClientTestCase(unittest.TestCase):
    """Test case for the client methods."""

    def __init__( self, test_description, args, logging,
                  testname, test_data):
        super(ClientTestCase, self).__init__(testname)
        self.test_description = test_description
        self.args = args
        self.logging = logging
        self.test_data = test_data
        self.exp_exception = self.test_data.get('exception')


        # json-ify any _content for the request
        if '_content' in self.test_data['data']:
            x = (self.test_data['data']['_content'])
            x = json.dumps(x)
            self.test_data['data']['_content'] = x

        # we assume expected_exception is something like:
        # file_name.className and we do a split so we
        # can import the class
        if self.exp_exception:
            data = self.exp_exception.split('.')
            class_name = data[-1]
            exception_module_name = '.'.join(data[:-1])
            try:
                exp_module = __import__(exception_module_name, fromlist=[class_name])
                self.exp_exception = getattr(exp_module, class_name)
            except Exception, e:
                print Exception, e



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
        print ''
        response = ''
        cm = None

        self.write_inject_file(self.test_data)

        if self.exp_exception:
            with self.assertRaises(self.exp_exception) as cm:
                print 'Expected exception: %s' %self.exp_exception
                response = self.client.flavors.list()
        else:
            response = self.client.flavors.list()
        if cm:
            print 'Exception info: %s' % vars(cm.exception)
            self.assertEqual(self.test_data['data']['status_code'], cm.exception.code)
        print 'Test response: %s' %response
        print '-'*80
        self.remove_inject_file()
