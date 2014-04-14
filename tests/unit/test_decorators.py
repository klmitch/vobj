# Copyright 2013, 2014 Rackspace
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import unittest

from vobj import decorators


class UpgraderTest(unittest.TestCase):
    def test_no_arg(self):
        @decorators.upgrader
        def test():
            pass

        self.assertEqual(test.__vers_upgrader__, None)

    def test_empty_arg(self):
        @decorators.upgrader()
        def test():
            pass

        self.assertEqual(test.__vers_upgrader__, None)

    def test_int_arg(self):
        @decorators.upgrader(5)
        def test():
            pass

        self.assertEqual(test.__vers_upgrader__, 5)

    def test_int_arg_low(self):
        self.assertRaises(TypeError, decorators.upgrader, 0)

    def test_other_arg(self):
        self.assertRaises(TypeError, decorators.upgrader, 'other')


class DowngraderTest(unittest.TestCase):
    def test_int_arg(self):
        @decorators.downgrader(5)
        def test():
            pass

        self.assertEqual(test.__vers_downgrader__, 5)

    def test_int_arg_low(self):
        self.assertRaises(TypeError, decorators.downgrader, 0)

    def test_other_arg(self):
        self.assertRaises(TypeError, decorators.downgrader, 'other')
