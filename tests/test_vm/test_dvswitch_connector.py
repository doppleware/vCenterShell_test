import uuid
from unittest import TestCase

from mock import Mock, MagicMock

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

from common.vcenter.vmomi_service import pyVmomiService
from common.logger.service import LoggingService
from common.vcenter.task_waiter import SynchronousTaskWaiter
from models.VCenterConnectionDetails import VCenterConnectionDetails
from tests.utils.testing_credentials import TestCredentials
from vCenterShell.network.dvswitch.creator import DvPortGroupCreator
from vCenterShell.vm.dvswitch_connector import *
from vCenterShell.vm.portgroup_configurer import VirtualMachinePortGroupConfigurer
from pyVim.connect import SmartConnect, Disconnect
from common.logger.service import LoggingService
from common.utilites.debug import print_attributes
from models.VCenterConnectionDetails import VCenterConnectionDetails
from tests.utils.testing_credentials import TestCredentials
from common.vcenter.task_waiter import SynchronousTaskWaiter
from vCenterShell.commands.disconnect_dvswitch import VirtualSwitchToMachineDisconnectCommand
from vCenterShell.vm.vnic_to_network_mapper import VnicToNetworkMapper
from vCenterShell.network.dvswitch.name_generator import DvPortGroupNameGenerator
from vCenterShell.network.vnic.vnic_service import VNicService
from vCenterShell.vm.portgroup_configurer import *



class TestVirtualSwitchToMachineConnector(TestCase):
    LoggingService("CRITICAL", "DEBUG", None)

    def test_connect(self):
        # Arrange
        si = Mock()

        py_vmomi_service = Mock()
        py_vmomi_service.connect = Mock(return_value=si)


        dv_port_group_creator = MagicMock()
        virtual_machine_port_group_configurer = MagicMock()
        vlan_spec = Mock()
        virtual_switch_to_machine_connector = VirtualSwitchToMachineConnector(dv_port_group_creator,
                                                                              virtual_machine_port_group_configurer)

        vm = Mock()

        network_map = Mock()
        network_map.dv_port_name = 'dv_port_name'
        network_map.dv_switch_name = 'dvSwitch'
        network_map.dv_switch_path = 'QualiSB'
        network_map.port_group_path = 'QualiSB'
        network_map.vlan_id = '100'
        network_map.vlan_spec = 'Access'
        # Act
        virtual_switch_to_machine_connector.connect_by_mapping(si, vm, [network_map], Mock(spec=vim.Network))

    def integrationtest(self):
        resource_connection_details_retriever = Mock()
        credentials = TestCredentials()
        resource_connection_details_retriever.connection_details = Mock(
                return_value=VCenterConnectionDetails(credentials.host, credentials.username, credentials.password))
        py_vmomi_service = pyVmomiService(SmartConnect, Disconnect)
        synchronous_task_waiter = SynchronousTaskWaiter()
        dv_port_group_creator = DvPortGroupCreator(py_vmomi_service, synchronous_task_waiter)

        pg_name_generator = DvPortGroupNameGenerator
        vnic_to_network_mapper = VnicToNetworkMapper(pg_name_generator)
        virtual_machine_port_group_configurer = VirtualMachinePortGroupConfigurer(py_vmomi_service,
                                                                                  synchronous_task_waiter,
                                                                                  vnic_to_network_mapper,
                                                                                  VNicService())

        virtual_switch_to_machine_connector = VirtualSwitchToMachineConnector(dv_port_group_creator,
                                                                              virtual_machine_port_group_configurer)

        si = py_vmomi_service.connect(credentials.host, credentials.username,
                                      credentials.password,
                                      credentials.port)



        virtual_machine_path = 'Boris'
        virtual_machine_name = 'boris1'
        vm = py_vmomi_service.get_obj(si.content, [vim.VirtualMachine], virtual_machine_name)
        vm_uuid = vm.config.uuid
        #vm_uuid = self.get_vm_uuid(py_vmomi_service, si, virtual_machine_name)
        port_group_path = 'QualiSB'
        dv_switch_path = 'QualiSB'
        dv_switch_name = 'dvSwitch'
        dv_port_name = 'boris_group59'

        # Act
        # virtual_switch_to_machine_connector.connect(virtual_machine_name,
        #                                             dv_switch_path,
        #                                             dv_switch_name,
        #                                             dv_port_name,
        #                                             vm_uuid,
        #                                             port_group_path,
        #                                             59,
        #                                             vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec())
        #
