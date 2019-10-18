import unittest
import re

import string

import orm.parser as parser

class ParseRulesTest(unittest.TestCase):
    #pylint:disable=too-many-instance-attributes
    def setUp(self):
        self.maxDiff = None
        testpath = 'test/testdata/parser/'
        self.valid_rule_file = testpath + 'rule.yml'
        self.valid_rule_file2 = testpath + 'rule2.yml'
        self.invalid_rule_file = testpath + 'invalid_rule.failyml'
        self.defaults_file = testpath + 'defaults.yml'
        self.merge_files = [testpath + 'merge1.yml',
                            testpath + 'merge2.yml']
        self.valid_rule_files = [self.valid_rule_file,
                                 self.valid_rule_file2]
        def handle_condition_list(data_list_in, op, negate):
            data_out = (('!' if negate else '') + op
                        + '['  + ','.join(data_list_in) + ']')
            return data_out
        def handle_match(src, fun, inp, negate):
            data_out = (str(src) + ':' + ('!' if negate else '') + str(fun)
                        + '(' + str(inp) + ')')
            return data_out
        self.traverse_functions = {
            'handle_condition_list': handle_condition_list,
            'handle_match': handle_match
        }

    def test_list_rules_files(self):
        rulesglob = "test/testdata/parser/rule*.yml"
        file_list = parser.list_rules_files(rulesglob, recursive=True)
        self.assertIsInstance(file_list, list)
        self.assertEqual(file_list, self.valid_rule_files)

    def test_parse_yaml_file(self):
        yml_docs = parser.parse_yaml_file(self.valid_rule_file)
        self.assertIsInstance(yml_docs, list)
        self.assertEqual(len(yml_docs), 1)
        for yml_doc in yml_docs:
            self.assertIsInstance(yml_doc, dict)

    def test_get_unique_id(self):
        allowed_pattern = re.compile(r'^[a-zA-Z0-9_]+$')
        name_counter = {}
        id1 = parser.get_unique_id(name_counter, string.printable)
        id2 = parser.get_unique_id(name_counter, string.printable)
        self.assertIsInstance(id1, str)
        self.assertIsNotNone(re.search(allowed_pattern, id1))
        self.assertIsInstance(id2, str)
        self.assertIsNotNone(re.search(allowed_pattern, id2))
        self.assertNotEqual(id1, id2)

    def test_extract_from_origin(self):
        scheme, host, port = parser.extract_from_origin('www.example.com')
        self.assertIsInstance(scheme, str)
        self.assertEqual(scheme, 'https')
        self.assertIsInstance(host, str)
        self.assertEqual(host, 'www.example.com')
        self.assertIsInstance(port, str)
        self.assertEqual(port, '443')
        scheme, host, port = parser.extract_from_origin('http://example.com')
        self.assertIsInstance(scheme, str)
        self.assertEqual(scheme, 'http')
        self.assertIsInstance(host, str)
        self.assertEqual(host, 'example.com')
        self.assertIsInstance(port, str)
        self.assertEqual(port, '80')
        scheme, host, port = parser.extract_from_origin('imba://'
                                                        'www.example.com:1337')
        self.assertIsInstance(scheme, str)
        self.assertEqual(scheme, 'imba')
        self.assertIsInstance(host, str)
        self.assertEqual(host, 'www.example.com')
        self.assertIsInstance(port, str)
        self.assertEqual(port, '1337')

    def test_parse_document_v1(self):
        self.maxDiff = None
        domains = {'domains': ['www.example.com', 'site.example.com']}
        rule_foo = {
            'description': 'foo',
            'matches': 'foo_match',
            'prio': 1,
            'actions': 'foo_action'
        }
        rule_bar = {
            'description': 'bar',
            'matches': 'bar',
            'prio': 2,
            'actions': 'bar_action'
        }
        rule_baz = {
            'description': 'baz',
            'matches': 'baz',
            'prio': 3,
            'actions': 'baz_action'
        }
        rule_foo.update(domains)
        rule_bar.update(domains)
        tests = ['yeah', 'ooo']
        yml_doc = {
            'schema_version': 2,
            'rules': [domains.copy(), domains.copy()],
            'tests': tests
        }
        yml_doc['rules'][0].update(rule_foo)
        yml_doc['rules'][1].update(rule_bar)
        exp_parsed_doc = {
            'rules': {
                'www.example.com': [
                    rule_foo,
                    rule_bar
                ],
                'site.example.com': [
                    rule_foo,
                    rule_bar
                ]
            },
            'tests': tests
        }
        parsed_doc = parser.parse_document(yml_doc)
        self.assertDictEqual(parsed_doc, exp_parsed_doc)
        # Test doc with rules having different domains-values
        one_domain = {'domains': ['www.example.com']}
        both_domains = {'domains': ['www.example.com', 'site.example.com']}
        other_domain = {'domains': ['another.example.com']}
        rule_foo.update(one_domain)
        rule_bar.update(both_domains)
        rule_baz.update(other_domain)
        yml_doc = {
            'schema_version': 2,
            'rules': [rule_foo.copy(), rule_bar.copy(), rule_baz.copy()]
        }
        exp_parsed_doc = {
            'rules': {
                'www.example.com': [
                    rule_foo,
                    rule_bar
                ],
                'site.example.com': [
                    rule_bar
                ],
                'another.example.com': [
                    rule_baz
                ]
            },
            'tests': []
        }
        parsed_doc = parser.parse_document(yml_doc)
        self.assertDictEqual(parsed_doc, exp_parsed_doc)

    def test_parse_rules(self):
        # Test merging rule files
        exp_docs = {
            'rules': {
                'example.com': [
                    {
                        '_orm_source_file': self.merge_files[0],
                        '_rule_id': 'foo',
                        'description': 'foo',
                        'domains': ['example.com', 'site.example.com']
                    }, {
                        '_orm_source_file': self.merge_files[0],
                        '_rule_id': 'bar',
                        'description': 'bar',
                        'domains': ['example.com']
                    }, {
                        '_orm_source_file': self.merge_files[1],
                        '_rule_id': 'foo_3',
                        'description': 'foo',
                        'domains': ['example.com']
                    }, {
                        '_orm_source_file': self.merge_files[1],
                        '_rule_id': 'baz',
                        'description': 'baz',
                        'domains': ['example.com']
                    }
                ],
                'site.example.com': [
                    {
                        '_orm_source_file': self.merge_files[0],
                        '_rule_id': 'foo_2',
                        'description': 'foo',
                        'domains': ['example.com', 'site.example.com']
                    }
                ]
            },
            'tests': []
        }
        docs = parser.parse_rules(self.merge_files)
        self.assertEqual(docs, exp_docs)
        # Test https_redirection default
        defaults = {
            'https_redirection': True
        }
        exp_docs = {
            'rules': {
                'example.com': [
                    {
                        '_orm_source_file': self.defaults_file,
                        '_rule_id': 'foo',
                        'description': 'foo',
                        'domains': ['example.com'],
                        'actions': {
                            'https_redirection': True
                        }
                    }, {
                        '_orm_source_file': self.defaults_file,
                        '_rule_id': 'bar',
                        'description': 'bar',
                        'domains': ['example.com'],
                        'actions': {
                            'https_redirection': False
                        }
                    }, {
                        '_orm_source_file': self.defaults_file,
                        '_rule_id': 'lizard',
                        'description': 'lizard',
                        'domains': ['example.com'],
                        'actions': {
                            'https_redirection': True
                        }
                    }, {
                        '_orm_source_file': self.defaults_file,
                        '_rule_id': 'snek',
                        'description': 'snek',
                        'domains': ['example.com'],
                        'actions': {
                            # There should be no https_redirection here
                            'redirect': {
                                'type': 'temporary',
                                'url': 'internet'
                            }
                        }
                    }
                ]
            },
            'tests': []
        }
        docs = parser.parse_rules([self.defaults_file], defaults=defaults)
        self.assertEqual(docs, exp_docs)

    def test_parse_match_values(self):
        for value_type in ("path", "query", "method"):
            ## Test flattening
            exp_tree = {
                'or': [
                    {'match': {
                        'function': 'exact',
                        'input': {
                            'value': 'a'
                        },
                        'source': value_type}},
                    {'match': {
                        'function': 'exact',
                        'input': {
                            'value': 'b'
                        },
                        'source': value_type}},
                    {'match': {
                        'function': 'regex',
                        'input': {
                            'value': 'c'
                        },
                        'source': value_type}},
                    {'match': {
                        'function': 'regex',
                        'input': {
                            'value': 'd'
                        },
                        'source': value_type}}
                ]
            }
            tree = parser.parse_match_values(
                {
                    'exact': ['a', 'b'],
                    'regex': ['c', 'd'],
                },
                value_type
            )
            self.assertEqual(tree, exp_tree)
            ## Test negation
            exp_tree = {
                'not': {
                    'or': [
                        {'match': {
                            'function': 'exact',
                            'input': {
                                'value': 'a'
                            },
                            'source': value_type}}
                    ]
                }
            }
            tree = parser.parse_match_values(
                {
                    'exact': ['a'],
                    'not': True
                },
                value_type
            )
            self.assertEqual(tree, exp_tree)

    def test_parse_match_binary_operator(self):
        # OR
        in_exprs = [
            {'paths': {'exact': ['a']}},
            {'paths': {'exact': ['b']}}
        ]
        exp_tree = {
            'or': [
                {'or': [{'match': {'function': 'exact',
                                   'input': {
                                       'value': 'a'
                                   },
                                   'source': 'path'}}]},
                {'or': [{'match': {'function': 'exact',
                                   'input': {
                                       'value': 'b'
                                   },
                                   'source': 'path'}}]}
            ]
        }
        tree = parser.parse_match_binary_operator('any', in_exprs)
        self.assertEqual(tree, exp_tree)
        # AND
        in_exprs = [
            {'paths': {'exact': ['a']}},
            {'paths': {'exact': ['b']}}
        ]
        exp_tree = {
            'and': [
                {'or': [{'match': {'function': 'exact',
                                   'input': {
                                       'value': 'a'
                                   },
                                   'source': 'path'}}]},
                {'or': [{'match': {'function': 'exact',
                                   'input': {
                                       'value': 'b'
                                   },
                                   'source': 'path'}}]}
            ]
        }
        tree = parser.parse_match_binary_operator('all', in_exprs)
        self.assertEqual(tree, exp_tree)

    def test_parse_match_domains(self):
        in_domains = ['a', 'b']
        exp_tree = {
            'or': [
                {'match': {
                    'source': 'domain',
                    'function': 'exact',
                    'input': 'a'}},
                {'match': {
                    'source': 'domain',
                    'function': 'exact',
                    'input': 'b'}},
            ]
        }
        tree = parser.parse_match_domains(in_domains)
        self.assertEqual(tree, exp_tree)

    def test_create_match_tree(self):
        in_domains = ['example.com']
        in_matches = {'all': [{'paths': {'not': True,
                                         'regex':['foo']}}]}
        exp_tree = {
            'and': [
                {'or': [
                    {'match': {'source': 'domain',
                               'function': 'exact',
                               'input': 'example.com'}}
                ]},
                {'and': [
                    {'not': {'or': [
                        {'match': {
                            'source': 'path',
                            'function': 'regex',
                            'input': {
                                'value': 'foo'
                            }
                        }}
                    ]}}
                ]}
            ]
        }
        tree = parser.create_match_tree(in_matches, in_domains)
        self.assertEqual(tree, exp_tree)

    def test_minify_match_tree(self):
        match_tree = {
            'and': [
                {'match': 'foo'},
                {'or': [
                    {'match': 'bar'}
                ]},
                {'and': [
                    {'match': 'gurka'}
                ]}
            ]
        }
        exp_tree = {
            'and': [
                {'match': 'foo'},
                {'match': 'bar'},
                {'match': 'gurka'}
            ]
        }
        mini_tree = parser.minify_match_tree(match_tree)
        self.assertEqual(mini_tree, exp_tree)
        # Do nothing to this poor tree
        match_tree = {
            'and': [
                {'match': 'foo'},
                {'or': [
                    {'match': 'bar'},
                    {'match': 'baz'}
                ]},
                {'and': [
                    {'match': 'yeah'},
                    {'match': 'boi'}
                ]}
            ]
        }
        mini_tree = parser.minify_match_tree(match_tree)
        self.assertEqual(mini_tree, match_tree)
        # Deep nesting
        match_tree = {
            'or': [{'or': [{'and': [{'or': [{'and': [{'go': '!'}]}]}]}]}]
        }
        exp_tree = {'go': '!'}
        mini_tree = parser.minify_match_tree(match_tree)
        self.assertEqual(mini_tree, exp_tree)

    def test_traverse_match(self):
        match = {
            'source': 'doge',
            'function': 'become',
            'input': 'internet'
        }
        exp_data_out = 'doge:!become(internet)'
        data_out = parser.traverse_match(self.traverse_functions, match, True)
        self.assertEqual(data_out, exp_data_out)

    def test_traverse_condition_list(self):
        match_tree_list = [
            {'match': {'source': 'this',
                       'function': 'does',
                       'input': 'compute'}},
            {'match': {'source': 'this',
                       'function': 'does',
                       'input': 'pute'}}
        ]
        operator = 'dem_puters'
        data_out = parser.traverse_condition_list(self.traverse_functions,
                                                  match_tree_list,
                                                  operator,
                                                  True)
        exp_data_out = '!dem_puters[this:does(compute),this:does(pute)]'
        self.assertEqual(data_out, exp_data_out)

    def test_traverse_match_tree(self):
        match_tree = {
            'and': [
                {'or': [
                    {'match': {'source': 'domain',
                               'function': 'exact',
                               'input': 'example.com'}}
                ]},
                {'and': [
                    {'not': {'or': [
                        {'match': {'source': 'path',
                                   'function': 'regex',
                                   'input': 'foo'}}
                    ]}}
                ]},
                {'not': {'not': {
                    'match': {'source': 'path',
                              'function': 'ends_with',
                              'input': 'yeah'}
                }}}
            ]
        }
        exp_data_out = ('and['
                        'or[domain:exact(example.com)],'
                        'and[!or[path:regex(foo)]],'
                        'path:ends_with(yeah)'
                        ']')
        data_out = parser.traverse_match_tree(self.traverse_functions,
                                              match_tree)
        self.assertEqual(data_out, exp_data_out)

if __name__ == '__main__':
    unittest.main()
