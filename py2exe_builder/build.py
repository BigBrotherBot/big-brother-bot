import os
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

egg_pkginfo_file = os.path.abspath(os.path.join(script_dir, '../b3.egg-info/PKG-INFO'))

# read version from the b3/PKG-INFO file
re_pkginfo_version = re.compile(r'^\s*Version:\s*(?P<version>(?P<numbers>\d+\.\d+(?:\.\d+)?)(?P<pre_release>(?:a|b|dev|d)\d*)?(?P<suffix>.*?))\s*$', re.MULTILINE)
with open(egg_pkginfo_file, 'r') as f:
    m = re_pkginfo_version.search(f.read())
if not m:
    print "could not find version from %s" % egg_pkginfo_file
    sys.exit(1)
current_b3_version = m.group("version")
current_b3_version_part1 = m.group("numbers")
current_b3_version_part2 = ""
if m.group("pre_release"):
    current_b3_version_part2 += m.group("pre_release")
if m.group("suffix"):
    current_b3_version_part2 += m.group("suffix")


config = None
def load_config():
    global config
    config_file_path = os.path.normpath(os.path.join(script_dir, CONFIG_FILE))
    if not os.path.isfile(config_file_path):
        print "Could not find config file '%s'" % config_file_path
        choice = raw_input("\nDo you want to create a stub ? [yN] : " % current_b3_version)
        if choice.lower() == 'y':
            create_config_file_stub()
            print "config file stub created"
            sys.exit(0)
        else:
            sys.exit(0)

    from b3.lib import yaml
    with open(config_file_path, 'r') as f:
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
    # location of the InnoSetup Compiler program taken from environment variable ISCC_EXE if exists, else from
    # the yaml config file.
    config['iscc'] = os.environ.get('ISCC_EXE', config['iscc'])
    if not config['iscc'].lower().endswith('iscc.exe'):
        print "Invalid location for the ISCC.exe program. '%s' is not a iscc.exe." % config['iscc']
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

# where to find the InnoSetup compiler
# you can override this value setting the environment variable ISCC_EXE
iscc:  C:\Program Files (x86)\Inno Setup 5\ISCC.exe

# where to generate the distribution files
output_dir: ../releases
""")


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
            cmd.append('/dB3_VERSION_NUMBER=' + current_b3_version_part1)
            cmd.append('/dB3_VERSION_SUFFIX=' + current_b3_version_part2)
            print " ".join(cmd)
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


def main():
    load_config()
    print "{0:>50} :  {1}".format('current B3 version', current_b3_version)
    build_results = list()
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