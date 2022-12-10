#
# Copyright (c) 2014, 2016, Oracle and/or its affiliates. All rights reserved.
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

"""
config_parser errors test.
"""

import os
import ConfigParser
import mutlib

from mysql.utilities.exception import UtilError
from mysql.utilities.common.ip_parser import parse_connection


class test(mutlib.System_test):
    """Test the config-path authentication mechanism.
    This module tests the ability to login to MySQL server using a
    configuration file.
    """

    config_file_path = None
    config_file_path_2 = None
    server1 = None
    test_group_names = None

    def check_prerequisites(self):
        # Check if the required tools are accessible
        self.check_mylogin_requisites()

        # Check the required number of servers
        return self.check_num_servers(1)

    def do_cleanup(self):
        """remove temporally configuration files.
        """
        try:
            os.remove(self.config_file_path)
            os.remove(self.config_file_path_2)
        except:
            pass

    def setup(self):
        self.config_file_path = os.path.abspath('./temp_1.cnf')
        self.config_file_path_2 = os.path.abspath('./temp_2.cnf')
        self.do_cleanup()
        self.test_group_names = []
        self.server1 = self.servers.get_server(0)

        config_p = ConfigParser.ConfigParser()
        with open(self.config_file_path, 'w') as config_f:

            config_p.add_section('client')
            config_p.set('client', 'user', 'my_user')
            config_p.set('client', 'password', 'mypasswd')
            config_p.set('client', 'host', 'no-host')

            self.test_group_names.append(('simple group name', 'simple_login'))
            config_p.add_section('simple_login')
            config_p.set('simple_login', 'user', self.server1.user)
            config_p.set('simple_login', 'password', self.server1.passwd)
            config_p.set('simple_login', 'host', self.server1.host)
            config_p.set('simple_login', 'port', self.server1.port)

            config_p.write(config_f)

        config_p = ConfigParser.ConfigParser()
        with open(self.config_file_path_2, 'w') as config_f:
            config_p.add_section('missing_values')
            config_p.set('missing_values', 'user', 'my_user')

            config_p.add_section('client')
            config_p.set('client', 'ssl-ca', 'ssl-ca.cert')
            config_p.set('client', 'ssl-cert', 'ssl-cert.cert')
            config_p.set('client', 'ssl-key', 'ssl-key.cert')

            config_p.write(config_f)

        return True

    def run(self):
        self.res_fname = "result.txt"
        # Test parse_connection with login-paths
        con_tests = [
            "test_user@localhost:3306",   # use of normal parser
            "test/slash",                 # slash
            # collision with login-path:
            "test_group_simple_login",    # simple collision
            "c:\\some_config.cnf",        # & no existing windows file
            "/etc_etc/some_config.cnf",   # & no existing linux file
            "test-hyphen1234#",           # another collision
            "test_default_group",         # test default client group
            "temp_1.cnf",                 # collision & default group
            "temp_1.cnf[undeclared]",     # undeclared group
            "temp_2.cnf",                 # collision & default group w/ssl
            "temp_2.cnf[missing_values]"  # missing values
        ]

        test_n = 0
        for test_ in con_tests:
            test_n += 1
            msg = "Test case {0} - {1}".format(test_n, test_)
            if self.debug:
                print(msg)
            self.results.append("{0}\n".format(msg))
            try:
                conn = parse_connection(test_)
            except UtilError as err:
                self.results.append("{0}\n".format(err.errmsg))
            else:
                self.results.append("{0}\n".format(sorted(conn.iteritems())))

        # Replacements
        self.replace_substring_portion("port or ", "socket", "port")
        self.replace_substring(".exe", "")

        return True

    def get_result(self):
        return self.compare(__name__, self.results)

    def record(self):
        return self.save_result_file(__name__, self.results)

    def cleanup(self):
        self.do_cleanup()
        return True
