import unittest
import string
import re

from orm.render import ORMInternalRenderException
import orm.rendervarnish as rendervarnish
from orm.rendervarnish import RenderVarnish

def assertIsStringList(self, lst, emptyOk=True):
    self.assertIsInstance(lst, list)
    for elem in lst:
        self.assertIsInstance(elem, str)
    if not emptyOk:
        self.assertTrue(lst)

class RenderVarnishTest(unittest.TestCase):
    def setUp(self):
        self.render = RenderVarnish(rule_docs={})
        self.match_tree = {'or': [{'and': [{'match': {'source': 'path',
                                                      'function': 'exact',
                                                      'input': {
                                                          'value': 'foo'
                                                      }}}]},
                                  {'not': {'match': {'source': 'path',
                                                     'function': 'exact',
                                                     'input': {
                                                         'value': 'bar'
                                                     }}}},
                                  {'match': {'source': 'path',
                                             'function': 'exact',
                                             'input': {
                                                 'value': 'baz'
                                             }}}]}

    def test_vcl_escape_string_to_regex(self):
        in_regex = r'derp"yeah"[^boi]/'
        exp_regex = r'derp\x22yeah\x22\[\^boi\]/'
        regex = rendervarnish.vcl_escape_string_to_regex(in_regex)
        self.assertEqual(regex, exp_regex)

    def test_vcl_escape_regex(self):
        in_regex = r'!derp"yeah"[^boi]/'
        exp_regex = r'!derp\x22yeah\x22[^boi]/'
        regex = rendervarnish.vcl_escape_regex(in_regex)
        self.assertEqual(regex, exp_regex)

    def test_vcl_safe_string(self):
        # bad_str contains '"}' which is end of long string syntax in Varnish
        bad_str = r'"}a{"{"">"}b"}'
        nice_bad_str = rendervarnish.vcl_safe_string(bad_str)
        exp_str = r'{"""} "}" {"a{"{"">""} "}" {"b""} "}" {""}'
        self.assertEqual(nice_bad_str, exp_str)
        # ok_str contains '"' which is end of string syntax in Varnish
        ok_str = r'a{"{"">}b'
        exp_str = r'{"a{"{"">}b"}'
        nice_ok_str = rendervarnish.vcl_safe_string(ok_str)
        self.assertEqual(nice_ok_str, exp_str)
        # nice_str contains no '"}' nor '"'
        nice_str = r'a{{>}b'
        exp_str = r'"a{{>}b"'
        nice_nice_str = rendervarnish.vcl_safe_string(nice_str)
        self.assertEqual(nice_nice_str, exp_str)
        # newline_str contains '\n' which should be trimmed
        newline_str = '\na\nb\n'
        exp_str = '"ab"'
        nice_newline_str = rendervarnish.vcl_safe_string(newline_str)
        self.assertEqual(nice_newline_str, exp_str)
        # newline_body_str contains '\n' which should be kept in the string
        newline_body_str = "<html>\n<body>\nHello\n</body>\n</html>"
        exp_str = '"<html>\n<body>\nHello\n</body>\n</html>"'
        nice_with_newlines_str = rendervarnish.vcl_safe_string(newline_body_str,
                                                               strip_newline=False)
        self.assertEqual(nice_with_newlines_str, exp_str)


    def test_get_unique_vcl_name(self):
        namespace = 'ns'
        allowed_pattern = re.compile(r'^' + namespace + r'_[a-zA-Z0-9_]+$')
        name1 = self.render.get_unique_vcl_name(namespace, string.printable)
        name2 = self.render.get_unique_vcl_name(namespace, string.printable)
        self.assertIsInstance(name1, str)
        self.assertIsNotNone(re.search(allowed_pattern, name1))
        self.assertIsInstance(name2, str)
        self.assertIsNotNone(re.search(allowed_pattern, name2))
        self.assertNotEqual(name1, name2)

    def test_make_match_path(self):
        with self.assertRaises(ORMInternalRenderException):
            self.render.make_match_path('unsupported_match_function',
                                        {'value': 'derp'})
        value = re.sub('\n|\r|\v|\f', '', string.printable)
        inp = {'value': value}
        allowed_pattern = re.compile(r'^variable\.get\("path"\) ~ {?".*"}?$')
        for function in ['regex', 'exact', 'begins_with', 'ends_with',
                         'contains']:
            match = self.render.make_match_path(function, inp)
            self.assertIsInstance(match, str)
            self.assertIsNotNone(re.search(allowed_pattern, match))

    def test_make_match_query(self):
        with self.assertRaises(ORMInternalRenderException):
            self.render.make_match_path('unsupported_match_function',
                                        {'value': 'derp'})
        value = re.sub('\n|\r|\v|\f', '', string.printable)
        inp = {'value': value}
        allowed_pattern = re.compile(r'^variable\.get\("query"\) ~ {?".*"}?$')
        for function in ['regex', 'exact', 'begins_with', 'ends_with',
                         'contains']:
            match = self.render.make_match_query(function, inp)
            self.assertIsInstance(match, str)
            self.assertIsNotNone(re.search(allowed_pattern, match))

    def test_make_match_domain(self):
        inp = re.sub('\n|\r|\v|\f', '', string.printable)
        with self.assertRaises(ORMInternalRenderException):
            self.render.make_match_path('unsupported_match_function',
                                        {'value': 'derp'})
        allowed_pattern = re.compile(r'^req\.http\.host (==|~) {?".*"}?$')
        for function in ['exact']:
            match = self.render.make_match_domain(function, inp)
            self.assertIsInstance(match, str)
            self.assertIsNotNone(re.search(allowed_pattern, match))

    def test_make_condition_match(self):
        unknown_source_match = {'source': 'unknown_source',
                                'function': 'exact',
                                'input': 'foo'}
        with self.assertRaises(ORMInternalRenderException):
            self.render.make_condition_match(unknown_source_match)
        for source in ['path', 'domain', 'query']:
            if source == 'query':
                inp = {'parameter': 'foo',
                       'value': 'bar'}
            elif source == 'path':
                inp = {'value': 'bar'}
            else:
                inp = 'lizard'
            match = {'source': source, 'function': 'exact', 'input': inp}
            condition = self.render.make_condition_match(match)
            self.assertIsInstance(condition, str)

    def test_handle_condition_list(self):
        match_tree_list = [{'match': {'source': 'path',
                                      'function': 'exact',
                                      'input': {
                                          'value': 'foo'
                                      }}},
                           {'match': {'source': 'path',
                                      'function': 'exact',
                                      'input': {
                                          'value': 'bar'
                                      }}}]
        cond1 = self.render.handle_condition_list('operator',
                                                  match_tree_list)
        self.assertIsInstance(cond1, str)
        cond2 = self.render.handle_condition_list('operator',
                                                  match_tree_list,
                                                  negate=True,
                                                  indent_depth=7)
        self.assertIsInstance(cond2, str)

    def test_parse_match_tree(self):
        unknown_key_tree = {'unknown_key': 'YEAH'}
        with self.assertRaises(ORMInternalRenderException):
            self.render.parse_match_tree(unknown_key_tree)
        cond1 = self.render.parse_match_tree(self.match_tree)
        self.assertIsInstance(cond1, str)
        cond2 = self.render.parse_match_tree(self.match_tree,
                                             negate=True,
                                             indent_depth=3)
        self.assertIsInstance(cond2, str)

    def test_make_condition(self):
        cond = self.render.make_condition(self.match_tree, 'rule_id')
        assertIsStringList(self, cond, emptyOk=False)

    def test_make_match_sub(self):
        sub = self.render.make_match_sub(self.match_tree, 'rule_id', 'sub_name')
        assertIsStringList(self, sub, emptyOk=False)

    def test_make_actions(self):
        unknown_action_config = {'unknown': 'action',
                                 'backend': {'origin': 'example.com'}}
        with self.assertRaises(ORMInternalRenderException):
            self.render.make_actions(unknown_action_config,
                                     'rule_id',
                                     match_sub_name='sub_name')
        action_config = {
            'https_redirection': True,
            'trailing_slash': 'add',
            'redirect': {'type': 'temporary',
                         'url': 'example.com'},
            'header_southbound': [{'remove': 'this'}],
            'backend': {'origin': 'example.com'},
            'header_northbound': [{'remove': 'that'}],
            'req_path': [{
                'replace': {
                    'from_exact': 'yeah',
                    'to': 'ooo',
                    'occurrences': 'first',
                    'ignore_case': True
                }
            }]
        }
        # None of domain and is_global is set
        with self.assertRaises(ORMInternalRenderException):
            self.render.make_actions(action_config,
                                     'rule_id')
        domain = 'domain'
        # Create regular rules
        created = self.render.make_actions(action_config,
                                           'rule_id',
                                           domain=domain,
                                           match_sub_name='sub_name')
        self.assertTrue(created)
        sb = self.render.actions_southbound
        nb = self.render.actions_northbound
        assertIsStringList(self, sb[domain], emptyOk=False)
        assertIsStringList(self, nb[domain], emptyOk=False)
        # Create default rules
        created = self.render.make_actions(action_config,
                                           'rule_id',
                                           domain=domain)
        self.assertTrue(created)
        sb = self.render.default_actions_southbound
        nb = self.render.default_actions_northbound
        assertIsStringList(self, sb[domain], emptyOk=False)
        assertIsStringList(self, nb[domain], emptyOk=False)
        # Create global rules
        created_global = self.render.make_actions(action_config,
                                                  'rule_id',
                                                  is_global=True)
        self.assertTrue(created_global)
        sb_global = self.render.global_actions_southbound
        nb_global = self.render.global_actions_northbound
        assertIsStringList(self, sb_global, emptyOk=False)
        assertIsStringList(self, nb_global, emptyOk=False)

