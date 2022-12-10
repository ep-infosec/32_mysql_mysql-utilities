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
diskusage_format test.
"""

import diskusage_basic

from mysql.utilities.exception import MUTLibError


class test(diskusage_basic.test):
    """Disk usage
    This test executes the disk space utility on a single server.
    It uses the diskusage_basic test for setup and teardown methods.
    """

    def check_prerequisites(self):
        return diskusage_basic.test.check_prerequisites(self)

    def setup(self):
        return diskusage_basic.test.setup(self)

    def run(self):
        self.res_fname = "result.txt"

        from_conn = "--server={0}".format(
            self.build_connection_string(self.server1))

        _FORMATS = ("CSV", "TAB", "GRID", "VERTICAL")

        cmd_base = "mysqldiskusage.py {0} util_test --format=".format(
            from_conn)
        test_num = 1
        for format_ in _FORMATS:
            comment = "Test Case {0} : Testing disk space with ".format(
                test_num)
            comment = "{0}{1} format ".format(comment, format_)

            res = self.run_test_case(0, cmd_base + format_, comment)
            if not res:
                raise MUTLibError("DISKUSAGE: {0}: failed".format(comment))

            test_num += 1

        comment = "Test Case %d : Testing disk space with " % test_num
        comment += "NOT_THERE format "
        res = self.run_test_case(2, cmd_base + "NOT_THERE", comment)
        if not res:
            raise MUTLibError("DISKUSAGE: %s: failed" % comment)

        diskusage_basic.test.mask(self)

        return True

    def get_result(self):
        return self.compare(__name__, self.results)

    def record(self):
        return self.save_result_file(__name__, self.results)

    def cleanup(self):
        return diskusage_basic.test.cleanup(self)
