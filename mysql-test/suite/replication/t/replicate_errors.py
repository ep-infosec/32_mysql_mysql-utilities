#
# Copyright (c) 2010, 2016, Oracle and/or its affiliates. All rights reserved.
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
replicate_errors test.
"""

import socket

import replicate
import mutlib

from mysql.utilities.exception import MUTLibError


class test(replicate.test):
    """check error conditions
    This test ensures the known error conditions are tested. It uses the
    cloneuser test as a parent for setup and teardown methods.
    """

    server3 = None
    port3 = None

    def check_prerequisites(self):
        return replicate.test.check_prerequisites(self)

    def setup(self):
        self.server3 = None
        return replicate.test.setup(self)

    def run(self):
        self.res_fname = "result.txt"

        master_str = "--master={0}".format(
            self.build_connection_string(self.server2))
        slave_str = " --slave={0}".format(
            self.build_connection_string(self.server1))

        cmd_str = "mysqlreplicate.py "

        test_num = 1
        comment = ("Test case {0} - error: cannot parse server "
                   "(slave)".format(test_num))
        res = mutlib.System_test.run_test_case(
            self, 2, "{0}{1} --slave=wikiwokiwonky --rpl-user=rpl:"
                     "whatsit".format(cmd_str, master_str), comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        comment = ("Test case {0} - error: cannot parse server "
                   "(master)".format(test_num))
        res = mutlib.System_test.run_test_case(
            self, 2, "{0}{1} --master=wikiwakawonky --rpl-user=rpl:"
                     "whatsit".format(cmd_str, slave_str), comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        comment = ("Test case {0} - error: invalid login to server "
                   "(master)".format(test_num))
        res = mutlib.System_test.run_test_case(
            self, 1, "{0}{1} --master=nope:nada@localhost:5510 --rpl-user=rpl:"
                     "whatsit".format(cmd_str, slave_str), comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        comment = ("Test case {0} - error: invalid login to server "
                   "(slave)".format(test_num))
        res = mutlib.System_test.run_test_case(
            self, 1, "{0}{1} --slave=nope:nada@localhost:5511 --rpl-user=rpl:"
                     "whatsit".format(cmd_str, master_str), comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        conn_str = self.build_connection_string(self.server1)
        same_str = "--master={0} --slave={0} ".format(conn_str)

        test_num += 1
        comment = ("Test case {0}a - error: slave and master same "
                   "machine".format(test_num))
        res = mutlib.System_test.run_test_case(
            self, 2, "{0}{1}--rpl-user=rpl:whatsit".format(cmd_str, same_str),
            comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        conn_str = self.build_connection_string(self.server1)
        same_str = "--master={0} --slave=root:root@{1}:{2} ".format(
            conn_str, socket.gethostname().split('.', 1)[0],
            self.server1.port)
        comment = ("Test case {0}b - error: slave and master same "
                   "alias/host".format(test_num))
        res = mutlib.System_test.run_test_case(
            self, 2, "{0}{1}--rpl-user=rpl:whatsit".format(cmd_str, same_str),
            comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        # Now we must muck with the servers. We need to turn binary logging
        # off for the next test case.

        self.port3 = int(self.servers.get_next_port())
        res = self.servers.start_new_server(self.server0,
                                            self.port3,
                                            self.servers.get_next_id(),
                                            "root", "temprep1")
        self.server3 = res[0]
        if not self.server3:
            raise MUTLibError("{0}: Failed to create a new slave.".format(
                comment))

        new_server_str = self.build_connection_string(self.server3)
        new_master_str = self.build_connection_string(self.server1)

        cmd_str = "mysqlreplicate.py --master={0} {1}".format(new_server_str,
                                                              slave_str)

        test_num += 1
        comment = ("Test case {0} - error: No binary logging on "
                   "master".format(test_num))
        cmd = cmd_str + " --rpl-user=rpl:whatsit "
        res = mutlib.System_test.run_test_case(self, 1, cmd, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        self.server3.exec_query("CREATE USER dummy@localhost")
        self.server3.exec_query("GRANT SELECT ON *.* TO dummy@localhost")
        self.server1.exec_query("CREATE USER dummy@localhost")
        self.server1.exec_query("GRANT SELECT ON *.* TO dummy@localhost")

        test_num += 1
        comment = "Test case {0} - error: replicate() fails".format(test_num)

        conn = self.get_connection_values(self.server3)

        cmd = "mysqlreplicate.py --slave=dummy@localhost"
        if conn[3] is not None:
            cmd = "{0}:{1}".format(cmd, conn[3])
        if conn[4] is not None and conn[4] != "":
            cmd = "{0}:{1}".format(cmd, conn[4])
        cmd = "{0} --rpl-user=rpl:whatsit --master={1}".format(
            cmd, new_master_str)
        res = mutlib.System_test.run_test_case(self, 1, cmd, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        cmd_str = "mysqlreplicate.py {0} {1}".format(master_str, slave_str)

        res = self.server2.show_server_variable("server_id")
        if not res:
            raise MUTLibError("Cannot get master's server id.")
        master_serverid = res[0][1]

        self.server2.exec_query("SET GLOBAL server_id = 0")

        test_num += 1
        comment = "Test case {0} - error: Master server id = 0".format(
            test_num)
        cmd = "{0} --rpl-user=rpl:whatsit ".format(cmd_str)
        res = mutlib.System_test.run_test_case(self, 1, cmd, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        self.server2.exec_query("SET GLOBAL server_id = {0}".format(
            master_serverid))

        res = self.server1.show_server_variable("server_id")
        if not res:
            raise MUTLibError("Cannot get slave's server id.")
        slave_serverid = res[0][1]

        self.server1.exec_query("SET GLOBAL server_id = 0")

        test_num += 1
        comment = "Test case {0} - error: Slave server id = 0".format(test_num)
        cmd = cmd_str + " --rpl-user=rpl:whatsit "
        res = mutlib.System_test.run_test_case(self, 1, cmd, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        self.server1.exec_query("SET GLOBAL server_id = {0}".format(
            slave_serverid))

        test_num += 1
        comment = ("Test case {0} - --master-log-pos but no log "
                   "file".format(test_num))
        cmd_opts = "--master-log-pos=96 "
        res = mutlib.System_test.run_test_case(self, 2, cmd + cmd_opts,
                                               comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        comment = ("Test case {0} - --master-log-file and "
                   "--start-from-beginning".format(test_num))
        cmd_opts = "--master-log-file='mysql_bin.00005' --start-from-beginning"
        res = mutlib.System_test.run_test_case(self, 2, cmd + cmd_opts,
                                               comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        comment = ("Test case {0} - --master-log-pos and "
                   "--start-from-beginning".format(test_num))
        cmd_opts = "--master-log-pos=96 --start-from-beginning"
        res = mutlib.System_test.run_test_case(self, 2, cmd + cmd_opts,
                                               comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        comment = ("Test case {0} - --master-log-file+pos and "
                   "--start-from-beginning".format(test_num))
        cmd_opts = ("--master-log-pos=96 --start-from-beginning "
                    "--master-log-file='mysql_bin.00005'")
        res = mutlib.System_test.run_test_case(self, 2, cmd + cmd_opts,
                                               comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        comment = "Test case {0} - no options used".format(test_num)
        cmd = "mysqlreplicate.py"
        res = self.run_test_case(2, cmd, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        comment = "Test case {0} - option --slave missing".format(test_num)
        cmd = "mysqlreplicate.py {0}".format(master_str)
        res = self.run_test_case(2, cmd, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        comment = "Test case {0} - option --rpl-user missing".format(test_num)
        cmd = "mysqlreplicate.py {0} {1}".format(master_str, slave_str)
        res = self.run_test_case(2, cmd, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        # Mask known platform-dependent lines
        self.mask_result("Error 2005:", "(1", '#######')
        self.replace_substring(" (42000)", "")
        self.replace_result("ERROR: Query failed. 1227",
                            "ERROR: Query failed. 1227: Access denied;\n")

        self.replace_any_result(
            ["ERROR: Can't connect to MySQL server on",
             "Error 2002: Can't connect to", "Error 2003: Can't connect to",
             "Error Can't connect to MySQL server on "],
            "Error ####: Can't connect to local MySQL server ####...\n")

        self.replace_result("mysqlreplicate: error: Master connection "
                            "values invalid",
                            "mysqlreplicate: error: Master connection "
                            "values invalid\n")
        self.replace_result("mysqlreplicate: error: Slave connection "
                            "values invalid",
                            "mysqlreplicate: error: Slave connection "
                            "values invalid\n")

        return True

    def get_result(self):
        return self.compare(__name__, self.results)

    def record(self):
        return self.save_result_file(__name__, self.results)

    def cleanup(self):
        if self.server3:
            self.servers.stop_server(self.server3)
            self.servers.remove_server(self.server3.role)
            self.server3 = None
        return replicate.test.cleanup(self)
