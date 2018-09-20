########
# Copyright (c) 2018 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

from dsl_parser import (constants,
                        exceptions)
from dsl_parser.tests.abstract_test_parser import AbstractTestParser


class TestSubstitutionMapping(AbstractTestParser):
    BASE_BLUEPRINT = """
node_types:
    cloudify.nodes.Compute:
        properties:
            x:
                default: y
node_templates: {}
    """

    def test_successful_empty_mapping(self):
        yaml = """
node_templates: {}
substitution_mapping:
"""
        self.parse(yaml)

    def test_node_template_broken_schema(self):
        yaml = """
node_templates: {}
substitution_mapping:
    node_type: 12
"""
        self.assertRaises(exceptions.DSLParsingFormatException,
                          self.parse, yaml)

    def test_basic_definition(self):
        yaml = self.BASE_BLUEPRINT + """
substitution_mapping:
    node_type: cloudify.nodes.Compute
"""
        parsed = self.parse(yaml)
        node_type_to_sub = parsed[constants.SUBSTITUTION_MAPPING]['node_type']
        self.assertEqual(node_type_to_sub, 'cloudify.nodes.Compute')

    def test_not_existing_node_type(self):
        yaml = """
node_templates: {}
substitution_mapping:
    node_type: cloudify.nodes.Compute
"""
        self.assertRaises(exceptions.DSLParsingLogicException,
                          self.parse, yaml)
