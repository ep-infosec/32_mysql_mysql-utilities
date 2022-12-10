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
server_info_errors test.
"""

import server_info

from mysql.utilities.exception import MUTLibError


class test(server_info.test):
    """check errors for serverinfo
    This test executes a series of error tests using a variety of
    parameters. It uses the server_info test as a parent for setup and teardown
    methods.
    """

    def check_prerequisites(self):
        return server_info.test.check_prerequisites(self)

    def setup(self):
        self.server3 = None
        return server_info.test.setup(self)

    def run(self):
        self.server1 = self.servers.get_server(0)
        self.res_fname = "result.txt"

        from_conn2 = "--server={0}".format(
            self.build_connection_string(self.server2))
        cmd_str = "mysqlserverinfo.py "

        test_num = 1
        comment = "Test case {0} - no server".format(test_num)
        res = self.run_test_case(2, cmd_str, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))
        self.results.append("\n")

        test_num += 1
        cmd_opts = "{0} --server=xewkjsdd:21".format(cmd_str)
        comment = "Test case {0} - bad server".format(test_num)
        res = self.run_test_case(1, cmd_opts, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))
        self.results.append("\n")

        cmd_str = "mysqlserverinfo.py {0} ".format(from_conn2)

        test_num += 1
        cmd_opts = "{0} --format=ASDASDASD".format(cmd_str)
        comment = "Test case {0} - bad format".format(test_num)
        res = self.run_test_case(2, cmd_opts, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))
        self.results.append("\n")

        test_num += 1
        cmd_str_wrong = cmd_str.replace(":root", ":wrong")
        cmd_opts = "{0} --format=grid".format(cmd_str_wrong)
        comment = "Test case {0} - wrong password".format(test_num)
        res = self.run_test_case(1, cmd_opts, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))
        self.results.append("\n")

        test_num += 1
        cmd_str_wrong = cmd_str.replace(":root", ":")
        cmd_opts = "{0} --format=grid".format(cmd_str_wrong)
        comment = "Test case {0} - no password".format(test_num)
        res = self.run_test_case(1, cmd_opts, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))
        self.results.append("\n")

        cmd_str = self.start_stop_newserver()

        test_num += 1
        cmd_opts = "{0} --format=vertical".format(cmd_str)
        comment = ("Test case {0} - offline server without start, basedir, "
                   "datadir option".format(test_num))
        res = self.run_test_case(1, cmd_opts, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))
        self.results.append("\n")

        test_num += 1
        cmd_opts = "{0} --format=vertical --basedir=.".format(cmd_str)
        comment = ("Test case {0} - offline server without start, "
                   "datadir option".format(test_num))
        res = self.run_test_case(1, cmd_opts, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))
        self.results.append("\n")

        test_num += 1
        cmd_opts = ("{0} --format=vertical --basedir=. "
                    "--datadir=.").format(cmd_str)
        comment = ("Test case {0} - offline server without start "
                   "option".format(test_num))
        res = self.run_test_case(1, cmd_opts, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        cmd_opts = "{0} --start-timeout=1.5".format(cmd_str)
        comment = ("Test case {0} - Invalid --start-timeout "
                   "value".format(test_num))
        res = self.run_test_case(2, cmd_opts, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        cmd_opts = ("{0} --format=vertical --basedir=not_exist --datadir=."
                    " --start").format(cmd_str)
        comment = ("Test case {0} - Invalid basedir with --start "
                   "option.".format(test_num))
        res = self.run_test_case(2, cmd_opts, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        cmd_opts = ("{0} --format=vertical --basedir=. --datadir=not_exist"
                    " --start").format(cmd_str)
        comment = ("Test case {0} - Invalid datadir with --start "
                   "option.".format(test_num))
        res = self.run_test_case(2, cmd_opts, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        server_info.test.do_replacements(self)

        self.replace_result("ERROR: Server connection values invalid:",
                            "ERROR: Server connection values invalid\n")

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
