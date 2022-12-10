#
# Copyright (c) 2010, 2014, Oracle and/or its affiliates. All rights reserved.
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
diskusage_errors test.
"""

import os

import diskusage_basic

from mysql.utilities.exception import MUTLibError, UtilError


class test(diskusage_basic.test):
    """Disk usage errors
    This test executes the disk space utility
    on a single server testing error conditions.
    It uses the diskusage_basic test for setup and teardown methods.
    """

    port1 = None

    def check_prerequisites(self):
        if self.servers.get_server(0).check_version_compat(5, 6, 2):
            raise MUTLibError("Test requires server version prior to 5.6.2")
        return diskusage_basic.test.check_prerequisites(self)

    def setup(self):
        self.server0 = self.servers.get_server(0)
        self.export_import_file = "test_run.txt"

        self.port1 = int(self.servers.get_next_port())

        self.error_log = os.path.join(os.getcwd(), "error_log.err")

        res = self.servers.start_new_server(
            self.server0, self.port1, self.servers.get_next_id(),
            "root", "diskusage_none",
            '--skip-innodb --default-storage-engine=MyISAM --log-bin '
            '--log-error="{0}"'.format(self.error_log))
        self.server1 = res[0]
        if not self.server1:
            raise MUTLibError("Failed to start a new server.")

        self.drop_all()
        data_file = os.path.normpath("./std_data/basic_data.sql")
        try:
            self.server1.read_and_exec_SQL(data_file, self.debug)
        except UtilError as err:
            raise MUTLibError("Failed to read commands from file {0}: "
                              "{1}".format(data_file, err.errmsg))

        # Create a new user 'repl:repl' (without privileges).
        try:
            self.server1.exec_query("CREATE USER 'repl'@'{0}' IDENTIFIED BY "
                                    "'repl'".format(self.server1.host))
        except UtilError as err:
            raise MUTLibError("Failed to create user 'repl'@'{0}' (with "
                              "password 'repl'): {1}".format(self.server1.host,
                                                             err.errmsg))
        return True

    def run(self):
        self.res_fname = "result.txt"

        from_conn = "--server={0}".format(
            self.build_connection_string(self.server1))

        cmd_base = "mysqldiskusage.py {0} --format=csv".format(from_conn)
        test_num = 1
        comment = ("Test Case {0} : Errors for logs, binlog, "
                   "innodb ".format(test_num))
        cmd = "{0} -lambi -vv".format(cmd_base)
        res = self.run_test_case(0, cmd, comment)
        if not res:
            raise MUTLibError("DISKUSAGE: {0}: failed".format(comment))
        self.results.append("\n")

        test_num += 1
        comment = ("Test Case {0} : Using a user without "
                   "privileges.".format(test_num))
        cmd_base = cmd_base.replace('root', 'repl')
        cmd = '{0} -a'.format(cmd_base)
        res = self.run_test_case(0, cmd, comment)
        if not res:
            raise MUTLibError("DISKUSAGE: {0}: failed".format(comment))

        test_num += 1
        comment = ("Test Case {0} : Using bad user account.".format(test_num))
        cmd_base = cmd_base.replace('repl:repl', 'root:toor')
        cmd = '{0} -a'.format(cmd_base)
        res = self.run_test_case(2, cmd, comment)
        if not res:
            raise MUTLibError("DISKUSAGE: {0}: failed".format(comment))

        diskusage_basic.test.mask(self)

        self.mask_column_result("mysql,", ",", 2, "XXXXXXX")
        self.mask_column_result("util_test", ",", 2, "XXXXXXX")
        self.mask_column_result("mysql,X", ",", 3, "XXXXXXX")
        self.mask_column_result("util_test,X", ",", 3, "XXXXXXX")
        self.mask_column_result("mysql,X", ",", 4, "XXXXXXX")
        self.mask_column_result("util_test,X", ",", 4, "XXXXXXX")
        self.mask_column_result("mysql,X", ",", 5, "XXXXXXX")
        self.mask_column_result("util_test,X", ",", 5, "XXXXXXX")

        self.replace_result("error_log.err", "error_log.err,XXXX\n")

        # Remove this row for 5.5 servers
        self.remove_result("performance_schema")

        return True

    def get_result(self):
        return self.compare(__name__, self.results)

    def record(self):
        return self.save_result_file(__name__, self.results)

    def cleanup(self):
        # Perform base cleanup.
        res = diskusage_basic.test.cleanup(self)

        # Need to shutdown the spawned server
        if self.server1:
            res = self.servers.stop_server(self.server1)
            self.server1 = None
            self.servers.clear_last_port()
        return res
