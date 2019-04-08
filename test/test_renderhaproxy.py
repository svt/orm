import unittest

from orm.render import ORMInternalRenderException
from orm.renderhaproxy import RenderHAProxy
import orm.renderhaproxy as renderhaproxy

class RenderHAProxyTest(unittest.TestCase):
    def assertIsStringList(self, lst, emptyOk=True):
        self.assertIsInstance(lst, list)
        for elem in lst:
            self.assertIsInstance(elem, str)
        if not emptyOk:
            self.assertTrue(lst)

    def setUp(self):
        self.render = RenderHAProxy(rule_docs={})

    def test_make_backend_action(self):
        backend_config = {'origin': 'internet.example.com'}
        self.render.make_backend_action(backend_config, 'rule_id')
        self.assertIsStringList(self.render.backends, emptyOk=False)
        self.assertIsStringList(self.render.backend_acls, emptyOk=False)
        backend_config = {'servers': ['internet.example.com', 'space.example.com']}
        self.render.make_backend_action(backend_config, 'rule_id')
        self.assertIsStringList(self.render.backends, emptyOk=False)
        self.assertIsStringList(self.render.backend_acls, emptyOk=False)
        backend_config_unknown = {'unknown': 'backend config'}
        with self.assertRaises(ORMInternalRenderException):
            self.render.make_backend_action(backend_config_unknown, 'rule_id')
        backend_config_unknown_scheme = {'origin': 'derp://example.com'}
        with self.assertRaises(ORMInternalRenderException):
            self.render.make_backend_action(backend_config_unknown_scheme,
                                            'rule_id')

    def test_make_actions(self):
        unknown_action_config = {'unknown': 'action',
                                 'backend': {'origin': 'example.com'}}
        with self.assertRaises(ORMInternalRenderException):
            self.render.make_actions(unknown_action_config, 'rule_id')
        action_config = {
            'redirect': {'type': 'temporary',
                         'url': 'example.com'},
            'header_southbound': [{'remove': 'this'}],
            'backend': {'origin': 'example.com'},
            'header_northbound': [{'remove': 'that'}],
            'req_path': [{
                'replace': {
                    'from_exact': 'yeah',
                    'to': 'ooo',
                    'how': 'first_occurrence'
                }
            }]
        }
        self.render.make_actions(action_config, 'rule_id')
        self.assertIsStringList(self.render.backends, emptyOk=False)
        self.assertIsStringList(self.render.backend_acls, emptyOk=False)

    def test_make_custom_internal_healthcheck(self):
        healthcheck_config = None
        out = renderhaproxy.make_custom_internal_healthcheck(healthcheck_config)
        self.assertIsInstance(out, list)
        self.assertFalse(out)

        healthcheck_config = {
            'http': {
                'method': 'GET',
                'path': '/',
                'domain': 'example.com'
            }
        }
        out = renderhaproxy.make_custom_internal_healthcheck(healthcheck_config)
        self.assertIsStringList(out, emptyOk=False)
