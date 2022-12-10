#
# Copyright (c) 2010, 2015, Oracle and/or its affiliates. All rights reserved.
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
server_info_parameters test.
"""
import os

import server_info

from mysql.utilities.exception import MUTLibError


_FORMATS = ['GRID', 'CSV', 'TAB', 'VERTICAL']


class test(server_info.test):
    """check parameters for serverinfo
    This test executes a series of server_info tests using a variety of
    parameters. It uses the server_info test as a parent for setup and teardown
    methods.
    """

    def check_prerequisites(self):
        return server_info.test.check_prerequisites(self)

    def setup(self):
        self.server3 = None
        return server_info.test.setup(self)

    def run(self):
        quote_char = "'" if os.name == "posix" else '"'
        self.server1 = self.servers.get_server(0)
        self.res_fname = "result.txt"

        from_conn2 = "--server={0}".format(
            self.build_connection_string(self.server2))
        cmd_str = "mysqlserverinfo.py {0} ".format(from_conn2)

        test_num = 1

        cmd_opts = " --format=csv --help"
        comment = "Test case {0} - show help".format(test_num)
        res = self.run_test_case(0, cmd_str + cmd_opts, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        # Mask version information
        self.replace_result("MySQL Utilities mysqlserverinfo.py version",
                            "MySQL Utilities mysqlserverinfo.py version XXX\n")
        # Mask copyright date
        self.replace_result("Copyright (c)", "Copyright (c) YYYY Oracle "
                                             "and/or its affiliates. All "
                                             "rights reserved.\n")

        test_num += 1
        cmd_opts = " --format=csv --no-headers"
        comment = "Test case {0} - no headers".format(test_num)
        res = self.run_test_case(0, cmd_str + cmd_opts, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        for format_ in _FORMATS:
            cmd_opts = " --format={0} --no-headers".format(format_)
            test_num += 1
            comment = "Test case {0} - {1}".format(test_num, cmd_opts)
            res = self.run_test_case(0, cmd_str + cmd_opts, comment)
            if not res:
                raise MUTLibError("{0}: failed".format(comment))

        cmd_str = self.start_stop_newserver(delete_log=False,
                                            stop_server=False)

        test_num += 1
        # We will also show that -vv does not produce any additional output.
        cmd_opts = " --format=vertical -vv"
        comment = "Test case {0} - verbose run against online server".format(
            test_num)
        res = self.run_test_case(0, cmd_str + cmd_opts, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        cmd_opts = (" --format=vertical --show-servers --port-range="
                    "3306:{0}".format(self.servers.view_next_port()))
        comment = "Test case {0} - show servers".format(test_num)
        res = self.run_test_case(0, cmd_str + cmd_opts, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        comment = "Test case {0} - show servers (no conn)".format(test_num)
        res = self.run_test_case(0, "mysqlserverinfo.py --show-servers "
                                 "--port-range=3306:{0}"
                                 "".format(self.servers.view_next_port()),
                                 comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        # Now, stop the server then run verbose test again
        res = self.server3.show_server_variable('basedir')
        self.basedir = os.path.normpath(res[0][1])
        res = self.server3.show_server_variable('datadir')
        self.datadir3 = os.path.normpath(res[0][1])

        self.servers.stop_server(self.server3, 10, False)
        self.servers.remove_server(self.server3.role)
        self.remove_logs_from_server(self.datadir3)
        # NOTICE: The -vv option cannot be tested as it produces machine-
        #         specific data from the server start command.

        test_num += 1
        comment = "Test case {0} - run against offline server".format(test_num)
        cmd_opts = ("--format=vertical --start --basedir={2}{0}{2} "
                    "--datadir={2}{1}{2} --start-timeout=0"
                    "".format(self.basedir, self.datadir3, quote_char))
        cmd = "{0} {1}".format(cmd_str, cmd_opts)
        res = self.run_test_case(0, cmd, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        # Mask version
        self.replace_result(
            "MySQL Utilities mysqlserverinfo version",
            "MySQL Utilities mysqlserverinfo version X.Y.Z\n")

        server_info.test.do_replacements(self)

        self.replace_result("+---", "+---------+\n")
        self.replace_result("|", "| XXXX ...|\n")
        self.replace_result("localhost:", "localhost:XXXX [...]\n")
        self.remove_result("#  Process id:")

        # Remove warning that appears only on 5.7 and which is not important
        # for the sake of this test.
        self.remove_result_and_lines_around(
            "WARNING: Unable to get size information from 'stderr' "
            "for 'error log'.", lines_before=3, lines_after=1)

        return True

    def get_result(self):
        return self.compare(__name__, self.results)

    def record(self):
        return self.save_result_file(__name__, self.results)

    def cleanup(self):
        from mysql.utilities.common.tools import delete_directory

        if self.server3:
            delete_directory(self.datadir3)
            self.server3 = None
        return server_info.test.cleanup(self)
