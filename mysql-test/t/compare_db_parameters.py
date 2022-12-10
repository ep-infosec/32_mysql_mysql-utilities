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
compare_db_parameters test.
"""

import compare_db

from mysql.utilities.exception import MUTLibError

_COMPACT_OUTPUT = ['', ' --compact']
_DIFF_FORMATS = ['unified', 'context', 'differ']
_OUTPUT_FORMATS = ['grid', 'csv', 'tab', 'vertical']
_DIRECTIONS = ['server1', 'server2']


class test(compare_db.test):
    """check parameters for dbcompare
    This test executes a series of check database operations on two
    servers using a variety of parameters. It uses the compare_db test
    as a parent for setup and teardown methods.
    """

    def check_prerequisites(self):
        return compare_db.test.check_prerequisites(self)

    def setup(self, spawn_servers=True):
        return compare_db.test.setup(self)

    def run(self):
        self.server1 = self.servers.get_server(0)
        self.res_fname = "result.txt"

        s1_conn = "--server1={0}".format(
            self.build_connection_string(self.server1))
        s2_conn = "--server2={0}".format(
            self.build_connection_string(self.server2))

        cmd_str = ("mysqldbcompare.py {0} {1} "
                   "inventory:inventory ".format(s1_conn, s2_conn))

        test_num = 1
        cmd_opts = " --help"
        comment = "Test case {0} - Use{1} ".format(test_num, cmd_opts)
        res = self.run_test_case(0, cmd_str + cmd_opts, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        # Remove version information
        self.remove_result_and_lines_after("MySQL Utilities mysqldbcompare.py "
                                           "version", 6)

        compare_db.test.alter_data(self)
        self.server1.exec_query("DROP VIEW inventory.tools")

        for diff in _DIFF_FORMATS:
            for fmt in _OUTPUT_FORMATS:
                test_num += 1
                cmd_opts = (" -t --difftype={0} --format={1}"
                            "").format(diff, fmt)
                comment = "Test case {0} - Use {1}".format(test_num, cmd_opts)
                res = self.run_test_case(1,
                                         "{0}{1}".format(cmd_str, cmd_opts),
                                         comment)
                if not res:
                    raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        cmd_opts = " -d differ --format=csv"
        comment = "Test case {0} - without force ".format(test_num)
        res = self.run_test_case(1, cmd_str + cmd_opts, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        cmd_opts += " --quiet -t"
        comment = "Test case {0} - {1}".format(test_num, cmd_opts)
        res = self.run_test_case(1, cmd_str + cmd_opts, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        cmd_str_all = ("mysqldbcompare.py {0} {1} ".format(s1_conn, s2_conn))
        cmd_opts_all = "--quiet --all  "
        comment = "Test case {0} - {1}".format(test_num, cmd_opts_all)
        res = self.run_test_case(1, cmd_str_all + cmd_opts_all, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        cmd_opts = " --format=csv -t"
        cmd_opts += " --width=65"
        comment = "Test case {0} - {1}".format(test_num, cmd_opts)
        res = self.run_test_case(1, cmd_str + cmd_opts, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        cmd_opts = " --format=csv -t"
        cmd_opts += " --width=60"  # Minimum width for data check results.
        comment = "Test case {0} - {1}".format(test_num, cmd_opts)
        res = self.run_test_case(1, cmd_str + cmd_opts, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        cmd_opts = " --format=csv -vvv -t"
        comment = "Test case {0} - {1}".format(test_num, cmd_opts)
        res = self.run_test_case(1, cmd_str + cmd_opts, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        cmd_opts = " --format=csv -vvv -t --disable-binary-logging"
        comment = "Test case {0} - {1}".format(test_num, cmd_opts)
        res = self.run_test_case(1, cmd_str + cmd_opts, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        cmd_opts = " --format=csv -vvv -t --span-key-size=16"
        comment = "Test case {0} - {1}".format(test_num, cmd_opts)
        cmd = "{0}{1}".format(cmd_str, cmd_opts)
        res = self.run_test_case(1, cmd, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        cmd_opts = "--span-key-size=9"
        comment = ("Test case {0} - Warning span size must be an even number: "
                   "{1}").format(test_num, cmd_opts)
        cmd = "{0}{1}".format(cmd_str, cmd_opts)
        res = self.run_test_case(1, cmd, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        # Test use of --skip-table-options (different AUTO_INCREMENT)
        difftype_options = ['', '--difftype=context', '--difftype=sql']
        cmd_base = ("mysqldbcompare.py {0} {1} "
                    "db_diff_test:db_diff_test -t --skip-row-count "
                    "--skip-data-check".format(s1_conn, s2_conn))

        for difftype_opt in difftype_options:
            for direct in _DIRECTIONS:
                test_num += 1
                comment = ("Test case {0}a - Changes for {1} {2} (not "
                           "skipping table options)."
                           "").format(test_num, direct, difftype_opt)
                cmd = ("{0} --changes-for={1} {2}"
                       "").format(cmd_base, direct, difftype_opt)
                res = self.run_test_case(1, cmd, comment)
                if not res:
                    raise MUTLibError("{0}: failed".format(comment))
                comment = ("Test case {0}b - Changes for {1} {2} "
                           "(skipping table options)."
                           "").format(test_num, direct, difftype_opt)
                cmd = ("{0} --changes-for={1} {2} "
                       "--skip-table-options").format(cmd_base, direct,
                                                      difftype_opt)
                res = self.run_test_case(0, cmd, comment)
                if not res:
                    raise MUTLibError("{0}: failed".format(comment))

        # the compact option tests, it does not applies to differ diff fmt
        _DIFF_FORMATS.remove('differ')
        for diff in _DIFF_FORMATS:
            for fmt in _OUTPUT_FORMATS:
                test_num += 1
                cmd_opts = (" -t --difftype={0} --format={1}{2}"
                            "").format(diff, fmt, _COMPACT_OUTPUT[1])
                comment = "Test case {0} - Use {1}".format(test_num,
                                                           cmd_opts)
                res = self.run_test_case(1,
                                         "{0}{1}".format(cmd_str, cmd_opts),
                                         comment)
                if not res:
                    raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        comment = ("Test case {0} - Warning using --exclude without "
                   "--all").format(test_num)
        cmd_opts = "--exclude=%"
        cmd = "{0}{1}".format(cmd_str, cmd_opts)
        res = self.run_test_case(1, cmd, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        comment = ("Test case {0} - Warning using --regexp without "
                   "--exclude").format(test_num)
        cmd_opts = "--regexp"
        cmd = "{0}{1}".format(cmd_str, cmd_opts)
        res = self.run_test_case(1, cmd, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        # Mask version
        self.replace_result(
            "MySQL Utilities mysqldbcompare version",
            "MySQL Utilities mysqldbcompare version X.Y.Z\n")

        compare_db.test.do_replacements(self)

        return True

    def get_result(self):
        return self.compare(__name__, self.results)

    def record(self):
        return self.save_result_file(__name__, self.results)

    def cleanup(self):
        return compare_db.test.cleanup(self)
