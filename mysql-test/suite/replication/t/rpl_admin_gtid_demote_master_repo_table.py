#
# Copyright (c) 2013, 2015, Oracle and/or its affiliates. All rights reserved.
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
rpl_admin_gtid_demote_master_repo_table test.
"""

import rpl_admin

from mysql.utilities.exception import MUTLibError


_DEFAULT_MYSQL_OPTS = ('"--log-bin=mysql-bin --skip-slave-start '
                       '--log-slave-updates --gtid-mode=on '
                       '--enforce-gtid-consistency --report-host=localhost '
                       '--report-port={0} '
                       '--master-info-repository=table"')


class test(rpl_admin.test):
    """test replication administration commands
    This test runs the mysqlrpladmin utility on a known topology.

    Note: this test requires GTID enabled servers.
    """

    def check_prerequisites(self):
        if not self.servers.get_server(0).check_version_compat(5, 6, 9):
            raise MUTLibError("Test requires server version 5.6.9")
        return self.check_num_servers(1)

    def setup(self):
        self.res_fname = "result.txt"

        # Spawn servers
        self.server0 = self.servers.get_server(0)
        mysqld = _DEFAULT_MYSQL_OPTS.format(self.servers.view_next_port())
        self.server1 = self.servers.spawn_server("rep_master_gtid", mysqld,
                                                 True)
        mysqld = _DEFAULT_MYSQL_OPTS.format(self.servers.view_next_port())
        self.server2 = self.servers.spawn_server("rep_slave1_gtid", mysqld,
                                                 True)
        mysqld = _DEFAULT_MYSQL_OPTS.format(self.servers.view_next_port())
        self.server3 = self.servers.spawn_server("rep_slave2_gtid", mysqld,
                                                 True)
        mysqld = _DEFAULT_MYSQL_OPTS.format(self.servers.view_next_port())
        self.server4 = self.servers.spawn_server("rep_slave3_gtid", mysqld,
                                                 True)

        # Reset spawned servers (clear binary log and GTID_EXECUTED set)
        self.reset_master()

        self.m_port = self.server1.port
        self.s1_port = self.server2.port
        self.s2_port = self.server3.port
        self.s3_port = self.server4.port

        rpl_admin.test.reset_topology(self)

        return True

    def run(self):
        test_num = 1

        master_conn = self.build_connection_string(self.server1).strip(' ')
        slave1_conn = self.build_connection_string(self.server2).strip(' ')

        comment = ("Test case {0} - mysqlrplshow OLD Master before "
                   "demote".format(test_num))
        cmd_str = "mysqlrplshow.py --master={0} ".format(master_conn)
        #  --master=root:root@localhost:13091 --disco=root:root -r
        cmd_opts = "--discover-slaves={0} -r".format(master_conn.split('@')[0])
        res = self.run_test_case(0, cmd_str + cmd_opts, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        # mysqlrpladmin --master=root:root@localhost:13091
        # --new-master=root:root@localhost:13094
        # --discover-slaves-login=root:root --demote-master  switchover
        # --rpl-user=rpl:rplpass
        comment = ("Test case {0} - demote-master after switchover "
                   "-vvv".format(test_num))
        cmd_str = "mysqlrpladmin.py --master={0} ".format(master_conn)
        cmd_opts = (" --new-master={0} --discover-slaves={1} "
                    "--rpl-user=rpluser:hispassword --demote-master "
                    "switchover -vvv".format(slave1_conn,
                                             master_conn.split('@')[0]))
        res = self.run_test_case(0, cmd_str + cmd_opts, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))
        self.results.append("\n")

        test_num += 1
        comment = ("Test case {0} - mysqlrplshow OLD Master after "
                   "demote".format(test_num))
        cmd_str = "mysqlrplshow.py --master={0} ".format(master_conn)
        #  --master=root:root@localhost:13091 --disco=root:root -r
        cmd_opts = "--discover-slaves={0} -r".format(master_conn.split('@')[0])
        res = self.run_test_case(0, cmd_str + cmd_opts, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        comment = ("Test case {0} - mysqlrplshow NEW Master after "
                   "demote".format(test_num))
        cmd_str = "mysqlrplshow.py --master={0} ".format(slave1_conn)
        #  --master=root:root@localhost:13091 --disco=root:root -r
        cmd_opts = "--discover-slaves={0} -r".format(master_conn.split('@')[0])
        res = self.run_test_case(0, cmd_str + cmd_opts, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        # Now we return the topology to its original state for other tests
        rpl_admin.test.reset_topology(self)

        # Mask out non-deterministic data
        rpl_admin.test.do_masks(self)

        self.replace_result("# QUERY = SELECT "
                            "WAIT_UNTIL_SQL_THREAD_AFTER_GTIDS(",
                            "# QUERY = SELECT "
                            "WAIT_UNTIL_SQL_THREAD_AFTER_GTIDS(XXXXX)\n")
        self.replace_substring("localhost", "XXXXXXXXX")

        self.remove_result_and_lines_before("WARNING: Cannot connect to some "
                                            "slaves (--verbose for more "
                                            "details).")

        self.replace_result("| XXXXXXXXX  | PORT2  | MASTER  | UP     "
                            "| ON         | OK      | ",
                            "| XXXXXXXXX  | PORT2  | MASTER  | UP     "
                            "| ON         | OK      | XXXXXXXX    "
                            "| XXXXXXXX          | XXXXXXXX        "
                            "|            |             |              "
                            "|                  |               |           "
                            "|                |            "
                            "|               |\n")

        self.replace_result("| XXXXXXXXX  | PORT1  | SLAVE   | UP     "
                            "| ON         | OK      | ",
                            "| XXXXXXXXX  | PORT1  | SLAVE   | UP     "
                            "| ON         | OK      | XXXXXXXX    "
                            "| XXXXXXXX          | XXXXXXXX        "
                            "| Yes        | Yes         | 0            "
                            "| No               | 0             |           "
                            "| 0              |            "
                            "| 0             |\n")

        self.replace_result("| XXXXXXXXX  | PORT3  | SLAVE   | UP     "
                            "| ON         | OK      | ",
                            "| XXXXXXXXX  | PORT3  | SLAVE   | UP     "
                            "| ON         | OK      | XXXXXXXX    "
                            "| XXXXXXXX          | XXXXXXXX        "
                            "| Yes        | Yes         | 0            "
                            "| No               | 0             |           "
                            "| 0              |            "
                            "| 0             |\n")

        self.replace_result("| XXXXXXXXX  | PORT4  | SLAVE   | UP     "
                            "| ON         | OK      | ",
                            "| XXXXXXXXX  | PORT4  | SLAVE   | UP     "
                            "| ON         | OK      | XXXXXXXX    "
                            "| XXXXXXXX          | XXXXXXXX        "
                            "| Yes        | Yes         | 0            "
                            "| No               | 0             |           "
                            "| 0              |            "
                            "| 0             |\n")

        self.mask_column_result("| version", "|", 2, " XXXXXXXX ")
        self.mask_column_result("| master_log_file", "|", 2, " XXXXXXXX ")
        self.mask_column_result("| master_log_pos", "|", 2, " XXXXXXXX ")
        self.replace_result("# Return Code = 0",
                            "# Return Code = NNN\n")

        return True

    def get_result(self):
        return self.compare(__name__, self.results)

    def record(self):
        return self.save_result_file(__name__, self.results)

    def cleanup(self):
        # Kill all spawned servers.
        self.kill_server_list(
            ['rep_master_gtid', 'rep_slave1_gtid', 'rep_slave2_gtid',
             'rep_slave3_gtid']
        )
        return rpl_admin.test.cleanup(self)
