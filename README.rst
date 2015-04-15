# orava
error injecting / stochastic cli testing tool

Running the example test
------------------------

This simple proof of concept is designed to be run against a devstack instance.
It pokes at novaclient and injects a test status code and message into what
should into what should be a good nova.list_flavors() call.

It works by using mock.patch to alter novaclient's most basic 'request' method.
The patched version includes logic to check if the user has specified any
test data to be injected into the response object before passing it onto the
rest of the client code.

We expect relevant credentials (openrc) to be set as env vars.
::
    python -m unittest example_test


Running a test case with variants
---------------------------------

To run a more complex test case that supports variants
::
    python orava.py --map-file=test_maps/basic.yml 

This command line will run 14 variations of a single test case, that is
focused on nova.flavor_list.
