import unittest

from greenery.fsm import fsm

import orm.validator as validator

class ValidateRulesTest(unittest.TestCase):
    #pylint:disable=too-many-instance-attributes
    def setUp(self):
        self.testpath = 'test/testdata/validator/'
        self.valid_rule = self.testpath + 'rule.yml'
        self.invalid_collision = self.testpath + 'invalid_collision.yml'
        self.invalid_schema = self.testpath + 'invalid_schema.yml'
        self.invalid_yaml = self.testpath + 'invalid_yaml.yml'
        self.notfound = self.testpath + '__notfound'
        self.ignore_case = self.testpath + 'ignore_case.yml'
        self.multiple_domain_default = (self.testpath
                                        + 'multiple_domain_default.yml')
        self.domain_default_false = (self.testpath
                                     + 'domain_default_false.yml')
        self.valid_globals = self.testpath + 'valid_globals.yml'
        self.invalid_globals = self.testpath + 'invalid_globals.yml'

    def test_lego_ignore_case(self):
        exp = ('[yY][eE][aA][hH]\\[[bB][oO][iI]\\]'
               '[tT][hH][iI][sS][rRa-eA-EgG\\-eExX][!]')
        out = validator.lego_ignore_case('yeAh\\[boi\\]this[ra-eg\\-ex][!]')
        self.assertEqual(exp, out)
        # Do not convert weird non-ascii character ranges.
        exp = ('[a-ö][$-f]')
        out = validator.lego_ignore_case('[a-ö][$-f]')
        self.assertEqual(exp, out)

    def test_ignore_case(self):
        pass

    def test_validate_rule_files(self):
        r = validator.validate_rule_files(yml_files=[self.valid_rule])
        self.assertEqual(r, True, "Check valid rule file")

        r = validator.validate_rule_files(yml_files=[self.invalid_schema])
        self.assertEqual(r, False, "Check invalid rule file schema")

    def test_validate_globals_file(self):
        r = validator.validate_globals_file(globals_file=self.valid_globals)
        self.assertEqual(r, True, "Check valid globals file")

        r = validator.validate_globals_file(globals_file=self.invalid_globals)
        self.assertEqual(r, False, "Check invalid globals file schema")

    def test_validate_rule_schema(self):
        r = validator.validate_rule_schema(source_file=self.valid_rule)
        self.assertEqual(r, True, "Check for valid schema")

        r = validator.validate_rule_schema(source_file=self.invalid_schema)
        self.assertEqual(r, False, "Check for invalid schema")

    def test_validate_rule_constraints(self):
        r = validator.validate_rule_constraints(yml_files=[self.valid_rule])
        self.assertEqual(r, True, "Constraint check with valid ORM file")
        r = validator.validate_rule_constraints(yml_files=
                                                [self.invalid_collision])
        self.assertEqual(r, False, "Constraint check with invalid ORM file")
        r = validator.validate_rule_constraints(yml_files=[self.ignore_case])
        self.assertEqual(r, False, "Constraint check with ignore_case "
                         "collision in invalid ORM file")
        r = validator.validate_rule_constraints(yml_files=[
            self.multiple_domain_default
        ])
        self.assertEqual(r, False, "Constraint check with invalid ORM file "
                         "due to multiple domain_default")
        r = validator.validate_rule_constraints(yml_files=[
            self.domain_default_false
        ])
        self.assertEqual(r, False, "Constraint check with invalid ORM file "
                         "due to 'domain_default: False'")

    def test_get_schema(self):
        yml_file = 'superfile'
        yml_doc_without_version = {'good': 'stuff'}
        with self.assertRaises(validator.ORMSchemaException):
            validator.get_schema(yml_file, yml_doc_without_version)
        yml_doc_unknown_version = {'schema_version': 'is not known'}
        with self.assertRaises(validator.ORMSchemaException):
            validator.get_schema(yml_file, yml_doc_unknown_version)
        for schema_type in validator.orm_schemas:
            for schema_version in validator.orm_schemas[schema_type]:
                yml_doc = {'schema_version': schema_version}
                orm_schema = validator.get_schema(yml_file,
                                                  yml_doc,
                                                  schema_type)
                self.assertIsInstance(orm_schema, dict)

    def test_get_match_path_fsm(self):
        match_tree = {
            'and': [
                {'or': [
                    {'not': {'and': [
                        {'match': {
                            'source': 'path',
                            'function': 'regex',
                            'input': {
                                'value': 'imba'
                            }
                        }}
                    ]}}
                ]},
                {'not': {'not': {
                    'match': {
                        'source': 'path',
                        'function': 'begins_with',
                        'input': {
                            'value': 'yeah'
                        }
                    }
                }}}
            ]
        }
        fsm_obj = validator.get_match_path_fsm(match_tree)
        self.assertIsInstance(fsm_obj, fsm)
        # Test match tree without any path matches
        match_tree = {
            'match': {'source': 'domain',
                      'function': 'exact',
                      'input': 'example.com'}
        }
        fsm_obj = validator.get_match_path_fsm(match_tree)
        self.assertIsInstance(fsm_obj, fsm)

if __name__ == '__main__':
    unittest.main()