def fresh_action_args():
    return {
        'config_out': {
            'sb': [],
            'nb': [],
            'synth': []
        },
        'rule_id': 'dummy_rule_id'
    }

class RenderVarnishActionsTest(unittest.TestCase):
    def assertActionConfigOut(self, config_out, only=None):
        config_out_keys = ('sb', 'nb', 'synth')
        self.assertTrue(all(key in config_out_keys for key in config_out))
        self.assertIsInstance(config_out, dict)
        if only:
            for key in config_out:
                if key in only:
                    assertIsStringList(self, config_out[key], emptyOk=False)
                else:
                    self.assertIsInstance(config_out[key], list)
                    self.assertFalse(config_out[key])
        else:
            assertIsStringList(self, config_out['sb'])
            assertIsStringList(self, config_out['nb'])
            assertIsStringList(self, config_out['synth'])

    def setUp(self):
        self.rule_id = 'dummy_rule_id'

    def test_make_header_action(self):
        unknown_header_action_config = [
            {'unknown_header_action': 'is_unknown'}
        ]
        with self.assertRaises(ORMInternalRenderException):
            rendervarnish.make_sb_header_action(unknown_header_action_config,
                                                **fresh_action_args())
        header_action_config = [
            {'set': {'field': 'grodan', 'value': 'boll'}},
            {'add': {'field': 'kalle', 'value': 'stropp'}},
            {'remove': 'internet'}
        ]
        config_out = rendervarnish.make_sb_header_action(header_action_config,
                                                         **fresh_action_args())
        self.assertActionConfigOut(config_out, only=('sb'))
        config_out = rendervarnish.make_nb_header_action(header_action_config,
                                                         **fresh_action_args())
        self.assertActionConfigOut(config_out, only=('nb'))

    def test_make_redirect_action(self):
        redir_types = [
            'temporary',
            'permanent',
            'temporary_allow_method_change',
            'permanent_allow_method_change'
        ]
        for redir_type in redir_types:
            redirect_configs = []
            # Test explicit redirect with url
            redirect_configs.append({
                'type': redir_type,
                'url': 'example.com'
            })
            # Test dynamic redirect with only domain specified
            redirect_configs.append({
                'type': redir_type,
                'domain': 'another.example.com'
            })
            # Test dynamic redirect with only path specified
            path = [{
                'replace': {
                    'from_exact': 'yeah',
                    'to': 'ooo',
                }
            }]
            redirect_configs.append({
                'type': redir_type,
                'path': path
            })
            for scheme in ['http', 'https']:
                # Test dynamic redirect with only scheme specified
                redirect_configs.append({
                    'type': redir_type,
                    'scheme': scheme
                })
                # Test dynamic redirect with everything specified
                redirect_configs.append({
                    'type': redir_type,
                    'scheme': scheme,
                    'domain': 'yeah',
                    'path': path
                })
            for config in redirect_configs:
                config_out = rendervarnish.make_redirect_action(config,
                                                                **fresh_action_args())
                self.assertActionConfigOut(config_out, only=('sb'))

    def test_make_synth_resp_action(self):
        config_out = rendervarnish.make_synth_resp_action('YEAH',
                                                          **fresh_action_args())
        self.assertActionConfigOut(config_out, only=('sb', 'synth'))

    def test_make_backend_action(self):
        backend_config = {'origin': 'internet.example.com'}
        config_out = rendervarnish.make_backend_action(backend_config,
                                                       **fresh_action_args())
        self.assertActionConfigOut(config_out, only=('sb'))
        backend_config = {'servers': ['internet.example.com', 'space.example.com']}
        config_out = rendervarnish.make_backend_action(backend_config,
                                                       **fresh_action_args())
        self.assertActionConfigOut(config_out, only=('sb'))

    def test_make_https_redir_action(self):
        config_out = rendervarnish.make_https_redir_action(True,
                                                           **fresh_action_args())
        self.assertActionConfigOut(config_out, only=('sb'))

    def test_make_trailing_slash_action(self):
        for trailing_slash_action in ['add', 'remove']:
            config_out = rendervarnish.make_trailing_slash_action(trailing_slash_action,
                                                                  **fresh_action_args())
            self.assertActionConfigOut(config_out, only=('sb'))
        config_out = rendervarnish.make_trailing_slash_action('do_nothing',
                                                              **fresh_action_args())
        self.assertActionConfigOut(config_out, only=())
        unknown_action = 'walk_the_dogs'
        with self.assertRaises(ORMInternalRenderException):
            rendervarnish.make_trailing_slash_action(unknown_action,
                                                     **fresh_action_args())

    def test_make_path_mod_actions(self):
        unknown_path_mod_config = {
            'unknown': 'stuff'
        }
        with self.assertRaises(ORMInternalRenderException):
            rendervarnish.make_path_mod_actions(unknown_path_mod_config,
                                                **fresh_action_args())
        path_mod_config = [{
            'replace': {
                'from_exact': 'yeah',
                'to': 'ooo',
            }
        }, {
            'replace': {
                'from_regex': 'foob',
                'to': 'bar',
            }
        }]
        config_out = rendervarnish.make_path_mod_actions(path_mod_config,
                                                         **fresh_action_args())
        self.assertActionConfigOut(config_out, only=('sb'))

    def test_make_action_if_clause(self):
        actions = [
            'this',
            'and',
            'that'
        ]
        if_clause = rendervarnish.make_action_if_clause(actions, 'rule_id')
        assertIsStringList(self, if_clause, emptyOk=False)

    def test_make_path_replace_action(self):
        unknown_from_replace_config = {
            'from_unknown': 'foo',
            'to': 'bar'
        }
        with self.assertRaises(ORMInternalRenderException):
            rendervarnish.make_path_replace_action(unknown_from_replace_config)
        unknown_to_replace_config = {
            'from': 'foo',
            'to_unknown': 'halp!'
        }
        with self.assertRaises(ORMInternalRenderException):
            rendervarnish.make_path_replace_action(unknown_to_replace_config)
        for key in ['exact', 'regex']:
            for occurrences in ['first', 'all']:
                for ignore_case in [True, False]:
                    replace_config = {
                        'from_' + key: 'yeah',
                        'to': 'ooo',
                        'occurrences': occurrences,
                        'ignore_case': ignore_case
                    }
                    req_path = rendervarnish.make_path_replace_action(
                        replace_config,
                        indent_depth=9
                    )
                    assertIsStringList(self, req_path, emptyOk=False)
        replace_config = {
            'from_regex': '(.*)-gator-number-(\\d+)',
            'to_regsub': '\\U\\1-snek #\\2'
        }
        req_path = rendervarnish.make_path_replace_action(replace_config,
                                                          indent_depth=7)
        assertIsStringList(self, req_path, emptyOk=False)

    def test_make_path_prefix_action(self):
        prefix_configs = [{
            'add': 'derp'
        }, {
            'remove': 'merp'
        }, {
            'add': 'derp',
            'remove': 'merp'
        }]
        for prefix_config in prefix_configs:
            config_out = rendervarnish.make_path_prefix_action(prefix_config)
            assertIsStringList(self, config_out, emptyOk=False)

if __name__ == '__main__':
    unittest.main()
