from pyVmomi import vim

from common.logger import getLogger
from common.vcenter.vmomi_service import *
from vCenterShell.network.vnic.common import vnic_compose_empty, vnic_attached_to_network

from common.logger import getLogger
logger = getLogger("vCenterCommon")



# class VirtualMachinePortGroupConfigurer(object):
#     def __init__(self, pyvmomi_service, synchronous_task_waiter):
#         self.pyvmomi_service = pyvmomi_service
#         self.synchronous_task_waiter = synchronous_task_waiter
#
#     def configure_port_group_on_vm(self, service_instance,
#                                    virtual_machine_path,
#                                    vm_uuid,
#                                    port_group_path,
#                                    port_group_name):
#
#         logger.debug("virtual machine path {} vmUUID {}".format(virtual_machine_path, vm_uuid))
#         vm = self.pyvmomi_service.find_by_uuid(service_instance, vm_uuid, True)
#         # vm = self.pyvmomi_service.find_vm_by_name(service_instance, virtual_machine_path, virtual_machine_name)
#         # This code is for changing only one Interface. For multiple Interface
#         # Iterate through a loop of network names.
#         device_change = []
#         for device in vm.config.hardware.device:
#             if isinstance(device, vim.vm.device.VirtualEthernetCard):
#                 nicspec = vim.vm.device.VirtualDeviceSpec()
#                 nicspec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
#                 nicspec.device = device
#                 nicspec.device.wakeOnLanEnabled = True
#
#                 network = self.pyvmomi_service.find_network_by_name(service_instance, port_group_path, port_group_name)
#                 dvs_port_connection = vim.dvs.PortConnection()
#                 dvs_port_connection.portgroupKey = network.key
#                 dvs_port_connection.switchUuid = network.config.distributedVirtualSwitch.uuid
#                 nicspec.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
#                 nicspec.device.backing.port = dvs_port_connection
#
#                 nicspec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
#                 nicspec.device.connectable.startConnected = True
#                 nicspec.device.connectable.allowGuestControl = True
#                 device_change.append(nicspec)
#                 break
#
#         config_spec = vim.vm.ConfigSpec(deviceChange=device_change)
#         task = vm.ReconfigVM_Task(config_spec)
#         logger.info("Successfully changed network")
#         return self.synchronous_task_waiter.wait_for_task(task)

