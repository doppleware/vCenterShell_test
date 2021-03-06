import subprocess
import urllib

from common.utilites.common_utils import fixurl

OVF_DESTENATION_FORMAT = 'vi://{0}:{1}@{2}/{3}/host/{4}{5}'

COMPLETED_SUCCESSFULLY = 'Completed successfully'
NO_SSL_PARAM = '--noSSLVerify'
ACCEPT_ALL_PARAM = '--acceptAllEulas'
POWER_ON_PARAM = '--powerOn'
POWER_OFF_PARAM = '--powerOffTarget'
VM_FOLDER_PARAM = '--vmFolder={0}'
VM_NAME_PARAM = '--name={0}'
DATA_STORE_PARAM = '--datastore={0}'
RESOURCE_POOL_PARAM_TO_URL = '/Resources/{0}'


class OvfImageDeployerService(object):
    def __init__(self, ovf_tool_exe_path, logger):
        self.ovf_tool_exe_path = ovf_tool_exe_path
        self.logger = logger

    def deploy_image(self, image_params):
        """
        Receives ovf image parameters and deploy it on the designated vcenter
        :type image_params: vCenterShell.vm.ovf_image_params.OvfImageParams
        """
        args = self._get_args(image_params)
        self.logger.debug('opening ovf tool process with the params: {0}'.format(','.join(args)))
        process = subprocess.Popen(args, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.logger.debug('communicating with ovf tool')
        result = process.communicate()
        process.stdin.close()

        if result:
            res = '\n\r'.join(result)
        else:
            raise Exception('no result has return from the ovftool')

        self.logger.info('communication with ovf tool results: {0}'.format(res))
        if res.find(COMPLETED_SUCCESSFULLY) > -1:
            return True

        image_params.connectivity.password = '******'
        args_for_error = ' '.join(self._get_args(image_params))
        self.logger.error('error deploying image with the args: {0}, error: {1}'.format(args_for_error, res))
        raise Exception('error deploying image with the args: {0}, error: {1}'.format(args_for_error, res))

    # C:\Program Files\VMware\VMware OVF Tool>ovftool --X:logFile="c:\log.log"
    # --noSSLVerify --acceptAllEulas --vmFolder="Raz" --name="raz_test_1" --datastore="aa"
    # "C:\images\test\OVAfile121_QS\OVAfile121_QS.ovf"
    # "vi://qualisystems%5Craz.a:%21QAZ2wsx@192.168.42.110/QualiSB/host/QualiSB Cluster"
    def _get_args(self, image_params):
        """
        :type image_params: vCenterShell.vm.ovf_image_params.OvfImageParams
        """
        # create vm name
        vm_name_param = VM_NAME_PARAM.format(image_params.vm_name)

        # datastore name
        datastore_param = DATA_STORE_PARAM.format(image_params.datastore)

        # power state
        power_state = POWER_ON_PARAM if image_params.power_on else POWER_OFF_PARAM

        # build basic args
        args = [self.ovf_tool_exe_path,
                NO_SSL_PARAM,
                ACCEPT_ALL_PARAM,
                power_state,
                vm_name_param,
                datastore_param]
        # append user folder
        if hasattr(image_params, 'vm_folder') and image_params.vm_folder:
            vm_folder_str = VM_FOLDER_PARAM.format(image_params.vm_folder)
            args.append(vm_folder_str)

        # append args that are user inputs
        if hasattr(image_params, 'user_arguments') and image_params.user_arguments:
            args += [key
                     for key in image_params.user_arguments]

        # get ovf destination
        ovf_destination = self._get_ovf_destenation(image_params)

        image_url = image_params.image_url
        # set location and destination
        args += [image_url,
                 ovf_destination]

        return args

    def _get_ovf_destenation(self, image_params):
        resource_pool_str = ''
        if image_params.resource_pool:
            resource_pool_str = RESOURCE_POOL_PARAM_TO_URL.format(image_params.resource_pool)

        # connection to the vcenter and the path of the cluster name of the deployed image
        ovf_destination = OVF_DESTENATION_FORMAT. \
            format(image_params.connectivity.username,
                   image_params.connectivity.password,
                   str(image_params.connectivity.host).encode('ascii'),
                   str(image_params.datacenter).encode('ascii'),
                   str(image_params.cluster).encode('ascii'),
                   str(resource_pool_str).encode('ascii'))
        return fixurl(ovf_destination)

    @staticmethod
    def fix_param(param):
        if str(param).find(' ') > -1:
            return '\"{0}\"'.format(param)
        return param
