﻿from common.utilites.common_utils import first_or_default
from models.VCenterConnectionDetails import VCenterConnectionDetails
from models.VCenterInventoryPathAttribute import VCenterInventoryPathAttribute
from models.VCenterTemplateModel import *
from models.VMClusterModel import *


class VCenterImageModel(object):
    pass


class CloudshellDataRetrieverService:
    PATH_DELIMITER = "/"

    def get_vcenter_image_attribute_data(self, resource_attributes):
        model = VCenterImageModel()
        model.auto_power_on = resource_attributes['Auto Power On']
        model.auto_power_off = resource_attributes['Auto Power Off']
        model.vcenter_image = resource_attributes['vCenter Image']
        model.vcenter_image_arguments = resource_attributes['vCenter Image Arguments']
        model.vcenter_name = resource_attributes['vCenter Name']
        model.vm_cluster = resource_attributes['VM Cluster']
        model.vm_location = resource_attributes['VM Location']
        model.vm_resource_pool = resource_attributes['VM Resource Pool']
        model.vm_storage = resource_attributes['VM Storage']
        model.wait_for_ip = resource_attributes['Wait for IP']
        return

    def getVCenterTemplateAttributeData(self, resource_attributes):
        """ get vCenter resource name, template name, template folder from 'vCenter Template' attribute """

        template_att = resource_attributes.attributes["vCenter Template"]
        template_components = template_att.split(self.PATH_DELIMITER)

        return VCenterTemplateModel(
                vcenter_resource_name=template_components[0],
                vm_folder=self.PATH_DELIMITER.join(template_components[1:-1]),
                template_name=template_components[-1])

    def getPowerStateAttributeData(self, resource_attributes):
        """
        get power state attribute data 
        :rtype: boolean
        """
        power_state = False
        if resource_attributes.attributes["VM Power State"].lower() == "true":
            power_state = True
        return power_state

    def getVMClusterAttributeData(self, resource_attributes):
        """ 
        get cluster and resource pool from 'VM Cluster' attribute 
        if attribute is empty than return None as values
        :rtype VMClusterModel:
        """
        result = VMClusterModel(None, None)

        storage_att = resource_attributes.attributes["VM Cluster"]
        if storage_att:
            storage_att_components = storage_att.split("/")
            if len(storage_att_components) == 2:
                result.cluster_name = storage_att_components[0]
                result.resource_pool = storage_att_components[1]

        return result

    def getVMStorageAttributeData(self, resource_attributes):
        """
        get datastore from 'VM Storage' attribute
        :rtype str:
        """
        datastore_name = resource_attributes.attributes["VM Storage"]
        if not datastore_name:
            datastore_name = None
        return datastore_name

    def getVCenterConnectionDetails(self, session, vCenter_resource_details):
        """
        Return a dictionary with vCenter connection details. Methods receives a ResourceDetails object of a vCenter resource
        and retrieves the connection details from its attributes.

        :param vCenter_resource_details:   the ResourceDetails object of a vCenter resource
        :param session:                    the cloushell api session, its needed in order to decrypt the password
        """
        user = vCenter_resource_details.attributes["User"]
        encrypted_pass = vCenter_resource_details.attributes["Password"]
        vcenter_url = vCenter_resource_details.address
        password = session.DecryptPassword(encrypted_pass).Value

        return VCenterConnectionDetails(vcenter_url, user, password)

    def get_vcenter_connection_details(self, session, vcenter_resource_model, vcenter_resource_instance):
        """
        Return a dictionary with vCenter connection details. Methods receives a ResourceDetails object of a vCenter resource
        and retrieves the connection details from its attributes.

        :param session:                    the cloushell api session, its needed in order to decrypt the password
        :param vcenter_resource_model:   the VMwarevCenterResourceModel object of a vCenter resource
        :param vcenter_resource_instance:   the ResourceDetails object of a vCenter resource
        """
        user = vcenter_resource_model.user
        encrypted_pass = vcenter_resource_model.password
        vcenter_url = vcenter_resource_instance.address
        password = session.DecryptPassword(encrypted_pass).Value

        return VCenterConnectionDetails(vcenter_url, user, password)

    # obsolete
    def getVCenterInventoryPathAttributeData(self, resource_attributes):
        """ get vCenter resource name & virtual machine folder path """

        path_att = resource_attributes.attributes["vCenter Inventory Path"]
        path_components = path_att.split("/")

        vm_folder = ""
        if len(path_components) > 1:
            vm_folder = "/".join(path_components[1:])

        return VCenterInventoryPathAttribute(
            vCenter_resource_name=path_components[0],
            vm_folder=vm_folder
        )
