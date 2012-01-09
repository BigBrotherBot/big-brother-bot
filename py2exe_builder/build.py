import os
import mmap
import re
import sys
import subprocess

CONFIG_FILE = 'build.yaml'

script_dir = os.path.abspath(os.path.dirname(__file__))

try:
    # make sure to import the b3 module from the parent directory
    # (in case an other b3 module was installed system wide with an egg)
    sys.path.insert(0, os.path.abspath(os.path.join(script_dir, '..')))
    from b3 import __version__ as b3_version
    from b3.update import B3version
except ImportError:
    print "Could not import b3"
    raise

current_b3_version = B3version(b3_version)
egg_pkginfo_file = os.path.abspath(os.path.join(script_dir, '../b3.egg-info/PKG-INFO'))
config = None

re_iss_b3_version_number = re.compile('^(?P<part1>#define B3_VERSION_NUMBER ")(?P<number>(\d+(\.\d+)+)?)(?P<part2>"\s*)$', re.MULTILINE)
re_iss_b3_version_suffix = re.compile('^(?P<part1>#define B3_VERSION_SUFFIX ")(?P<suffix>((a|b|dev)\d+)?)(?P<part2>"\s*)$', re.MULTILINE)


def load_config():
    global config

    if not os.path.isfile(os.path.join(script_dir, CONFIG_FILE)):
        print "Could not find config file '%s'" % os.path.abspath(os.path.join(script_dir, CONFIG_FILE))
        choice = raw_input("\nDo you want to create a stub ? [yN] : " % current_b3_version)
        if choice.lower() == 'y':
            create_config_file_stub()
            print "config file stub created"
            sys.exit(0)
        else:
            sys.exit(0)

    from b3.lib import yaml
    with open(CONFIG_FILE, 'r') as f:
        config = yaml.load(f)

    if not 'innosetup_scripts' in config:
        print "Invalid config file. Could not find 'innosetup_scripts'."
        sys.exit(1)
    if not len(config['innosetup_scripts']):
        print "Invalid config file. No script found in 'innosetup_scripts' section."
        sys.exit(1)
    if not 'iscc' in config:
        print "Invalid config file. Could not find 'iscc'."
        sys.exit(1)
    if not os.path.isfile(os.path.abspath(os.path.join(script_dir, config['iscc']))):
        print "Invalid config file. '%s' is not a file." % config['iscc']
        sys.exit(1)
    if not config['iscc'].lower().endswith('iscc.exe'):
        print "Invalid config file. '%s' is not a iscc.exe." % config['iscc']
        sys.exit(1)
    if not 'output_dir' in config:
        print "Invalid config file. output_dir not set."
        sys.exit(1)
    else:
        dist_dir = os.path.abspath(os.path.join(script_dir, config['output_dir']))
        if not os.path.isdir(dist_dir):
            os.makedirs(dist_dir)


def create_config_file_stub():
    with open(os.path.abspath(os.path.join(script_dir, CONFIG_FILE)), 'w') as f:
        f.write("""\
# list of InnoSetup script to compile
innosetup_scripts:
 - b3-installer-project.iss
 - b3_lite_for_bf3-installer-project.iss

# where to find the InnoSetup compiler
iscc:  C:\Program Files (x86)\Inno Setup 5\ISCC.exe

# where to generate the distribution files
output_dir: dist
""")


def get_innosetup_script_version(innosetup_scripts):
    """\
    For all given file names, extract the B3version found in the file content.
    Returns result as a dict where file names are the keys and B3version the values.
    """
    innosetup_scripts_versions = dict()
    for file_name in innosetup_scripts:
        with open(os.path.join(script_dir, file_name), 'r') as f:
            version_number = version_suffix = ''
            map = mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ)
            m_number = re_iss_b3_version_number.search(map)
            if m_number:
                version_number = m_number.group('number')
            m_suffix = re_iss_b3_version_suffix.search(map)
            if m_suffix:
                version_suffix = m_suffix.group('suffix')
            map.close()
            innosetup_scripts_versions[file_name]  = B3version(version_number + version_suffix)
    return innosetup_scripts_versions


def update_innosetup_scripts(innosetup_scripts, current_b3_version):
    """\
    for all scripts of innosetup_scripts, update the version to current_b3_version if necessary
    """
    def extract_full_version_from_innosetup_script(str_content):
        """Return the full version string found in given string as expected in a InnoSetup script"""
        version_number = version_suffix = ''
        m_number = re_iss_b3_version_number.search(str_content)
        if m_number:
            version_number = m_number.group('number')
        m_suffix = re_iss_b3_version_suffix.search(str_content)
        if m_suffix:
            version_suffix = m_suffix.group('suffix')
        return version_number + version_suffix
    
    current_b3_version_number = current_b3_version.version
    current_b3_version_suffix = current_b3_version.prerelease
    for file_name in innosetup_scripts:
        data = ''
        with open(os.path.join(script_dir, file_name), 'r') as f:
            data = f.read()
        script_version = B3version(extract_full_version_from_innosetup_script(data))
        if script_version != current_b3_version:
            data = re_iss_b3_version_number.sub("\g<part1>%s\g<part2>" % '.'.join(map(str, current_b3_version_number)), data)
            data = re_iss_b3_version_suffix.sub("\g<part1>%s\g<part2>" % ''.join(map(str, current_b3_version_suffix)), data)
            with open(os.path.join(script_dir, file_name), 'w') as f:
                f.write(data)


