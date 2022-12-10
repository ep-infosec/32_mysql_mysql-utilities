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
check_rpl_errors test.
"""

import socket

import check_rpl
import mutlib

from mysql.utilities.exception import MUTLibError


class test(check_rpl.test):
    """check replication conditions
    This test runs the mysqlrplcheck utility on a known master-slave topology
    to test various errors. It uses the check_rpl test as a parent for
    setup and teardown methods.

    Note: Many of the errors from the mysqlreplicate utility are not included
    in this test. Additionally, errors that require unique setup conditions
    cannot be tested easily. Thus, the errors represented in this test cover
    only the mysqlrplcheck utility and command/rpl.py file.
    """

    def check_prerequisites(self):
        return check_rpl.test.check_prerequisites(self)

    def setup(self):
        return check_rpl.test.setup(self)

    def run(self):
        self.res_fname = "result.txt"

        master_str = "--master={0}".format(
            self.build_connection_string(self.server2))
        slave_str = " --slave={0}".format(
            self.build_connection_string(self.server1))
        conn_str = master_str + slave_str

        cmd = "mysqlreplicate.py --rpl-user=rpl:rpl "
        try:
            self.exec_util(cmd, self.res_fname)
        except MUTLibError as err:
            raise MUTLibError(err.errmsg)

        cmd_str = "mysqlrplcheck.py " + conn_str

        test_num = 1
        comment = "Test case {0} - master parameter invalid".format(test_num)
        cmd_opts = " {0} --master=root_root_root".format(slave_str)
        res = mutlib.System_test.run_test_case(self, 2, cmd_str + cmd_opts,
                                               comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        comment = "Test case {0} - slave parameter invalid".format(test_num)
        cmd_opts = " {0} --slave=root_root_root".format(master_str)
        res = mutlib.System_test.run_test_case(self, 2, cmd_str + cmd_opts,
                                               comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        comment = ("Test case {0} - same server literal "
                   "specification".format(test_num))
        same_str = self.build_connection_string(self.server2)
        cmd_opts = " --master={0} --slave={1}".format(same_str, same_str)
        res = mutlib.System_test.run_test_case(self, 2, cmd_str + cmd_opts,
                                               comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        comment = ("Test case {0} - error: invalid login to server "
                   "(master)".format(test_num))
        res = mutlib.System_test.run_test_case(
            self, 1, "{0}{1} --master=nope:nada@localhost:"
                     "5510".format(cmd_str, slave_str), comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        comment = ("Test case {0} - error: invalid login to server "
                   "(slave)".format(test_num))
        res = mutlib.System_test.run_test_case(
            self, 1, "{0}{1} --slave=nope:nada@localhost:"
                     "5511".format(cmd_str, master_str), comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        comment = "Test case {0} - master and slave same host".format(test_num)
        res = mutlib.System_test.run_test_case(
            self, 2, "{0}{1} --slave=root:root@{2}:{3}".format(
                cmd_str, master_str, socket.gethostname().split('.', 1)[0],
                self.server2.port), comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        comment = "Test case {0} - no options used".format(test_num)
        cmd = "mysqlrplcheck.py"
        res = self.run_test_case(2, cmd, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        comment = "Test case {0} - option --slave missing".format(test_num)
        cmd = "mysqlrplcheck.py {0}".format(master_str)
        res = self.run_test_case(2, cmd, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        self.do_replacements()

        # Mask known platform-dependent lines
        self.mask_result("Error 2005:", "(1", '#######')
        self.replace_substring(" (42000)", "")
        self.replace_result("ERROR: Query failed. 1227: Access denied;",
                            "ERROR: Query failed. 1227: Access denied;\n")

        self.replace_any_result(
            ["ERROR: Can't connect",
             "Error 2002: Can't connect to", "Error 2003: Can't connect to",
             "Error Can't connect to MySQL server on "],
            "Error ####: Can't connect to local MySQL server ####...\n")

        self.replace_result("mysqlrplcheck: error: Master connection "
                            "values invalid",
                            "mysqlrplcheck: error: Master connection "
                            "values invalid\n")
        self.replace_result("mysqlrplcheck: error: Slave connection "
                            "values invalid",
                            "mysqlrplcheck: error: Slave connection "
                            "values invalid\n")

        return True

    def get_result(self):
        return self.compare(__name__, self.results)

    def record(self):
        return self.save_result_file(__name__, self.results)

    def cleanup(self):
        return check_rpl.test.cleanup(self)
