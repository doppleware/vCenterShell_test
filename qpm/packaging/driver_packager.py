import os
import sys
import zipfile
import ConfigParser
import xml.etree.ElementTree as ET
import time

DRIVER_FILE_BASE_DIR = 'vCenterShellPackage'
STRIPING_CHARS = ' \t\n\r'
DRIVER_FOLDER = 'driver_folder'
INCLUDE_FILES = 'include_files'
INCLUDE_DIRS = 'include_dirs'
TARGET_NAME = 'target_name'
IS_DRIVER = 'is_driver'
VERSION_FILENAME = 'version.txt'
TARGET_DIR = 'target_dir'


def zip_dir(path, zip_handler, include_dir=True):
    """
    zip all files and items in dir
    :param path:
    :param zip_handler: zip file handler
    :param boolean include_dir: specify if we want the archive with or without the directory
    """
    for root, dirs, files in os.walk(path):
        for file_to_zip in files:
            filename = os.path.join(root, file_to_zip)
            add_file(filename, zip_handler, include_dir)


def add_file(filename, zip_handler, include_dir=True):
    if os.path.isfile(filename):  # regular files only
        if include_dir:
            zip_handler.write(filename)
        else:
            splited_filename = filename.split('\\', 1)
            s_filename = splited_filename[1] if len(splited_filename) > 1 else filename
            zip_handler.write(filename, s_filename)


def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)


def add_version_file_to_zip(ziph, driver_path=None):
    if not os.path.exists(VERSION_FILENAME):
        raise Exception('no version file found')
    ziph.write(VERSION_FILENAME)


def main(args):
    config_file_name = args[1]

    pack_driver(config_file_name)


def pack_driver(config_file_name):
    config = ConfigParser.SafeConfigParser()
    config.readfp(open(config_file_name))
    driver = config.get('Packaging', DRIVER_FOLDER)
    include_dirs = config.get('Packaging', INCLUDE_DIRS).split(',')
    target_name = config.get('Packaging', TARGET_NAME)
    target_dir = config.get('Packaging', TARGET_DIR)
    try:
        include_files = config.get('Packaging', INCLUDE_FILES).split(',')
    except Exception:
        include_files = []
    try:
        is_driver = config.getboolean('Packaging', IS_DRIVER)
    except Exception:
        is_driver = False
    version = _get_version()
    if is_driver:
        _update_driver_version(driver, version)
    else:
        _update_script_version(target_name, version)
    zip_name = os.path.join(DRIVER_FILE_BASE_DIR, target_dir, target_name + '.zip')
    print 'Creating script {0} version {1}'.format(zip_name, version)
    ensure_dir(zip_name)
    # deletes old package
    if os.path.isfile(zip_name):
        os.remove(zip_name)
    zip_file = zipfile.ZipFile(zip_name, 'w')
    os.chdir(os.path.join(os.getcwd(), driver))
    zip_dir('.', zip_file)
    os.chdir(os.path.join(os.getcwd(), '../'))
    if driver.find("\\") != -1:
        path_parts = len(driver.split("\\")) - 1
        if path_parts > 0:
            path_fixer = ''
            for i in range(path_parts):
                path_fixer += '../'
            os.chdir(os.path.join(os.getcwd(), path_fixer))
    add_version_file_to_zip(zip_file)
    for file_to_include in include_files:
        add_file(file_to_include, zip_file, False)
    for dir_to_include in include_dirs:
        zip_dir(dir_to_include, zip_file)
    zip_file.close()


def _update_driver_version(folder_path, version):
    driver_model_path = os.path.join(_get_current_dir(), folder_path, 'drivermetadata.xml')
    tree = ET.parse(driver_model_path)
    if tree.getroot().get('Version'):
        tree.getroot().attrib['Version'] = version
        tree.write(driver_model_path)
    else:
        raise Exception('version attribute in: {0} not found'.format(driver_model_path))


def _get_current_dir():
    return os.getcwd()


def _update_script_version(script_name, version):
    ns = {'default': 'http://schemas.qualisystems.com/ResourceManagement/DataModelSchema.xsd'}
    datamodel_path = os.path.join(_get_current_dir(),'vCenterShellPackage', 'DataModel', 'datamodel.xml')

    tree = ET.parse(datamodel_path)
    scripts = tree.getroot().findall('.//default:ScriptDescriptors/default:ScriptDescriptor/[@Name="{0}"]'
                                     .format(script_name), ns)
    if not len(scripts):
        raise Exception('Script {0} not found in datamodel.xml'.format(script_name))

    scripts[0].set('Version', version)
    tree.write(datamodel_path)


def _get_version():
    with open('version.txt', 'r') as version_file:
        version = version_file.read().replace('\n', '')
    return version


if __name__ == "__main__":
    main(sys.argv)