def build_innosetup_scripts(innosetup_scripts):
    """\
    build each given innosetup script
    """
    results = {}
    compiler = os.path.abspath(os.path.join(script_dir, config["iscc"]))
    for file_name in innosetup_scripts:
        script_file = os.path.abspath(os.path.join(script_dir, file_name))
        print "building %s" % script_file
        try:
            cmd = [compiler, script_file, '/Q']
            cmd.append('/O%s' % os.path.join(script_dir, config['output_dir']))
            exit_code = subprocess.call(cmd)
            if exit_code == 0:
                results[file_name] = 'OK'
            else:
                results[file_name] = 'KO'
        except Exception, err:
            results[file_name] = err
    return results.items()


def build_zip_distribution(source_folder):
    """\
    create a zipped distribution without installer
    """
    import zipfile
    dist_dir = os.path.join(script_dir, config['output_dir'])
    zip_filename = 'BigBrotherBot-%s-win32.zip' % current_b3_version
    print "building " + zip_filename + " (from " + os.path.abspath(source_folder) + ")"
    zip = zipfile.ZipFile(os.path.join(dist_dir, zip_filename), 'w')
    for root, dirs, files in os.walk(source_folder):
        for file in files:
            file_path = os.path.abspath(os.path.join(root, file))
            zip.write(file_path, arcname=os.path.join('b3', file_path[len(os.path.abspath(source_folder)):]))
    zip.close()
    return os.path.join(dist_dir, zip_filename), 'OK'


def py2exe():
    import shutil
    dist_py2exe_dir = os.path.abspath(os.path.join(script_dir, 'dist_py2exe'))
    print "cleaning directory %s" % dist_py2exe_dir
    if os.path.isdir(dist_py2exe_dir):
        shutil.rmtree(dist_py2exe_dir)
    os.makedirs(dist_py2exe_dir)
    print "py2exe"
    process = subprocess.Popen([sys.executable, os.path.abspath(os.path.join(script_dir, '../setupPy2exe.py')), 'py2exe'], stderr=subprocess.PIPE, cwd=os.path.join(script_dir, '..'))
    exit_code = process.communicate()
    if exit_code != 0:
        choice = raw_input("Do you want to continue ? [Yn] : ")
        if choice.lower() == 'n':
            sys.exit(1)
    shutil.copy(os.path.join(script_dir, 'assets_common/readme-windows.txt'), os.path.join(dist_py2exe_dir, 'readme.txt'))
    shutil.copy(os.path.join(script_dir, 'assets_common/gpl-2.0.txt'), os.path.join(dist_py2exe_dir, 'license.txt'))
    try:
        os.remove(os.path.abspath(os.path.join(dist_py2exe_dir, 'README')))
    except WindowsError, err:
        print "WARNING: %s" % err


def main():

    load_config()

    print "{0:>50} :  {1}".format('detected current B3 version', current_b3_version)
    choice = raw_input("\nDo you want to continue ? [Yn] : " % current_b3_version)
    if choice.lower() not in ('y', 'Y', ''):
        sys.exit(0)

    innosetup_scripts_versions = get_innosetup_script_version(config['innosetup_scripts'])

    need_updates = False
    for file_name, version in innosetup_scripts_versions.items():
        need_updates = need_updates or (current_b3_version != version)
        print "{0:>50} :  {1:<10} {2}".format(os.path.relpath(file_name), version, 'need update' if current_b3_version != version else '')

    if not need_updates:
        print "\nall files have the right version number"
    else:
        choice = raw_input("\nDo you want to update the files with the current version \"%s\" ? [Yn] : " % current_b3_version)
        if choice.lower() != 'n':
            update_innosetup_scripts(config['innosetup_scripts'], current_b3_version)
        else:
            print "not updating scripts"

    build_results = list()
    py2exe()
    build_results += build_innosetup_scripts(config['innosetup_scripts'])
    build_results.append(build_zip_distribution(os.path.join(script_dir, "dist_py2exe")))

    print "\nBuild results :"
    print "---------------"
    for file_name, result in build_results:
        print "{0:>50} :  {1}".format(os.path.relpath(file_name), result)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass