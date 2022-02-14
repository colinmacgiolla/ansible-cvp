#!/usr/bin/python
# coding: utf-8 -*-
#
# GNU General Public License v3.0+
#
# Copyright 2019 Arista Networks AS-EMEA
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: cv_change_control_v3
version_added: TBD
author: EMEA AS Team (@aristanetworks)
short_description: Change Control management with Cloudvision
description:
  - CloudVision Portal Change Control Module.
  - ''
options:
  - TODO


'''

EXAMPLES = r'''
---
TODO
'''

# Required by Ansible and CVP
import logging
from ansible.module_utils.basic import AnsibleModule
import ansible_collections.arista.cvp.plugins.module_utils.logger   # noqa # pylint: disable=unused-import
from ansible_collections.arista.cvp.plugins.module_utils import tools_cv
from ansible_collections.arista.cvp.plugins.module_utils.change_tools import CvChangeControlTools

MODULE_LOGGER = logging.getLogger('arista.cvp.cv_change_control_v3')
MODULE_LOGGER.info('Start cv_change_control_v3 module execution')


def main():
    """
    main entry point for module execution.
    """
    argument_spec = dict(
        name=dict(type='str'),
        tasks=dict(type="list", elements='str'),
        mode=dict(type='str', choices=['parallel','series']),
        thing=dict(default='change', type='str', choices=['change', 'stage', 'task', 'action']),
        state=dict(default='get', type='str', choices=['get', 'set', 'remove']),
    )

    ansible_module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    # Instantiate ansible results
    result = dict(changed=False, data={}, failed=False)
    warnings = []

    MODULE_LOGGER.info('starting module cv_change_control_v3')
    if ansible_module.check_mode:
        MODULE_LOGGER.warning('! check_mode is enable')
        # module.exit_json(changed=True)

    if not tools_cv.HAS_CVPRAC:
        ansible_module.fail_json(
            msg='cvprac required for this module. Please install using pip install cvprac'
        )

    # Create CVPRAC client
    cv_client = tools_cv.cv_connect(ansible_module)

    result = dict(changed=False)

    # Instantiate the image class
    cv_cc = CvChangeControlTools(
        cv_connection=cv_client,
        ansible_module=ansible_module,
        check_mode=ansible_module.check_mode
    )

    result['changed'], result['data'], warnings = cv_cc.module_action(**ansible_module.params)
    MODULE_LOGGER.warning(warnings)

    ansible_module.exit_json(**result)


if __name__ == '__main__':
    main()
