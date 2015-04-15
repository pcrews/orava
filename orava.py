import argparse
import logging
import os
import sys
import unittest

from  test_loader import load_test_suite

# orava.py - cli testing tool for error injection / stochastic testing

def get_parser():
    ##########
    # parser
    ##########
    description = 'orava.py - cli testing tool error-injection / stochastic testing'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--verbose',
                       action='count',
                       dest='verbose',
                       default=0,
                       help='Controls internal output.  Utilize multiple times to increase output'
                       )
    parser.add_argument('--map-file',
                       dest='map_file',
                       default='nova_base.dat',
                       help='Module containing test inputs.  Assumed to be in the config directory'
                       )
    parser.add_argument('--os_username',
                       action='store',
                       dest='osusername',
                       default=os.environ['OS_USERNAME'],
                       help='OpenStack username to use for testing.'
                       )
    parser.add_argument('--os_password',
                       action='store',
                       dest='ospassword',
                       default=os.environ['OS_PASSWORD'],
                       help='OpenStack password for os-username'
                       )
    parser.add_argument('--os_tenant_name',
                       action='store',
                       dest='ostenantname',
                       default=os.environ['OS_TENANT_NAME'],
                       help='OpenStack tenant name'
                       )
    parser.add_argument('--os_auth_url',
                       action='store',
                       dest='osauthurl',
                       default= os.environ['OS_AUTH_URL'],
                       help='OpenStack auth url (keystone endpoint)'
                       )
    return parser


#######
# main
#######
parser = get_parser()
args = parser.parse_args(sys.argv[1:])
print args, '<<<<<<<<<<<'
if args.verbose:
    logging.info("VERBOSE: argument values:")
    for key, item in vars(args).items():
        print("VERBOSE: %s || %s" % (key, item))

# configure logging
logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%Y%m%d-%H%M%S %p', level=logging.INFO)
# disable INFO-level logging for the requests library...it is noise here
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)

##################################
# test away!
##################################
suite = load_test_suite(args, args.map_file, logging)
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not result.wasSuccessful())
