from urllib.parse import urlparse
import re
import sys
import requests

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def python_regex(orm_regex):
    return '^{}$'.format(orm_regex)

def run_tests(tests, target, verify_certs=True):
    #pylint:disable=too-many-locals
    # TODO: clean up ^
    for test in tests:
        print("Run tests from: %s" % test['_orm_source_file'])
        name = test.get("name")
        url = test["request"]["url"]
        status = test["expect"].get("status")
        body = test["expect"].get("body", [])
        test_headers = test["expect"].get("headers", [])
        url_parsed = urlparse(url)
        do_target = "{scheme}://{netloc}{path}".format(
            scheme=url_parsed.scheme,
            netloc=target,
            path=url_parsed.path
        )
        if url_parsed.query:
            do_target = '{}?{}'.format(do_target, url_parsed.query)
        if url_parsed.fragment:
            do_target = '{}#{}'.format(do_target, url_parsed.fragment)
        print("  %s" % name)
        headers = {
            'Host': url_parsed.netloc
        }
        r = requests.get(do_target,
                         headers=headers,
                         verify=verify_certs,
                         allow_redirects=False)

        if status:
            if r.status_code != status:
                print("    Got status code %s, expect %s"
                      % (r.status_code, status))
                sys.exit(1)

        for b in body:
            regex = python_regex(b["regex"])
            if not re.search(regex, r.text, flags=re.MULTILINE):
                print("    Body did not match %s" % regex)
                print("Body:\n{}".format(r.text))
                sys.exit(1)

        for h in test_headers:
            # Make sure that all expected headers are there
            if h['field'] not in r.headers:
                print("    Header %s not found" % h['field'])
                sys.exit(1)

            # Check that the expected header contains the correct data
            for header in test_headers:
                hf = header['field']
                hr = python_regex(header['regex'])
                if not re.search(hr, r.headers.get(hf)):
                    print("    Header %s contains %s, expected %s"
                          % (hf, r.headers.get(hf), hr))
                    sys.exit(1)
