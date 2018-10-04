########
# Copyright (c) 2013 GigaSpaces Technologies Ltd. All rights reserved
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

import copy
import json

from dsl_parser import (functions,
                        exceptions,
                        scan,
                        models,
                        parser,
                        multi_instance)
from dsl_parser.multi_instance import modify_deployment


__all__ = [
    'modify_deployment'
]


def parse_dsl(dsl_location,
              resources_base_path,
              resolver=None,
              validate_version=True,
              additional_resources=(),
              return_resolved_blueprint=False):
    return parser.parse_from_path(
            dsl_file_path=dsl_location,
            resources_base_path=resources_base_path,
            resolver=resolver,
            validate_version=validate_version,
            additional_resource_sources=additional_resources,
            return_resolved_blueprint=return_resolved_blueprint)


def _set_plan_inputs(plan, inputs=None):
    inputs = inputs if inputs else {}
    # Verify inputs satisfied
    missing_inputs = []
    for input_name, input_def in plan['inputs'].iteritems():
        if input_name in inputs:
            try:
                str(json.dumps(inputs[input_name], ensure_ascii=False))
            except UnicodeEncodeError:
                raise exceptions.DSLParsingInputTypeException(
                    exceptions.ERROR_INVALID_CHARS,
                    'Illegal characters in input: {0}. '
                    'Only valid ascii chars are supported.'.format(input_name))
        else:
            if 'default' in input_def and input_def['default'] is not None:
                inputs[input_name] = input_def['default']
            else:
                missing_inputs.append(input_name)

    if missing_inputs:
        raise exceptions.MissingRequiredInputError(
            "Required inputs {0} were not specified - expected "
            "inputs: {1}".format(missing_inputs, plan['inputs'].keys())
        )
    # Verify all inputs appear in plan
    not_expected = [input_name for input_name in inputs.keys()
                    if input_name not in plan['inputs']]
    if not_expected:
        raise exceptions.UnknownInputError(
            "Unknown inputs {0} specified - "
            "expected inputs: {1}".format(not_expected,
                                          plan['inputs'].keys()))

    plan['inputs'] = inputs


def _process_functions(plan):
    handler = functions.plan_evaluation_handler(plan)
    scan.scan_service_template(
        plan, handler, replace=True, search_secrets=True)


def _validate_secrets(plan, get_secret_method):
    if 'secrets' not in plan:
        return

    # Mainly for local workflow that doesn't support secrets
    if get_secret_method is None:
        raise exceptions.UnsupportedGetSecretError(
            "The get_secret intrinsic function is not supported"
        )

    invalid_secrets = []
    for secret_key in plan['secrets']:
        try:
            get_secret_method(secret_key)
        except Exception as exception:
            if hasattr(exception, 'status_code')\
                    and exception.status_code == 404:
                invalid_secrets.append(secret_key)
            else:
                raise
    plan.pop('secrets')

    if invalid_secrets:
        raise exceptions.UnknownSecretError(
            "Required secrets {0} don't exist in this tenant"
            .format(invalid_secrets)
        )


def prepare_deployment_plan(
        plan, get_secret_method=None, inputs=None, **kwargs):
    """
    Prepare a plan for deployment
    """
    plan = models.Plan(copy.deepcopy(plan))
    _set_plan_inputs(plan, inputs)
    _process_functions(plan)
    _validate_secrets(plan, get_secret_method)
    return multi_instance.create_deployment_plan(plan)
