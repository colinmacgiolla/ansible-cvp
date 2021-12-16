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
__metaclass__ = type

import traceback
import logging
import os
from ansible.module_utils.basic import AnsibleModule
import ansible_collections.arista.cvp.plugins.module_utils.logger   # noqa # pylint: disable=unused-import
from ansible_collections.arista.cvp.plugins.module_utils.response import CvApiResult, CvManagerResult, CvAnsibleResponse
try:
    from cvprac.cvp_client import CvpClient  # noqa # pylint: disable=unused-import
    from cvprac.cvp_client_errors import CvpApiError, CvpRequestError  # noqa # pylint: disable=unused-import
    HAS_CVPRAC = True
except ImportError:
    HAS_CVPRAC = False
    CVPRAC_IMP_ERR = traceback.format_exc()


MODULE_LOGGER = logging.getLogger('arista.cvp.image_tools')
MODULE_LOGGER.info('Start image_tools module execution')


class CvImageTools():
    """
    CvImageTools Class to manage Cloudvision software images and byndles
    """

    def __init__(self, cv_connection, ansible_module: AnsibleModule = None, check_mode: bool = False):
        self.__cv_client = cv_connection
        self.__ansible = ansible_module
        self.__check_mode = check_mode
        self._images = list()
        self._imageBundles = list()
        self.refresh_cvp_image_data()
 
 
    def __get_images(self):
        images = []
        
        MODULE_LOGGER.debug('  -> Collecting images')
        images = self.__cv_client.api.get_images()['data']
        MODULE_LOGGER.debug(images)
        if len(images) > 0:
            return images
        return None


    def __get_image_bundles(self):
        imageBundles = []
        MODULE_LOGGER.debug('  -> Collecting image bundles')
        imageBundles = self.__cv_client.api.get_image_bundles()['data']
        MODULE_LOGGER.debug(imageBundles)
        if len(imageBundles) > 0:
            return imageBundles
        return None


    def refresh_cvp_image_data(self):
        images = self.__get_images()
        bundles = self.__get_image_bundles()

        return images, bundles


    def is_image_present(self, image):
        """
        Checks if a named image is present.
    
        Parameters
        ----------
        image: str
           The name of the software image
    
        Returns
        -------
        Bool:
            True if present, False if not
        """
    
        for entry in self._images:
            if entry["imageFileName"] == os.path.basename(image):
                return True            
        return False


    def does_bundle_exist(self, bundle):
        """
        Checks if a named bundle already exists

        Parameters
        ----------
        bundle : str
            Name of software image bundle.

        Returns
        -------
        Bool:
            True if present, False if not
        """
        for entry in self._imageBundles:
            if entry["name"] == bundle:
                return True
        return False


    def get_bundle_key(self, bundle):
        """
        Gets the key for a given bundle

        Parameters
        ----------
        bundle : str
            Ansible module.

        Returns
        -------
        str:
            The string value equivelent to the bundle key,
            or None if not found
        """
        for entry in self._imageBundles:
            if entry["name"] == bundle:
                return entry["key"]
        return None


    def build_image_list(self, image_list):
        """
        Builds a list of the image data structures, for a given list of image names.

        Parameters
        ----------
        image_list : list
            List of software image names

        Returns
        -------
        List:
            Returns a list of images, with complete data or None in the event of failure
        """
        internal_image_list = list()
        image_data = None
        success = True
        
        for entry in image_list:
            for image in self._images:
                if image["imageFileName"] == entry:
                    image_data = image
                    
            if image_data is not None:
                internal_image_list.append(image_data)
                image_data = None
            else:
                success = False
        
        if success:
            return image_list
        else:
            return None


    def module_action(self, image: str, image_list: list, bundle_name: str, mode: str="images", action: str = "get" ):
        """
        Method to call the other modules.

        Parameters
        ----------
        image : str
            The name (and/or path) of the software image.
        image_list: list
            List of software image names (used for image bundles)
        bundle_name: str
            The name of the software image bundle
        mode: str
            Default "images". Can run in "images" or "bundles" mode
        action: str
            Default "get". Can add/update, get or remove images or image bundles

        Returns
        -------
        dict:
        result with tasks and information.
        """
        changed = False
        data = dict()
        warnings = list()
        
        
        cvp_images = list()
        cvp_image_bundles = list()

        
        
        if mode == "images":
            if action == "get":
                cvp_images, cvp_image_bundles = self.refresh_cvp_image_data()
                
                
                return changed, {'images':self._images,'image_bundle': self._imageBundles } , warnings

            
            elif action == "add" and self.__check_mode == False:
                if len(image) > 0 and os.path.exists(image):
                    if self.is_image_present(image) is False:
                        MODULE_LOGGER.debug("Image not present. Trying to add.")
                        try:
                            data = self.__cv_client.api.add_image(image)
                            cvp_images, cvp_image_bundles = self.refresh_cvp_image_data()
                            MODULE_LOGGER.debug(data)
                            changed = True
                        except Exception as e:
                            self.__ansible.module.fail_json( msg="%s" % str(e))
                    else:
                        self.__ansible.module.fail_json(msg="Same image name already exists on the system")
                else:
                    self.__ansible.module.fail_json(msg="Specified file ({}) does not exist".format(image) )
            else:
                self.__ansible.module.fail_json(msg="Deletion of images through API is not currently supported")


        # So we are dealing with bundles rather than images
        else:
            if action == "get":
                data = self.refresh_cvp_image_data()
                return changed, self._imageBundles, warnings
            
            elif action == "add" and self.__check_mode == False:
                # There are basically 2 actions - either we are adding a new bundle (save)
                # or changing an existing bundle (update)
                if self.does_bundle_exist(bundle_name):
                    warnings.append('Note that when updating a bundle, all the images to be used in the bundle must be listed')
                    key = self.get_bundle_key(bundle_name)
                    images = self.build_image_list(image_list)
                    if images is not None:
                        try:
                            response = self.__cv_client.api.update_image_bundle( key, bundle_name, images )
                            changed = True
                            data = response['data']
                            cvp_images, cvp_image_bundles = self.refresh_cvp_image_data()
                        except Exception as e:
                            self.__ansible.module.fail_json( msg="%s" % str(e) )
                    
                    else:
                        self.__ansible.module.fail_json(msg="Unable to update bundle - images not present on server")
                            
                    return changed, data, warnings
                        

                else:
                    images = self.build_image_list(image_list)
                    if images is not None:
                        try:
                            response = self.__cv_client.api.save_image_bundle( bundle_name, images )
                            changed = True
                            data = response['data']
                            cvp_images, cvp_image_bundles = self.refresh_cvp_image_data()
                        except Exception as e:
                            self.__ansible.module.fail_json( msg="%s" % str(e) )

                    else:
                        self.__ansible.module.fail_json(msg="Unable to create bundle - images not present on server")
                    
                    return changed, data, warnings
                
            elif action == "remove" and self.__check_mode == False:
                warnings.append('Note that deleting the image bundle does not delete the images')
                if self.does_bundle_exist(bundle_name):
                    key = self.get_bundle_key(bundle_name)
                    try:
                        response = self.__cv_client.client.api.delete_image_bundle(key,bundle_name )
                        changed = True
                        data = response['data']
                        cvp_images, cvp_image_bundles = self.refresh_cvp_image_data()
                    except Exception as e:
                            self.__ansible.module.fail_json( msg="%s" % str(e) )
                else:
                    self.__ansible.module.fail_json(msg="Unable to delete bundle - not found")
                    
            else:
                # You have reached a logically impossible state
                warnings.append("You have reached a logically impossible state")
                
        return changed, data, warnings