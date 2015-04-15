import json
import os
import re
import requests
import yaml

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

