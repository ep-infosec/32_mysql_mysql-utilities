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
copy_user_errors test.
"""

import copy_user

from mysql.utilities.exception import MUTLibError


class test(copy_user.test):
    """clone user error conditions
    This test ensures the known error conditions are tested. It uses the
    cloneuser test as a parent for setup and teardown methods.
     """

    def check_prerequisites(self):
        return copy_user.test.check_prerequisites(self)

    def setup(self):
        return copy_user.test.setup(self)

    def run(self):
        self.res_fname = "result.txt"

        from_conn = "--source={0}".format(
            self.build_connection_string(self.server1))
        to_conn = "--destination={0}".format(
            self.build_connection_string(self.server2))

        cmd_str = ("mysqluserclone.py --source=noone:nope@localhost:3306 "
                   "{0}".format(to_conn))

        test_num = 1
        comment = ("Test case {0} - error: invalid login to source "
                   "server".format(test_num))
        res = self.run_test_case(1, cmd_str + " a@b b@c", comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        cmd_str = ("mysqluserclone.py --destination=noone:nope@localhost:3306 "
                   "{0}".format(from_conn))
        comment = ("Test case {0} - error: invalid login to destination "
                   "server".format(test_num))
        res = self.run_test_case(1, cmd_str + " a@b b@c", comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        cmd_str = "mysqluserclone.py {0} {1} ".format(from_conn, to_conn)
        comment = "Test case {0} - error: no arguments".format(test_num)
        res = self.run_test_case(2, cmd_str, comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        comment = "Test case {0} - error: no new user".format(test_num)
        res = self.run_test_case(2, cmd_str + "joenopass@localhost", comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        comment = ("Test case {0} - error: cannot use dump and quiet "
                   "together".format(test_num))
        res = self.run_test_case(2, cmd_str + " root@localhost  x@f --quiet "
                                              "--dump", comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        cmd_str = ("mysqluserclone.py --source=wikiwakawonky "
                   "{0} ".format(to_conn))
        comment = ("Test case {0} - error: cannot parser source "
                   "connection".format(test_num))
        res = self.run_test_case(2, cmd_str + " root@localhost x@f", comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        test_num += 1
        cmd_str = ("mysqluserclone.py --destination=wikiwakawonky "
                   "{0} ".format(from_conn))
        comment = ("Test case {0} - error: cannot parser destination "
                   "connection".format(test_num))
        res = self.run_test_case(2, cmd_str + " root@localhost x@f", comment)
        if not res:
            raise MUTLibError("{0}: failed".format(comment))

        # Replace error code.
        self.replace_any_result(["ERROR: Can't connect",
                                 "Error 1045", "Error 2003",
                                 "Error Can't connect to MySQL server on",
                                 "ERROR: Access denied for user",
                                 "Error Access denied for user"],
                                "Error XXXX: Access denied\n")

        self.replace_result("mysqluserclone: error: Source connection "
                            "values invalid",
                            "mysqluserclone: error: Source connection "
                            "values invalid\n")
        self.replace_result("mysqluserclone: error: Destination connection "
                            "values invalid",
                            "mysqluserclone: error: Destination connection "
                            "values invalid\n")

        self.replace_substring("on [::1]", "on localhost")

        return True

    def get_result(self):
        return self.compare(__name__, self.results)

    def record(self):
        return self.save_result_file(__name__, self.results)

    def cleanup(self):
        return copy_user.test.cleanup(self)
