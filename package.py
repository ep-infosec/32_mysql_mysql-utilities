#!/usr/bin/env python
#
# Copyright (c) 2013, 2015 Oracle and/or its affiliates. All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#
"""Module for packaging MySQL Utilities

The aim of this module is to package MySQL Utilities in such way that
the utilities look just like any other application. The end-user
should not notice that they are using Python and should not even
have Python installed. Everything should be provided when the
packages of this scripts are installed.

Since we package and Python and it's modules, we need to make sure
that we use a 'clean' Python installation and always use the
same Python version for every Platform.

Except for the dependencies, package.py works just like setup.py.

Dependencies
============
- zlib development packages (when compiling Python)
- Python v2.7 (compiled or installed from python.org)
- Connector/Python (installed in subdir mysql/)
- cx_Freeze (latest from http://cx-freeze.sourceforge.net/, not through PyPI)

Installing dependencies
=======================

!!!NOTE!!!
*) Below instructions are for Unix, but it works similar for Windows.
*) Make sure to use the Python version _you_ compiled, not the Python
   version coming with the operating system.

Installing Python
-----------------
You can install Python from binaries or from source. If you are installing
binaries you best use the packages you can download from http://python.org
and install them so it does not interfere with the system installation.

If you compile sources, you have to download them from http://python.org
and make sure that the development packages for zlib and OpenSSL are
installed.

   shell> cd Python-2.7.X
   shell> ./configure --prefix=/opt/python/2.7 && make && make install

Installing MySQL Connector/Python
---------------------------------
MySQL Connector/Python is required to be installed in the MySQL
Utilities source, in the mysql/ subdirectory. This is because it
needs to be packaged and can't be found when installed normally.

There are two ways to install MySQL Connector/Python in a
specific location:

Method 1) Using setup.py
   shell> export MYUTILS=/path/to/mysql-utilities-source/
   shell> cd mysql-connector-python-1.0.9
   shell> /opt/python/2.7/bin/python setup.py \
    --install-base=$MYUTILS --install-platbase=$MYUTILS \
    --install-purelib=$MYUTILS --install-lib=$MYUTILS \
    --install-headers=$MYUTILS --install-scripts=$MYUTILS \
    --install-platlib=$MYUTILS --install-data=$MYUTILS

Method 2) Using setup.py and copying folders
   Alternatively, you can also copy the build directory:
   shell> cd mysql-connector-python-1.0.9
   shell> python setup.py build
   shell> cp -a build/lib/mysql/connector /path/to/mysql-utilities-source/mysql

Installing cx_Freeze
--------------------

1) Download source from http://cx-freeze.sourceforge.net/
2) Unpack the source and change to the folder
3) shell> /opt/python/2.7/bin/python setup.py install

"""

import ConfigParser
import fnmatch
import sys
import os
from glob import glob
import platform
import distutils.core
from distutils.command.bdist_dumb import bdist_dumb
from distutils.command.install_data import install_data as _install_data
from distutils import log
from distutils.dir_util import remove_tree
from distutils.util import change_root
from itertools import groupby

_REQUIRED_CX_FREEZE = (4, 3, 1)  # Or later
_REQUIRED_MYCONNPY = (1, 0, 8)  # Or later

# Make absolutely sure current working directory is looked in first
sys.path.insert(0, '.')

# Required Python Version
from mysql.utilities.common.tools import check_python_version
check_python_version()

# Require cx_Freeze
try:
    import cx_Freeze
    vercxfreeze = tuple([int(val) for val in cx_Freeze.version.split('.')])
    if not vercxfreeze >= _REQUIRED_CX_FREEZE:
        raise ImportError
except ImportError:
    log.error("Package cx_Freeze v{0} or later is required.".format(
        '.'.join([str(val) for val in _REQUIRED_CX_FREEZE])))
    sys.exit(1)

# Require Connector/Python
try:
    from mysql.connector import version
    if not version.VERSION >= _REQUIRED_MYCONNPY:
        raise ImportError
except ImportError:
    log.error("MySQL Connector/Python v{0} or later is required.".format(
        '.'.join([str(val) for val in _REQUIRED_MYCONNPY])))
    sys.exit(1)

from info import META_INFO, INSTALL

