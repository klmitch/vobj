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

import mock

from vobj import version


class SmartVersionTest(unittest.TestCase):
    def test_new_basic(self):
        sv = version.SmartVersion(5, 'schema')

        self.assertEqual(sv._schema, 'schema')
        self.assertEqual(sv._master, None)

    def test_new_master(self):
        sv = version.SmartVersion(5, 'schema', 'master')

        self.assertEqual(sv._schema, 'schema')
        self.assertEqual(sv._master, 'master')

    def test_len_no_schema(self):
        sv = version.SmartVersion(1, None)

        self.assertEqual(len(sv), 0)

    def test_len_with_schema(self):
        schema = mock.Mock(__vers_downgraders__=range(5))
        sv = version.SmartVersion(1, schema)

        self.assertEqual(len(sv), 6)

    def test_contains_no_schema(self):
        sv = version.SmartVersion(1, None)

        self.assertFalse(5 in sv)

    def test_contains_with_schema(self):
        schema = mock.Mock(__vers_downgraders__={3: True}, __version__=4)
        sv = version.SmartVersion(1, schema)

        self.assertFalse(5 in sv)
        self.assertTrue(4 in sv)
        self.assertTrue(3 in sv)

    def test_getitem_no_master(self):
        schema = mock.Mock(__vers_downgraders__={3: True}, __version__=4)
        sv = version.SmartVersion(1, schema)

        self.assertRaises(RuntimeError, lambda: sv[4])

    def test_getitem_no_schema(self):
        master = mock.Mock(__vers_accessor__=mock.Mock(return_value='access'))
        sv = version.SmartVersion(1, None, master)

        self.assertRaises(KeyError, lambda: sv[4])
        self.assertFalse(master.__vers_accessor__.called)

    def test_getitem_return_master(self):
        schema = mock.Mock(__vers_downgraders__={3: True}, __version__=4)
        master = mock.Mock(__vers_accessor__=mock.Mock(return_value='access'))
        sv = version.SmartVersion(1, schema, master)

        result = sv[4]

        self.assertEqual(result, master)
        self.assertFalse(master.__vers_accessor__.called)

    def test_getitem_missing_downgrader(self):
        schema = mock.Mock(__vers_downgraders__={3: True}, __version__=4)
        master = mock.Mock(__vers_accessor__=mock.Mock(return_value='access'))
        sv = version.SmartVersion(1, schema, master)

        self.assertRaises(KeyError, lambda: sv[2])
        self.assertFalse(master.__vers_accessor__.called)

    def test_getitem(self):
        schema = mock.Mock(__vers_downgraders__={3: True}, __version__=4)
        master = mock.Mock(__vers_accessor__=mock.Mock(return_value='access'))
        sv = version.SmartVersion(1, schema, master)

        result = sv[3]

        self.assertEqual(result, "access")
        master.__vers_accessor__.assert_called_once_with(3)

    def test_available_no_schema(self):
        sv = version.SmartVersion(1, None)

        result = sv.available()

        self.assertEqual(result, set())

    def test_available_with_schema(self):
        schema = mock.Mock(__vers_downgraders__={3: True}, __version__=4)
        sv = version.SmartVersion(1, schema)

        result = sv.available()

        self.assertEqual(result, set([3, 4]))