class VirtualMachinePortGroupConfigurer(object):
    def __init__(self, pyvmomi_service, synchronous_task_waiter):
        self.pyvmomi_service = pyvmomi_service
        self.synchronous_task_waiter = synchronous_task_waiter


    def configure_port_group_on_vm(self,
                                   service_instance,
                                   virtual_machine_path,
                                   vm_uuid,
                                   port_group_path,
                                   port_group_name):

        logger.debug("virtual machine path {} vmUUID {}".format(virtual_machine_path, vm_uuid))
        vm = self.pyvmomi_service.find_by_uuid(service_instance, vm_uuid, True)
        # vm = self.pyvmomi_service.find_vm_by_name(service_instance, virtual_machine_path, virtual_machine_name)
        # This code is for changing only one Interface. For multiple Interface
        # Iterate through a loop of network names.
        device_change = []
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualEthernetCard):
                nicspec = vim.vm.device.VirtualDeviceSpec()
                nicspec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                nicspec.device = device
                nicspec.device.wakeOnLanEnabled = True

                network = self.pyvmomi_service.find_network_by_name(service_instance, port_group_path, port_group_name)
                dvs_port_connection = vim.dvs.PortConnection()
                dvs_port_connection.portgroupKey = network.key
                dvs_port_connection.switchUuid = network.config.distributedVirtualSwitch.uuid
                nicspec.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
                nicspec.device.backing.port = dvs_port_connection

                nicspec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
                nicspec.device.connectable.startConnected = True
                nicspec.device.connectable.allowGuestControl = True
                device_change.append(nicspec)
                break

        config_spec = vim.vm.ConfigSpec(deviceChange=device_change)
        task = vm.ReconfigVM_Task(config_spec)
        logger.info("Successfully changed network")
        return self.synchronous_task_waiter.wait_for_task(task)

    def connect_networks(self, vm, networks):
        vnic_mapping = self.map_vnics(vm)
        vnic_map_helper = dict()
        update_mapping = []
        sorted_by_name = self.sort_vnics_by_name(vnic_mapping)
        for network in networks:
            for vnic_name, vnic in sorted_by_name:
                if not (vnic_name in vnic_map_helper) and self.is_vnic_disconnected(vnic):
                    update_mapping.append((vnic, network, True))
                    vnic_map_helper[vnic_name] = True
                    break

        if len(update_mapping) == len(networks):
            return self.update_vnic_by_mapping(vm, update_mapping)
        raise Exception('not enough available vnics')

    def sort_vnics_by_name(self, vnic_mapping):
        sorted_by_name = sorted(vnic_mapping.items(), key=lambda kvp: kvp[0])
        return sorted_by_name

    def connect_first_available_vnic(self, vm, network):
        vnic_mapping = self.map_vnics(vm)
        update_mapping = []
        sorted_by_name = self.sort_vnics_by_name(vnic_mapping)
        for vnic_name, vnic in sorted_by_name:
            if self.is_vnic_disconnected(vnic):
                update_mapping.append((vnic, network, True))
                return self.update_vnic_by_mapping(vm, update_mapping)
                # if self.is_vnic_attached_to_network(vnic, network)
        raise Exception('no available vnic')

    def connect_vinc_port_group(self, vm, vnic_name, network):
        """
        this function connect specific vnic to network
        :param vm: virtual machine
        :param vnic_name: the name of the vnic
        :param network: the network to connect to
        """
        mapping = dict()
        mapping[vnic_name] = network
        self.connect_by_mapping(vm, mapping)

    def connect_by_mapping(self, vm, mapping):
        """
        connect connect the vnics to the network by the specification in the mapping
        :param vm: virtual machine
        :param mapping: a dictionary vnic_name to network ({'vnic_name 1': <vim.Network>network})
        """
        update_mapping = []
        vnic_mapping = self.map_vnics(vm)
        for vnic_name, network in mapping.items():
            if vnic_name in vnic_mapping:
                vnic = vnic_mapping[vnic_name]
                update_mapping.append((vnic, network, True))

        if update_mapping:
            return self.update_vnic_by_mapping(vm, update_mapping)
        return None

    def disconnect_all_port_groups(self, vm, default_network=None):
        vnics = self.map_vnics(vm)
        update_mapping = [(vnic, None, False, default_network, ) for _, vnic in vnics.items()]
        return self.update_vnic_by_mapping(vm, update_mapping)

    def disconnect_network(self, vm, network, default_network=None):
        condition = lambda vnic: True if default_network else not self.is_vnic_disconnected(vnic)
        vnics = self.map_vnics(vm)

        update_mapping = [(vnic, network, False, default_network, )
                          for vnic_name, vnic in vnics.items()
                          if self.is_vnic_attached_to_network(vnic, network) and condition(vnic)]

        return self.update_vnic_by_mapping(vm, update_mapping)

    def update_vnic_by_mapping(self, vm, mapping):
        if not vm or not mapping:
            return None

        vnics_change = []
        for vnic, network, connect, default_network in mapping:
            network = default_network if default_network else network
            vnic_spec = vnic_compose_empty(vnic)
            vnic_attached_to_network(vnic_spec, network)
            vnic_spec = self.get_device_spec(vnic, connect)
            vnics_change.append(vnic_spec)

        return self.reconfig_vm(vnics_change, vm)

    def map_vnics(self, vm):
        """
        maps the vnic of the vm by name
        :param vm: virtual machine
        :return: dictionary: {'vnic_name': vnic}
        """
        mapping = dict()
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualEthernetCard):
                mapping[device.deviceInfo.label] = device
        return mapping

    #todo move to vNIC module
    def get_device_spec(self, vnic, set_connected):
        """
        this function creates the device change spec,
        :param vnic: vnic
        :param set_connected: bool, set as connected or not, default: True
        :rtype: device_spec
        """
        nic_spec = self.create_vnic_spec(vnic)
        self.set_vnic_connectivity_status(nic_spec, to_connect=set_connected)
        return nic_spec

    def create_vnic_spec(self, device):
        """
        create device spec for existing device and the mode of edit for the vcenter to update
        :param device:
        :rtype: device spec
        """
        nic_spec = vim.vm.device.VirtualDeviceSpec()
        nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
        nic_spec.device = device
        return nic_spec

    def set_vnic_connectivity_status(self, nic_spec, to_connect):
        """
        sets the device spec as connected or disconnected
        :param nic_spec: the specification
        :param to_connect: bool
        """
        nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        nic_spec.device.connectable.connected = to_connect
        nic_spec.device.connectable.startConnected = to_connect

    def reconfig_vm(self, device_change, vm):
        config_spec = vim.vm.ConfigSpec(deviceChange=device_change)
        task = vm.ReconfigVM_Task(config_spec)
        logger.info("Successfully changed network")
        return self.synchronous_task_waiter.wait_for_task(task)

    def is_vnic_attached_to_network(self, device, network):
        if hasattr(device, 'backing'):
            has_port_group_key = hasattr(device.backing, 'port') and hasattr(device.backing.port, 'portgroupKey')
            has_network_name = hasattr(device.backing, 'network') and hasattr(device.backing.network, 'name')
            return (has_port_group_key and device.backing.port.portgroupKey == network.key) or \
                   (has_network_name and device.backing.network.name == network.name)
        return False

    def is_vnic_disconnected(self, vnic):
        is_disconnected = not (hasattr(vnic, 'connectable') and vnic.connectable.connected)
        return is_disconnected