# cx_Freeze executables and configuration
APPS = [cx_Freeze.Executable(script) for script in glob('scripts/mysql*.py')]
# Acquire packages names to include in library from module info
INSTALL_COPY = INSTALL.copy()
print("Packages to include on library: {0}".format(INSTALL_COPY['packages']))
BUILD_EXE_OPTIONS = {
    "packages": INSTALL_COPY['packages'],
    "excludes": [],
    }

# Arguments passed to the setup() function. This is dict can
# be extended and modified through out the execution of this script.
SETUP_ARGS = META_INFO.copy()
SETUP_ARGS.update({
    'executables': APPS,
    'options': {
        'build_exe': BUILD_EXE_OPTIONS,
        'install_exe': {},
        },
    'cmdclass': {},
    })

SETUP_ARGS.update(INSTALL_COPY)


class NotSupportedCommand(distutils.core.Command):
    """Custom DistUtils command for unsupported commands

    This custom DistUtils command can be used to disable commands
    because, for example, they are not supported on the current
    platform.
    """
    description = "This command is not supported."
    user_options = []

    def initialize_options(self):
        self.help = 0

    def finalize_options(self):
        pass

    def run(self):
        log.error(self.description)


class Install(cx_Freeze.install):
    """Install"""
    install_exe = None

    def select_scheme(self, name):
        if self.install_exe is None and os.name != 'nt':
            arch = platform.architecture()[0]
            libdir = 'lib64' if arch == '64bit' else 'lib'
            self.install_exe = '$base/{libdir}/{name}'.format(
                libdir=libdir,
                name=self.distribution.metadata.name)
        cx_Freeze.install.select_scheme(self, name)


class BDistDumb(bdist_dumb):
    """BDistDumb"""
    description = bdist_dumb.description + ' (customized)'

    def run(self):
        """Run the command"""
        if not self.skip_build:
            self.run_command('build')

        archive_basename = "%s.%s" % (self.distribution.get_fullname(),
                                      self.plat_name)
        pseudoinstall_root = os.path.join(self.dist_dir, archive_basename)

        install = self.reinitialize_command('install', reinit_subcommands=1)
        install.root = pseudoinstall_root
        install.skip_build = self.skip_build
        install.warn_dir = 0

        log.info("installing to %s" % self.bdist_dir)
        self.run_command('install')

        installman = self.get_finalized_command('install_man')
        installman.root = pseudoinstall_root
        installman.run()

        # Make the archive
        self.make_archive(pseudoinstall_root, self.format,
                          root_dir=self.dist_dir, owner=self.owner,
                          group=self.group, base_dir=archive_basename)

        if not self.keep_temp:
            cwd = os.getcwd()
            os.chdir(self.dist_dir)
            remove_tree(archive_basename, dry_run=self.dry_run)
            os.chdir(cwd)


class InstallMan(distutils.core.Command):
    """InstallMan"""
    description = "Install Unix manual pages"
    root = None
    prefix = None

    user_options = [
        ('prefix=', None, 'installation prefix (default /usr/share/man)'),
        ('root=', None,
         "install everything relative to this alternate root directory"),
    ]

    def initialize_options(self):
        """Initialize options"""
        self.root = None
        self.prefix = None

    def finalize_options(self):
        """Finalize options"""
        self.set_undefined_options('install',
                                   ('root', 'root'),
                                   )
        if not self.prefix:
            self.prefix = '/usr/share/man'

        if self.root:
            self.prefix = change_root(self.root, self.prefix)

    def run(self):
        """Run the command"""
        srcdir = os.path.join('docs', 'man')
        manpages = os.listdir(srcdir)
        for man in manpages:
            src_man = os.path.join(srcdir, man)
            section = os.path.splitext(man)[1][1:]
            dest_dir = os.path.join(self.prefix, 'man' + section)
            self.mkpath(dest_dir)  # Could be different section
            dest_man = os.path.join(dest_dir, man)
            self.copy_file(src_man, dest_man)


