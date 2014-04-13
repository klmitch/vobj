# Copyright 2013 Rackspace
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

import operator
import unittest

import mock
import six

from vobj import version


class SmartVersionTest(unittest.TestCase):
    def test_init_basic(self):
        sv = version.SmartVersion(5, 'schema')

        self.assertEqual(sv._version, 5)
        self.assertEqual(sv._schema, 'schema')
        self.assertEqual(sv._master, None)

    def test_init_master(self):
        sv = version.SmartVersion(5, 'schema', 'master')

        self.assertEqual(sv._version, 5)
        self.assertEqual(sv._schema, 'schema')
        self.assertEqual(sv._master, 'master')

    representations = {
        repr: repr(25),
        str: str(25),
        complex: complex(25),
        int: int(25),
        float: float(25),
    }
    if six.PY2:
        representations.update({
            unicode: unicode(25),
            long: long(25),
            oct: oct(25),
            hex: hex(25),
        })
    elif six.PY3:
        representations.update({
            round: round(25),
        })

    def test_representations(self):
        sv = version.SmartVersion(25, 'schema')

        for type_, expected in self.representations.items():
            result = type_(sv)

            self.assertEqual(type(expected), type(result))
            self.assertEqual(expected, result)

    comparisons = [
        (5, 7, {
            operator.lt: True,
            operator.le: True,
            operator.eq: False,
            operator.ne: True,
            operator.gt: False,
            operator.ge: False,
        }),
        (7, 5, {
            operator.lt: False,
            operator.le: False,
            operator.eq: False,
            operator.ne: True,
            operator.gt: True,
            operator.ge: True,
        }),
        (5, 5, {
            operator.lt: False,
            operator.le: True,
            operator.eq: True,
            operator.ne: False,
            operator.gt: False,
            operator.ge: True,
        }),
    ]

    def test_comparisons_integer(self):
        for lhs, rhs, truth_tab in self.comparisons:
            lhs = version.SmartVersion(lhs, 'schema')

            for op, expected in truth_tab.items():
                self.assertEqual(expected, op(lhs, rhs))

    def test_comparisons_smart_version(self):
        for lhs, rhs, truth_tab in self.comparisons:
            lhs = version.SmartVersion(lhs, 'schema')
            rhs = version.SmartVersion(rhs, 'schema')

            for op, expected in truth_tab.items():
                self.assertEqual(expected, op(lhs, rhs))

    def test_hash(self):
        for i in range(100):
            sv = version.SmartVersion(i, 'schema')

            self.assertEqual(hash(i), hash(sv))

    def test_bool(self):
        for i in range(100):
            sv = version.SmartVersion(i, 'schema')

            self.assertEqual(True, bool(sv))

    binary_operators = [
        operator.add, operator.sub, operator.mul,
        operator.floordiv, operator.truediv, operator.mod, divmod, pow,
        operator.lshift, operator.rshift, operator.and_, operator.xor,
        operator.or_,
    ]
    if six.PY2:
        binary_operators.append(operator.div)

    def test_binary_operators_integer(self):
        for op in self.binary_operators:
            expected = op(25, 35)
            lhs = version.SmartVersion(25, 'schema')

            result = op(lhs, 35)

            self.assertEqual(expected, result)

    def test_binary_operators_smart_version(self):
        for op in self.binary_operators:
            expected = op(25, 35)
            lhs = version.SmartVersion(25, 'schema')
            rhs = version.SmartVersion(35, 'schema')

            result = op(lhs, rhs)

            self.assertEqual(expected, result)

    def test_binary_operators_reflected(self):
        for op in self.binary_operators:
            expected = op(25, 35)
            rhs = version.SmartVersion(35, 'schema')

            result = op(25, rhs)

            self.assertEqual(expected, result)

    def test_pow_modulo_integer(self):
        expected = pow(25, 35, 15)
        lhs = version.SmartVersion(25, 'schema')

        result = pow(lhs, 35, 15)

    def test_pow_modulo_smart_version(self):
        expected = pow(25, 35, 15)
        lhs = version.SmartVersion(25, 'schema')
        rhs = version.SmartVersion(35, 'schema')
        modulo = version.SmartVersion(15, 'schema')

        result = pow(lhs, rhs, modulo)

        self.assertEqual(expected, result)

    unary_operators = [
        operator.neg, operator.pos, abs, operator.invert, operator.index,
    ]

    def test_unary_operators(self):
        for op in self.unary_operators:
            expected = op(25)
            sv = version.SmartVersion(25, 'schema')

            result = op(sv)

            self.assertEqual(expected, result)

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
