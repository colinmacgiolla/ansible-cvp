#!/usr/bin/env python
# coding: utf-8 -*-
#
# GNU General Public License v3.0+
#
# Copyright 2021 Arista Networks AS-EMEA
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

from __future__ import (absolute_import, division, print_function)
import string
__metaclass__ = type

import traceback
import logging
import os
from typing import List
from ansible.module_utils.basic import AnsibleModule
import ansible_collections.arista.cvp.plugins.module_utils.logger   # noqa # pylint: disable=unused-import
from ansible_collections.arista.cvp.plugins.module_utils.response import CvApiResult, CvManagerResult, CvAnsibleResponse  # noqa # pylint: disable=unused-import
try:
    from cvprac.cvp_client import CvpClient  # noqa # pylint: disable=unused-import
    from cvprac.cvp_client_errors import CvpApiError, CvpRequestError  # noqa # pylint: disable=unused-import
    HAS_CVPRAC = True
except ImportError:
    HAS_CVPRAC = False
    CVPRAC_IMP_ERR = traceback.format_exc()


MODULE_LOGGER = logging.getLogger('arista.cvp.change_tools')
MODULE_LOGGER.info('Start change_tools module execution')


class CvChangeControlTools():
    """
    CvImageTools Class to manage Cloudvision Change Controls
    """
    def __init__(self, cv_connection, ansible_module: AnsibleModule = None, check_mode: bool = False):
        self.__cv_client = cv_connection
        self.__ansible = ansible_module
        self.__check_mode = check_mode
        self.__cc_index = []
        
    def __index_cc__(self):
        MODULE_LOGGER.debug('Indexing Change Controls')
        for entry in self.change_controls['data']:
            self.__cc_index.append( (entry['result']['value']['change']['name'],entry['result']['value']['key']['id']) )

            
    def find_id_by_name(self, name):
        cc_id = []
        cc_id = list(filter(lambda x:name in x, self.__cc_index))
        return cc_id
            
        
    def get_all_change_controls(self):
        cc_list = []
        legacy = True
        MODULE_LOGGER.debug('Collecting Change controls')
        
        MODULE_LOGGER.debug('Trying legacy API call')
        cc_list = self.__cv_client.api.get_change_controls()
        cc_detailed_list = []
        
        if cc_list is None:
            legacy = False
            MODULE_LOGGER.debug('Using resource API call')
            cc_list = self.__cv_client.get('/api/resources/changecontrol/v1/ChangeControl/all')
            
            
        if len(cc_list) > 0:
            self.change_controls = cc_list
            self.__index_cc__()
            return True
        return False
    
    def get_change_control(self, cc_id):
        change = self.__cv_client.get_change_control_info(cc_id)
        if change is None:
            params = 'key.id={}'.format(cc_id)
            cc_url = '/api/resources/changecontrol/v1/ChangeControl?' + params
            change = self.__cv_client.get(cc_url)
        return change
    
        
    
    
    def module_action(self, tasks:List[str], thing:dict, name:str = None, mode:str = "series", action:str = "get" ):
        
        changed = False
        data = dict()
        warnings = list()
        
        self.get_all_change_controls()
        
        if action == "get":
            if name is None:
                return changed, {'change_controls': self.change_controls}, warnings
            else:
                cc_list = []
                cc_id_list = self.find_id_by_name(name)
                for change in cc_id_list:
                    cc_list.append(self.get_change_control(change) )
                    
                return changed, {'change_controls:': cc_list  }, warnings
        
        
        
        
        
        return changed, data, warnings