class install_data(_install_data):
    """Install data and edits the configuration file before installing it"""
    user = None
    home = None
    data_files = None

    def initialize_options(self):
        _install_data.initialize_options(self)
        self.user = None
        self.home = None

    def finalize_options(self):
        self.set_undefined_options('install',
                                   ('user', 'user'),
                                   ('home', 'home'))
        _install_data.finalize_options(self)

    def run(self):
        # Set up paths to write to config file
        install_dir = self.install_dir
        install_logdir = '/var/log'
        if self.user or self.home:
            install_sysconfdir = os.path.join(install_dir, 'etc')
        elif os.name == 'posix' and install_dir in ('/', '/usr'):
            install_sysconfdir = '/etc'
        else:
            install_sysconfdir = 'scripts\\etc\\mysql'

        if not self.data_files:
            return
        # Go over all entries in data_files and process it if needed
        for df in self.data_files:
            # Figure out what the entry contain and collect a list of files.
            if isinstance(df, str):
                # This was just a file name, so it will be installed
                # in the install_dir location. This is a copy of the
                # behaviour inside distutils intall_data.
                directory = install_dir
                filenames = [df]
            else:
                directory = df[0]
                filenames = df[1]

            # Process all the files for the entry and build a list of
            # tuples (directory, file)
            data_files = []
            for filename in filenames:
                # It was a config file template, add install
                # directories to the config file.
                if fnmatch.fnmatch(filename, 'data/*.cfg.in'):
                    config = ConfigParser.RawConfigParser({
                        'prefix': '',  # custom install_dir,
                        'logdir': install_logdir,
                        'sysconfdir': install_sysconfdir,
                    })
                    config.readfp(open(filename))
                    filename = os.path.splitext(filename)[0]
                    config.write(open(filename, "w"))
                    # change directory 'fabric'to mysql
                    directory = os.path.join(install_sysconfdir, 'mysql')
                if os.name == 'nt':
                    directory = install_sysconfdir
                data_files.append((directory, filename))

        # Re-construct the data_files entry from what was provided by
        # merging all tuples with same directory and provide a list of
        # files as second item, e.g.:
        #   [('foo', 1), ('bar', 2), ('foo', 3), ('foo', 4), ('bar', 5)]
        #   --> [('bar', [2, 5]), ('foo', [1, 3, 4])]
        data_files.sort()
        data_files = [
            (d, [f[1] for f in fs]) for d, fs in groupby(data_files,
                                                         key=lambda x: x[0])
        ]
        self.data_files = data_files
        log.info("package--> self.data_files {0}".format(self.data_files))
        log.info("package.py--> self.data_files {0}".format(self.data_files))
        _install_data.run(self)


# Specific packaging for Unix platforms
if os.name != 'nt':
    try:
        from internal.packaging.commands.dist_rpm import BuiltExeRPM
    except ImportError:
        pass  # Building RPM packages not available
    else:
        SETUP_ARGS['cmdclass'].update({'bdist_rpm': BuiltExeRPM})

# Specific packaging for Microsoft Windows
elif os.name == 'nt':
    SETUP_ARGS['cmdclass'].update({
        'bdist_rpm': NotSupportedCommand,
        })
    try:
        from internal.packaging.commands.dist_msi import (
            BuiltCommercialMSI,
            MSIBuiltDist,
        )
        from internal.packaging.commands import bdist
        import mysql.connector
    except ImportError as err:
        log.error("Can not make Windows packages. cx_Freeze and WiX 3.5 "
                  "(or greater) are required. Make also sure Connector/Python"
                  "is available in the mysql/ sub folder of the source of "
                  "MySQL Utilities")
        log.error("Latest error: {0}".format(err))
        sys.exit(1)
    else:
        SETUP_ARGS['cmdclass'].update({'bdist_msi': MSIBuiltDist,
                                       'bdist_com_msi': BuiltCommercialMSI,
                                       'bdist_com': bdist.BuiltCommercial})

# Custom commands
SETUP_ARGS['cmdclass'].update({
    'bdist_dumb': BDistDumb,
    'install': Install,
    'install_man': InstallMan,
    'install_data': install_data,
    })

# Disable commands
SETUP_ARGS['cmdclass'].update({
    'sdist': NotSupportedCommand,
    'upload': NotSupportedCommand,
    'register': NotSupportedCommand,
    'bdist_wininst': NotSupportedCommand,
    })


def main():
    """main"""
    cx_Freeze.setup(**SETUP_ARGS)

if __name__ == '__main__':
    main()
