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
compare_db_errors test.
"""

import os

import compare_db

from mysql.utilities.exception import MUTLibError, UtilError


class test(compare_db.test):
    """check errors for dbcompare
    This test executes a series of error conditions for the check database
    utility. It uses the compare_db test as a parent for setup and teardown
    methods.
    """

    def check_prerequisites(self):
        return compare_db.test.check_prerequisites(self)

    def setup(self, spawn_servers=True):
        self.server1 = self.servers.get_server(0)
        if self.need_server:
            try:
                self.servers.spawn_new_servers(2)
            except MUTLibError as err:
                raise MUTLibError("Cannot spawn needed servers: {0}".format(
                    err.errmsg))
        self.server2 = self.servers.get_server(1)
        self.drop_all()
        return True

    def run(self):
        self.res_fname = "result.txt"

        s1_conn = "--server1=" + self.build_connection_string(self.server1)
        s2_conn = "--server2=" + self.build_connection_string(self.server2)

        test_num = 1
        cmd_str = "mysqldbcompare.py -t -vvv inventory:inventory "
        cmd_opts = "--server1=joeunk:@:dooer " + s2_conn
        comment = "Test case {0} - Invalid --server1 ".format(test_num)
        res = self.run_test_case(2, cmd_str + cmd_opts, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        cmd_opts = "--server2=joeunk:@:dooer " + s1_conn
        comment = "Test case {0} - Invalid --server2 ".format(test_num)
        res = self.run_test_case(2, cmd_str + cmd_opts, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        cmd_str = "mysqldbcompare.py {0} {1}".format(s1_conn, s2_conn)
        cmd_opts = " inventory.inventory"
        comment = ("Test case {0} - missing backticks{1} "
                   "".format(test_num, cmd_opts))
        res = self.run_test_case(2, cmd_str + cmd_opts, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        # Set input parameter with appropriate quotes for the OS
        if os.name == 'posix':
            cmd_opts = "'`inventory.inventory`'"
        else:
            cmd_opts = '"`inventory.inventory`"'
        cmd_str = "mysqldbcompare.py {0} {1} {2}".format(s1_conn, s2_conn,
                                                         cmd_opts)
        comment = ("Test case {0} - non existing database "
                   "'`inventory.inventory`'".format(test_num))
        res = self.run_test_case(1, cmd_str, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        cmd_str = "mysqldbcompare.py {0} {1}".format(s1_conn, s2_conn)
        cmd_opts = " :inventory"
        comment = ("Test case {0} - invalid format{1} ".format(test_num,
                                                               cmd_opts))
        res = self.run_test_case(2, cmd_str + cmd_opts, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        cmd_opts = "--span-key-size=A"
        cmd_str = ("mysqldbcompare.py {0} {1} inventory:inventory "
                   "{2}").format(s1_conn, s2_conn, cmd_opts)
        comment = ("Test case {0} - invalid value for {1} "
                   "").format(test_num, cmd_opts)
        res = self.run_test_case(2, cmd_str, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        cmd_opts = "--span-key-size=16.6"
        cmd_str = ("mysqldbcompare.py {0} {1} inventory:inventory "
                   "{2}").format(s1_conn, s2_conn, cmd_opts)
        comment = ("Test case {0} - invalid value for {1} "
                   "").format(test_num, cmd_opts)
        res = self.run_test_case(2, cmd_str, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        cmd_opts = "--span-key-size=0"
        cmd_str = ("mysqldbcompare.py {0} {1} inventory:inventory "
                   "{2}").format(s1_conn, s2_conn, cmd_opts)
        comment = ("Test case {0} - span size equal to zero: {1} "
                   "").format(test_num, cmd_opts)
        res = self.run_test_case(2, cmd_str, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        cmd_opts = "--span-key-size=-4"
        cmd_str = ("mysqldbcompare.py {0} {1} inventory:inventory "
                   "{2}").format(s1_conn, s2_conn, cmd_opts)
        comment = ("Test case {0} - size too low for {1} "
                   "").format(test_num, cmd_opts)
        res = self.run_test_case(2, cmd_str, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        cmd_opts = "--span-key-size=33"
        cmd_str = ("mysqldbcompare.py {0} {1} inventory:inventory "
                   "{2}").format(s1_conn, s2_conn, cmd_opts)
        comment = ("Test case {0} - size too high for {1} "
                   "").format(test_num, cmd_opts)
        res = self.run_test_case(2, cmd_str, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        cmd_str = "mysqldbcompare.py"
        comment = "Test case {0} - no options".format(test_num)
        res = self.run_test_case(2, cmd_str, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        # Add two tables without primary keys
        self.server1.exec_query("CREATE DATABASE inventory")
        self.server1.exec_query("CREATE TABLE inventory.box (a int) "
                                "ENGINE=INNODB")
        self.server1.exec_query("INSERT INTO inventory.box VALUES (1)")
        # index with nullable collumn
        self.server1.exec_query("CREATE TABLE inventory.box_2 "
                                "(a int, b int, INDEX `ix_nullable` (`a`)) "
                                "ENGINE=INNODB")
        self.server1.exec_query("INSERT INTO inventory.box_2 VALUES (1, 2)")
        self.server2.exec_query("CREATE DATABASE inventory")
        self.server2.exec_query("CREATE TABLE inventory.box (a int) "
                                "ENGINE=INNODB")
        self.server2.exec_query("INSERT INTO inventory.box VALUES (2)")
        # index with nullable collumn
        self.server2.exec_query("CREATE TABLE inventory.box_2 "
                                "(a int, b int, INDEX `ix_nullable` (`a`)) "
                                "ENGINE=INNODB")
        self.server2.exec_query("INSERT INTO inventory.box_2 VALUES (2, 1)")

        test_num += 1
        cmd_str = ("mysqldbcompare.py {0} {1} {2} "
                   "".format(s1_conn, s2_conn, "inventory:inventory -t"))
        comment = ("Test case {0} - No pri key".format(test_num))
        res = self.run_test_case(1, cmd_str, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        cmd_str = ("mysqldbcompare.py {0} {1} {2} "
                   "--character-set=unsupported_charset"
                   "".format(s1_conn, s2_conn, "inventory:inventory -t"))
        comment = ("Test case {0} - Invalid --character-set"
                   "".format(test_num))
        res = self.run_test_case(1, cmd_str, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        # invalid index
        self.server1.exec_query("CREATE TABLE inventory.box_3 "
                                "(a int not null, b int, "
                                "UNIQUE `uk_nonull` (`a`))ENGINE=INNODB")
        self.server1.exec_query("INSERT INTO inventory.box_3 VALUES (2, 1)")
        # invalid index
        self.server2.exec_query("CREATE TABLE inventory.box_3 "
                                "(a int not null, b int, UNIQUE "
                                "`uk_nonull` (`a`)) ENGINE=INNODB")
        self.server2.exec_query("INSERT INTO inventory.box_3 VALUES (2, 1)")

        # different index
        self.server1.exec_query(
            "CREATE TABLE inventory.box_4 "
            "(a int not null, b int, c int, d int not null, "
            "UNIQUE `uk_nonull` (`d`), INDEX `ix_nonull` (`a`))ENGINE=INNODB"
        )
        self.server1.exec_query("INSERT INTO inventory.box_4 VALUES "
                                "(1, 2, 3, 4)")
        # different index
        self.server2.exec_query(
            "CREATE TABLE inventory.box_4 "
            "(a int not null, b int not null, c int, d int not null, UNIQUE "
            "`uk_nonull` (`a`, `b`)) ENGINE=INNODB"
        )
        self.server2.exec_query("INSERT INTO inventory.box_4 VALUES "
                                "(2, 1, 4, 3)")

        test_num += 1
        cmd_str = ("mysqldbcompare.py {0} {1} {2} --skip-checksum-table "
                   "--use-indexes=box_3.invalid_index --skip-diff"
                   "".format(s1_conn, s2_conn, "inventory:inventory -t"))
        comment = ("Test case {0} - Invalid --use-indexes and different "
                   "indexes".format(test_num))
        res = self.run_test_case(1, cmd_str, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        comment = ("Test case {0} - Cannot use --all with a database argument"
                   ".").format(test_num)
        cmd_str = ("mysqldbcompare.py {0} {1} {2}"
                   "".format(s1_conn, s2_conn, "--all inventory:inventory"))
        res = self.run_test_case(2, cmd_str, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        cmd_str = "mysqldbcompare.py {0}".format("inventory")
        comment = ("Test case {0} - Option --server1 is required"
                   ".").format(test_num)
        res = self.run_test_case(2, cmd_str, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        cmd_str = "mysqldbcompare.py {0} {1}".format(s1_conn, "--all")
        comment = ("Test case {0} - Option --server2 is required"
                   ".").format(test_num)
        res = self.run_test_case(2, cmd_str, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        comment = ("Test case {0} - Cannot compare all databases on the same "
                   "server.").format(test_num)
        s1_conn_local = s1_conn.replace('localhost', '127.0.0.1')
        s2_conn_same_srv = s1_conn.replace('127.0.0.1', 'localhost')
        s2_conn_same_srv = s2_conn_same_srv.replace('--server1', '--server2')
        cmd_str = ("mysqldbcompare.py {0} {1} {2}"
                   "".format(s1_conn_local, s2_conn_same_srv, "--all"))
        res = self.run_test_case(1, cmd_str, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        comment = ("Test case {0} - Comparing the same object on the same "
                   "server.").format(test_num)
        cmd_str = ("mysqldbcompare.py {0} {1} {2}"
                   "".format(s1_conn_local, s2_conn_same_srv,
                             "inventory:inventory"))
        res = self.run_test_case(1, cmd_str, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        comment = ("Test case {0} - Cannot compare all databases on the same "
                   "server and with the same connection string."
                   "").format(test_num)
        s2_conn_same_srv = s1_conn.replace('--server1', '--server2')
        cmd_str = ("mysqldbcompare.py {0} {1} {2}"
                   "".format(s1_conn, s2_conn_same_srv, "--all"))
        res = self.run_test_case(1, cmd_str, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        self.server1.exec_query("CREATE DATABASE db_latin "
                                "DEFAULT CHARACTER SET = latin1")
        self.server2.exec_query("CREATE DATABASE db_latin "
                                "DEFAULT CHARACTER SET = latin2")
        comment = ("Test case {0} - Compare databases where there "
                   "only the decorators differ for CREATE").format(test_num)
        s2_conn_same_srv = s1_conn.replace('--server1', '--server2')
        cmd_str = ("mysqldbcompare.py {0} {1} {2}"
                   "".format(s1_conn, s2_conn, "db_latin:db_latin"))
        res = self.run_test_case(1, cmd_str, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        # Mask output..
        self.replace_substring(str(self.server1.port), "PORT1")
        self.replace_result("mysqldbcompare: error: Server1 connection "
                            "values invalid",
                            "mysqldbcompare: error: Server1 connection "
                            "values invalid\n")
        self.replace_result("mysqldbcompare: error: Server2 connection "
                            "values invalid",
                            "mysqldbcompare: error: Server2 connection "
                            "values invalid\n")

        self.replace_substring("on [::1]", "on localhost")

        return True

    def get_result(self):
        return self.compare(__name__, self.results)

    def record(self):
        return self.save_result_file(__name__, self.results)

    def cleanup(self):
        dbs = ['inventory', 'db_latin']
        for db in dbs:
            try:
                self.server1.exec_query("DROP DATABASE IF EXISTS "
                                        "{0}".format(db))
            except UtilError as err:
                raise MUTLibError("Unable to drop {0} database: "
                                  "{1} on server1".format(db, err.errmsg))
            try:
                self.server2.exec_query("DROP DATABASE IF EXISTS "
                                        "{0}".format(db))
            except UtilError as err:
                raise MUTLibError("Unable to drop {0} database: "
                                  "{1} on server2".format(db, err.errmsg))
        return compare_db.test.cleanup(self)
