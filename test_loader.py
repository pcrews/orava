""" test_loader:
    Module for handling the ugly work of
    sifting through variants + loading them into the test suite
    Probably a better way exists...I should find it :/

"""
import os
import yaml
import unittest


def load_test_suite(args, map_file, logging):
    testloader = unittest.TestLoader()
    suite = unittest.TestSuite()

    map_dir = 'test_maps'

    # get our test input variants (nodes, names, etc)
    # assuming all such files live in map_dir
    # this is a convenience that may be removed / replaced
    # should it prove stupid
    if map_dir not in os.path.dirname(map_file):
        map_file = os.path.join(map_dir, map_file)
    with open(map_file, 'r') as inputs_file:
        test_inputs = yaml.load(inputs_file)

    # iterate through our dictionary of test_inputs and
    # create test cases.  We create one test for the suite
    # based on each 'variant' of a test that is provided.
    # The idea is to have a single test module that can
    # accept many inputs to provide more flexible / lazy / automated
    # testing

    for test_module_name, variants in test_inputs.items():
        # we assume test_module_name is something like:
        # file_name.className and we do a split so we
        # can import the class
        data = test_module_name.split('.')
        class_name = data[-1]
        test_module_name = '.'.join(data[:-1])
        try:
            test_module = __import__(test_module_name, fromlist=[class_name])
            test_class = getattr(test_module, class_name)
        except Exception, e:
            print Exception, e
        testnames = testloader.getTestCaseNames(test_class)
        for test_name in testnames:
            for test_variant in variants:
                # what variations of test_module should be created
                disabled = test_variant.get('disabled',None)
                if not disabled:
                    test_desc = test_variant.get('description','a test')
                    test_data = test_variant.get('test_data',None)
                    suite.addTest(test_class(test_desc,
                                             args,
                                             logging,
                                             test_name,
                                             test_data))
    return suite
