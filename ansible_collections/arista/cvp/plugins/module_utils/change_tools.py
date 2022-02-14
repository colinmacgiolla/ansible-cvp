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
        self.cvp_version = self.__cv_client.api.get_cvp_info()['version']
        self.apiversion = self.__cv_client.apiversion
        
    def __index_cc__(self):
        MODULE_LOGGER.debug('Indexing Change Controls')
        self.__cc_index.clear()
        
        for entry in self.change_controls['data']:
            self.__cc_index.append( (entry['result']['value']['change']['name'],entry['result']['value']['key']['id']) )

        
            
    def _find_id_by_name(self, name):
        cc_id = []
        cc_id = list( filter(lambda x:name in x, self.__cc_index) )
        MODULE_LOGGER.debug('%d changes found' % len(cc_id))
        return cc_id
            
        
    def get_all_change_controls(self):
        cc_list = []
        legacy = True
        MODULE_LOGGER.debug('Collecting Change controls')
        
        if self.apiversion < 3.0:
            MODULE_LOGGER.debug('Trying legacy API call')
            cc_list = self.__cv_client.api.get_change_controls()
        
        else:
            # Rewrite on cvprac > 1.0.7
            MODULE_LOGGER.debug('Using resource API call')
            cc_list = self.__cv_client.get('/api/resources/changecontrol/v1/ChangeControl/all')

        if len(cc_list) > 0:
            self.change_controls = cc_list
            self.__index_cc__()
            return True

        return None

    
    def get_change_control(self, cc_id):
        
        MODULE_LOGGER.debug('Collecting change control: %s' % cc_id)
        if self.apiversion < 3.0:
            MODULE_LOGGER.debug('Using legacy API call')
            change = self.__cv_client.api.get_change_control_info(cc_id)
        else:
            # Rewrite on cvprac > 1.0.7
            params = 'key.id={}'.format(cc_id)
            cc_url = '/api/resources/changecontrol/v1/ChangeControl?' + params
            change = self.__cv_client.get(cc_url)
            
        return change
    
        
    
    
    def module_action(self, tasks:List[str], thing:dict, name:str = None, mode:str = "series", state:str = "get", change_id:List[str] = None ):
        
        changed = False
        data = dict()
        warnings = list()
        
        self.get_all_change_controls()
        
        if state == "get":
            if name is None:
                return changed, {'change_controls': self.change_controls}, warnings
            else:
                cc_list = []
                cc_id_list = self._find_id_by_name(name)
                for change in cc_id_list:
                    MODULE_LOGGER.debug('Looking up change: %s with ID: %s' % (change[0],change[1]) )
                    cc_list.append(self.get_change_control(change[1]) )

                return changed, {'change_controls:': cc_list  }, warnings
            
            
        if state == "remove":
            MODULE_LOGGER.debug("Deleting change control")
            if change_id is not None:
                if name is not None:
                    warnings.append("Deleting CC IDs takes precedence over deleting named CCs. Only the provided CCids will be deleted")
                try:
                    changes = self.__cv_client.api.delete_change_controls(change_id)
                    MODULE_LOGGER.debug("Response to delete request was: %s" % changes)
                    if len(changes) > 0:
                        changed = True
                    else:
                        warnings.append('No changes made in delete request')
                except Exception as e:
                    self.__ansible.fail_json(msg="{0}".format(e))
                    
                return changed,{'remove':changes}, warnings
            
            elif name is not None:
                cc_list = self._find_id_by_name(name)
                if len(cc_list) == 0:
                    warnings.append("No matching change controls found for %s" % name)
                    return changed, {'search': name}, warnings
                elif len(cc_list) > 1:
                    warnings.append("Multiple changes (%d) found matching name: %s" % (len(cc_list),name ) )
                    e = "Deleting multiple CCs by name is not supported at this time"
                    self.__ansible.fail_json(msg="{0}".format(e))
                    return changed, {'matches': cc_list}, warnings
                else:
                    try:
                        changes = self.__cv_client.api.delete_change_controls(change_id)
                        if len(changes) > 0:
                            changed = True
                        else:
                            warnings.append('No changes made in delete request')
                    except Exception as e:
                        self.__ansible.fail_json(msg="{0}".format(e))
            else:
                e = "Unable to delete change control. Change name or change_id(s) must be specified"
                self.__ansible.fail_json(msg="{0}".format(e))
                    
        else:
            pass
                
            
        
        
        
        return changed, data, warnings