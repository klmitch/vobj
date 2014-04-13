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

import copy
import operator
import unittest

import mock

import vobj


class EmptyClass(object):
    # Used to test __setstate__() on abstract Schemas
    pass


class TestSmartVersion(unittest.TestCase):
    def test_init_basic(self):
        sv = vobj.SmartVersion(5, 'schema')

        self.assertEqual(sv._version, 5)
        self.assertEqual(sv._schema, 'schema')
        self.assertEqual(sv._master, None)

    def test_init_master(self):
        sv = vobj.SmartVersion(5, 'schema', 'master')

        self.assertEqual(sv._version, 5)
        self.assertEqual(sv._schema, 'schema')
        self.assertEqual(sv._master, 'master')

    representations = {
        repr: repr(25),
        str: str(25),
        unicode: unicode(25),
        complex: complex(25),
        int: int(25),
        long: long(25),
        float: float(25),
        oct: oct(25),
        hex: hex(25),
    }

    def test_representations(self):
        sv = vobj.SmartVersion(25, 'schema')

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
            lhs = vobj.SmartVersion(lhs, 'schema')

            for op, expected in truth_tab.items():
                self.assertEqual(expected, op(lhs, rhs))

    def test_comparisons_smart_version(self):
        for lhs, rhs, truth_tab in self.comparisons:
            lhs = vobj.SmartVersion(lhs, 'schema')
            rhs = vobj.SmartVersion(rhs, 'schema')

            for op, expected in truth_tab.items():
                self.assertEqual(expected, op(lhs, rhs))

    def test_hash(self):
        for i in range(100):
            sv = vobj.SmartVersion(i, 'schema')

            self.assertEqual(hash(i), hash(sv))

    def test_nonzero(self):
        for i in range(100):
            sv = vobj.SmartVersion(i, 'schema')

            self.assertEqual(True, bool(sv))

    binary_operators = [
        operator.add, operator.sub, operator.mul, operator.div,
        operator.floordiv, operator.truediv, operator.mod, divmod, pow,
        operator.lshift, operator.rshift, operator.and_, operator.xor,
        operator.or_,
    ]

    def test_binary_operators_integer(self):
        for op in self.binary_operators:
            expected = op(25, 35)
            lhs = vobj.SmartVersion(25, 'schema')

            result = op(lhs, 35)

            self.assertEqual(expected, result)

    def test_binary_operators_smart_version(self):
        for op in self.binary_operators:
            expected = op(25, 35)
            lhs = vobj.SmartVersion(25, 'schema')
            rhs = vobj.SmartVersion(35, 'schema')

            result = op(lhs, rhs)

            self.assertEqual(expected, result)

    def test_binary_operators_reflected(self):
        for op in self.binary_operators:
            expected = op(25, 35)
            rhs = vobj.SmartVersion(35, 'schema')

            result = op(25, rhs)

            self.assertEqual(expected, result)

    def test_pow_modulo_integer(self):
        expected = pow(25, 35, 15)
        lhs = vobj.SmartVersion(25, 'schema')

        result = pow(lhs, 35, 15)

    def test_pow_modulo_smart_version(self):
        expected = pow(25, 35, 15)
        lhs = vobj.SmartVersion(25, 'schema')
        rhs = vobj.SmartVersion(35, 'schema')
        modulo = vobj.SmartVersion(15, 'schema')

        result = pow(lhs, rhs, modulo)

        self.assertEqual(expected, result)

    unary_operators = [
        operator.neg, operator.pos, abs, operator.invert, operator.index,
    ]

    def test_unary_operators(self):
        for op in self.unary_operators:
            expected = op(25)
            sv = vobj.SmartVersion(25, 'schema')

            result = op(sv)

            self.assertEqual(expected, result)

    def test_len_no_schema(self):
        sv = vobj.SmartVersion(1, None)

        self.assertEqual(len(sv), 0)

    def test_len_with_schema(self):
        schema = mock.Mock(__vers_downgraders__=range(5))
        sv = vobj.SmartVersion(1, schema)

        self.assertEqual(len(sv), 6)

    def test_contains_no_schema(self):
        sv = vobj.SmartVersion(1, None)

        self.assertFalse(5 in sv)

    def test_contains_with_schema(self):
        schema = mock.Mock(__vers_downgraders__={3: True}, __version__=4)
        sv = vobj.SmartVersion(1, schema)

        self.assertFalse(5 in sv)
        self.assertTrue(4 in sv)
        self.assertTrue(3 in sv)

    def test_getitem_no_master(self):
        schema = mock.Mock(__vers_downgraders__={3: True}, __version__=4)
        sv = vobj.SmartVersion(1, schema)

        self.assertRaises(RuntimeError, lambda: sv[4])

    def test_getitem_no_schema(self):
        master = mock.Mock(__vers_cache__={})
        sv = vobj.SmartVersion(1, None, master)

        self.assertRaises(KeyError, lambda: sv[4])

    def test_getitem_return_master(self):
        schema = mock.Mock(__vers_downgraders__={3: True}, __version__=4)
        master = mock.Mock(__vers_cache__={})
        sv = vobj.SmartVersion(1, schema, master)

        result = sv[4]

        self.assertEqual(result, master)

    def test_getitem_missing_downgrader(self):
        schema = mock.Mock(__vers_downgraders__={3: True}, __version__=4)
        master = mock.Mock(__vers_cache__={})
        sv = vobj.SmartVersion(1, schema, master)

        self.assertRaises(KeyError, lambda: sv[2])

    def test_getitem_cached(self):
        schema = mock.Mock(__vers_downgraders__={3: True}, __version__=4)
        master = mock.Mock(__vers_cache__={3: "slave"})
        sv = vobj.SmartVersion(1, schema, master)

        result = sv[3]

        self.assertEqual(result, "slave")

    def test_available_no_schema(self):
        sv = vobj.SmartVersion(1, None)

        result = sv.available()

        self.assertEqual(result, set())

    def test_available_with_schema(self):
        schema = mock.Mock(__vers_downgraders__={3: True}, __version__=4)
        sv = vobj.SmartVersion(1, schema)

        result = sv.available()

        self.assertEqual(result, set([3, 4]))


class TestDowngraderClass(unittest.TestCase):
    def test_init(self):
        dg = vobj.Downgrader('downgrader', 'schema')

        self.assertEqual(dg.downgrader, 'downgrader')
        self.assertEqual(dg.schema, 'schema')

    def test_call(self):
        downgrader = mock.Mock(return_value=dict(a=3, b=2, c=1))
        values = mock.Mock(__setstate__=mock.Mock())
        schema = mock.Mock(__version__=3, return_value=values)
        dg = vobj.Downgrader(downgrader, schema)
        state = dict(__version__=5, a=1, b=2, c=3)

        result = dg(state)

        self.assertEqual(result, values)
        downgrader.assert_called_once_with(dict(a=1, b=2, c=3))
        schema.assert_called_once_with()
        values.__setstate__.assert_called_once_with(
            dict(__version__=3, a=3, b=2, c=1))


class TestVObjectMeta(unittest.TestCase):
    def test_empty(self):
        namespace = {
            '__module__': 'test_vobject',
        }

        result = vobj.VObjectMeta('TestVObject', (object,), namespace)

        self.assertEqual(result.__vers_schemas__, [])
        self.assertEqual(result.__version__, 0)

    def test_duplicate_version(self):
        class TestSchema(vobj.Schema):
            __version__ = 1

        namespace = {
            '__module__': 'test_vobject',
            'Schema1': TestSchema,
            'Schema2': TestSchema,
        }

        self.assertRaises(TypeError, vobj.VObjectMeta, 'TestVObject',
                          (object,), namespace)

    def test_missing_base(self):
        class TestSchema(vobj.Schema):
            __version__ = 2

            @vobj.upgrader
            def upgrader(cls, old):
                pass

        namespace = {
            '__module__': 'test_vobject',
            'Schema': TestSchema,
        }

        self.assertRaises(TypeError, vobj.VObjectMeta, 'TestVObject',
                          (object,), namespace)

    def test_schema_gap(self):
        class TestSchema1(vobj.Schema):
            __version__ = 1

        class TestSchema3(vobj.Schema):
            __version__ = 3

            @vobj.upgrader
            def upgrader(cls, old):
                pass

        namespace = {
            '__module__': 'test_vobject',
            'Schema1': TestSchema1,
            'Schema3': TestSchema3,
        }

        self.assertRaises(TypeError, vobj.VObjectMeta, 'TestVObject',
                          (object,), namespace)

    @mock.patch.object(vobj, 'Downgrader', side_effect=lambda x, y: (x, y))
    def test_normal(self, mock_Downgrader):
        class TestSchema1(vobj.Schema):
            __version__ = 1

        class TestSchema2(vobj.Schema):
            __version__ = 2

            @vobj.upgrader
            def upgrader(cls, old):
                pass

        namespace = {
            '__module__': 'test_vobject',
            'Schema1': TestSchema1,
            'Schema2': TestSchema2,
            'AbstractSchema': vobj.Schema,
        }

        result = vobj.VObjectMeta('TestVObject', (object,), namespace)

        self.assertEqual(result.__vers_schemas__, [TestSchema1, TestSchema2])
        self.assertEqual(result.__vers_downgraders__, {})
        self.assertTrue(isinstance(result.__version__, vobj.SmartVersion))
        self.assertEqual(result.__version__, 2)
        self.assertFalse(mock_Downgrader.called)

    @mock.patch.object(vobj, 'Downgrader', side_effect=lambda x, y: (x, y))
    def test_downgraders(self, mock_Downgrader):
        class TestSchema1(vobj.Schema):
            __version__ = 1

        class TestSchema2(vobj.Schema):
            __version__ = 2

            @vobj.upgrader
            def upgrader(cls, old):
                pass

        class TestSchema3(vobj.Schema):
            __version__ = 3

            @vobj.upgrader
            def upgrader(cls, old):
                pass

            @vobj.downgrader(1)
            def downgrader_1(cls, new):
                pass

            @vobj.downgrader(2)
            def downgrader_2(cls, new):
                pass

        namespace = {
            '__module__': 'test_vobject',
            'Schema1': TestSchema1,
            'Schema2': TestSchema2,
            'Schema3': TestSchema3,
        }

        result = vobj.VObjectMeta('TestVObject', (object,), namespace)

        self.assertEqual(result.__vers_schemas__, [
            TestSchema1,
            TestSchema2,
            TestSchema3,
        ])
        self.assertEqual(result.__vers_downgraders__, {
            1: (TestSchema3.downgrader_1, TestSchema1),
            2: (TestSchema3.downgrader_2, TestSchema2),
        })
        self.assertTrue(isinstance(result.__version__, vobj.SmartVersion))
        self.assertEqual(result.__version__, 3)
        mock_Downgrader.assert_has_calls([
            mock.call(TestSchema3.downgrader_1, TestSchema1),
            mock.call(TestSchema3.downgrader_2, TestSchema2),
        ])


class TestCallUpgrader(unittest.TestCase):
    def test_call(self):
        state = dict(__version__=2, a=1, b=2, c=3)
        upgrader = mock.Mock(im_self=mock.Mock(__version__=3),
                             return_value=dict(a=3, b=2, c=1))

        result = vobj._call_upgrader(upgrader, state)

        self.assertEqual(state, dict(__version__=2, a=1, b=2, c=3))
        self.assertEqual(result, dict(__version__=3, a=3, b=2, c=1))
        upgrader.assert_called_once_with(dict(a=1, b=2, c=3))


def fake_call_upgrader(upgrader, state):
    state = copy.deepcopy(state)
    state.setdefault('upgraders', [])
    state['upgraders'].append(upgrader)
    return state


class TestVObject(unittest.TestCase):
    def test_abstract_constructor(self):
        self.assertRaises(TypeError, vobj.VObject)

    @mock.patch.object(vobj.VObject, '__vers_init__')
    def test_init(self, mock_vers_init):
        class TestVObject(vobj.VObject):
            pass
        TestVObject.__vers_schemas__ = [
            mock.Mock(return_value={'__version__': 1}),
            mock.Mock(return_value={'__version__': 2}),
        ]

        result = TestVObject(a=1, b=2, c=3)

        mock_vers_init.assert_called_once_with({'__version__': 2})
        self.assertFalse(TestVObject.__vers_schemas__[0].called)
        TestVObject.__vers_schemas__[1].assert_called_once_with(
            dict(a=1, b=2, c=3))

    @mock.patch.object(vobj, 'SmartVersion', return_value='smart version')
    def test_vers_init_noversion(self, mock_SmartVersion):
        vobject = EmptyClass()
        vobject.__class__ = vobj.VObject
        super(vobj.VObject, vobject).__setattr__('__version__', 2)
        super(vobj.VObject, vobject).__setattr__('__vers_schemas__', [
            mock.Mock(return_value={'__version__': 1}),
            mock.Mock(return_value={'__version__': 2}),
        ])

        vobject.__vers_init__('values')

        self.assertEqual(vobject.__vers_values__, 'values')
        self.assertEqual(vobject.__version__, 'smart version')
        mock_SmartVersion.assert_called_once_with(
            2, vobject.__vers_schemas__[-1], vobject)

    @mock.patch.object(vobj, 'SmartVersion', return_value='smart version')
    def test_vers_init_withversion(self, mock_SmartVersion):
        vobject = EmptyClass()
        vobject.__class__ = vobj.VObject
        super(vobj.VObject, vobject).__setattr__('__version__', 2)
        super(vobj.VObject, vobject).__setattr__('__vers_schemas__', [
            mock.Mock(return_value={'__version__': 1}),
            mock.Mock(return_value={'__version__': 2}),
        ])

        vobject.__vers_init__('values', version=5)

        self.assertEqual(vobject.__vers_values__, 'values')
        self.assertEqual(vobject.__version__, 'smart version')
        mock_SmartVersion.assert_called_once_with(
            5, vobject.__vers_schemas__[-1], vobject)

    def test_getattr(self):
        class TestVObject(vobj.VObject):
            pass
        TestVObject.__vers_schemas__ = [
            mock.Mock(return_value=mock.Mock(attr='value')),
        ]
        vobject = TestVObject()

        self.assertEqual(vobject.attr, 'value')

    def test_setattr_delegated(self):
        class TestVObject(vobj.VObject):
            pass
        sch = mock.MagicMock()
        sch.__contains__.return_value = True
        TestVObject.__vers_schemas__ = [
            mock.Mock(return_value=sch),
        ]
        vobject = TestVObject()

        vobject.attr = 'value'

        sch.__contains__.assert_called_once_with('attr')
        self.assertEqual(sch.attr, 'value')
        self.assertFalse('attr' in vobject.__dict__)

    def test_setattr_undelegated(self):
        class TestVObject(vobj.VObject):
            pass
        sch = mock.MagicMock(attr='schema')
        sch.__contains__.return_value = False
        TestVObject.__vers_schemas__ = [
            mock.Mock(return_value=sch),
        ]
        vobject = TestVObject()

        vobject.attr = 'value'

        sch.__contains__.assert_called_once_with('attr')
        self.assertEqual(sch.attr, 'schema')
        self.assertEqual(vobject.__dict__['attr'], 'value')

    def test_delattr_delegated(self):
        class TestVObject(vobj.VObject):
            pass
        sch = mock.MagicMock()
        sch.__contains__.return_value = True
        TestVObject.__vers_schemas__ = [
            mock.Mock(return_value=sch),
        ]
        vobject = TestVObject()

        def test_func():
            del vobject.attr

        self.assertRaises(AttributeError, test_func)
        sch.__contains__.assert_called_once_with('attr')

    def test_delattr_undelegated(self):
        class TestVObject(vobj.VObject):
            pass
        sch = mock.MagicMock(attr='schema')
        sch.__contains__.return_value = False
        TestVObject.__vers_schemas__ = [
            mock.Mock(return_value=sch),
        ]
        vobject = TestVObject()
        super(vobj.VObject, vobject).__setattr__('attr', 'value')

        del vobject.attr

        sch.__contains__.assert_called_once_with('attr')
        self.assertEqual(sch.attr, 'schema')
        self.assertFalse('attr' in vobject.__dict__)

    def test_eq_equal(self):
        class TestVObject(vobj.VObject):
            pass
        TestVObject.__vers_schemas__ = [
            mock.Mock(side_effect=[
                dict(a=1, b=2, c=3),
                dict(a=1, b=2, c=3),
            ]),
        ]
        vobj1 = TestVObject()
        vobj2 = TestVObject()

        self.assertTrue(vobj1 == vobj2)

    def test_eq_unequal_class(self):
        class TestVObject1(vobj.VObject):
            pass
        TestVObject1.__vers_schemas__ = [
            mock.Mock(return_value=dict(a=1, b=2, c=3)),
        ]

        class TestVObject2(vobj.VObject):
            pass
        TestVObject2.__vers_schemas__ = [
            mock.Mock(return_value=dict(a=1, b=2, c=3)),
        ]

        vobj1 = TestVObject1()
        vobj2 = TestVObject2()

        self.assertFalse(vobj1 == vobj2)

    def test_eq_unequal_value(self):
        class TestVObject(vobj.VObject):
            pass
        TestVObject.__vers_schemas__ = [
            mock.Mock(side_effect=[
                dict(a=1, b=2, c=3),
                dict(a=3, b=2, c=1),
            ]),
        ]
        vobj1 = TestVObject()
        vobj2 = TestVObject()

        self.assertFalse(vobj1 == vobj2)

    def test_ne_equal(self):
        class TestVObject(vobj.VObject):
            pass
        TestVObject.__vers_schemas__ = [
            mock.Mock(side_effect=[
                dict(a=1, b=2, c=3),
                dict(a=1, b=2, c=3),
            ]),
        ]
        vobj1 = TestVObject()
        vobj2 = TestVObject()

        self.assertFalse(vobj1 != vobj2)

    def test_ne_unequal_class(self):
        class TestVObject1(vobj.VObject):
            pass
        TestVObject1.__vers_schemas__ = [
            mock.Mock(return_value=dict(a=1, b=2, c=3)),
        ]

        class TestVObject2(vobj.VObject):
            pass
        TestVObject2.__vers_schemas__ = [
            mock.Mock(return_value=dict(a=1, b=2, c=3)),
        ]

        vobj1 = TestVObject1()
        vobj2 = TestVObject2()

        self.assertTrue(vobj1 != vobj2)

    def test_ne_unequal_value(self):
        class TestVObject(vobj.VObject):
            pass
        TestVObject.__vers_schemas__ = [
            mock.Mock(side_effect=[
                dict(a=1, b=2, c=3),
                dict(a=3, b=2, c=1),
            ]),
        ]
        vobj1 = TestVObject()
        vobj2 = TestVObject()

        self.assertTrue(vobj1 != vobj2)

    def test_getstate(self):
        class TestVObject(vobj.VObject):
            pass
        state = {'__version__': 2}
        sch = mock.Mock(__getstate__=mock.Mock(return_value=state))
        TestVObject.__vers_schemas__ = [
            mock.Mock(return_value=sch),
        ]
        vobject = TestVObject()

        result = vobject.__getstate__()

        self.assertEqual(result, {'__version__': 2})
        sch.__getstate__.assert_called_once_with()

    @mock.patch.object(vobj, '_call_upgrader',
                       side_effect=fake_call_upgrader)
    def test_setstate_abstract(self, mock_call_upgrader):
        class TestVObject(vobj.VObject):
            pass
        vobject = EmptyClass()
        vobject.__class__ = TestVObject

        self.assertRaises(TypeError, vobject.__setstate__, {
            '__version__': 1,
            'attr': 'value',
        })
        self.assertFalse(mock_call_upgrader.called)

    @mock.patch.object(vobj, '_call_upgrader',
                       side_effect=fake_call_upgrader)
    def test_setstate_state_unversioned(self, mock_call_upgrader):
        class TestVObject(vobj.VObject):
            pass
        sch = mock.Mock(__setstate__=mock.Mock())
        TestVObject.__vers_schemas__ = [
            mock.Mock(return_value=sch, __version__=1),
        ]
        vobject = TestVObject()

        self.assertRaises(TypeError, vobject.__setstate__, {
            'attr': 'value',
        })
        self.assertFalse(mock_call_upgrader.called)
        self.assertFalse(sch.__setstate__.called)

    @mock.patch.object(vobj, '_call_upgrader',
                       side_effect=fake_call_upgrader)
    def test_setstate_state_lowversion(self, mock_call_upgrader):
        class TestVObject(vobj.VObject):
            pass
        sch = mock.Mock(__setstate__=mock.Mock())
        TestVObject.__vers_schemas__ = [
            mock.Mock(return_value=sch, __version__=1),
        ]
        vobject = TestVObject()

        self.assertRaises(TypeError, vobject.__setstate__, {
            '__version__': 0,
            'attr': 'value',
        })
        self.assertFalse(mock_call_upgrader.called)
        self.assertFalse(sch.__setstate__.called)

    @mock.patch.object(vobj, '_call_upgrader',
                       side_effect=fake_call_upgrader)
    def test_setstate_state_highversion(self, mock_call_upgrader):
        class TestVObject(vobj.VObject):
            pass
        sch = mock.Mock(__setstate__=mock.Mock())
        TestVObject.__vers_schemas__ = [
            mock.Mock(__version__=1),
            mock.Mock(__version__=2),
            mock.Mock(return_value=sch, __version__=3),
        ]
        vobject = TestVObject()

        self.assertRaises(TypeError, vobject.__setstate__, {
            '__version__': 4,
            'attr': 'value',
        })
        self.assertFalse(mock_call_upgrader.called)
        self.assertFalse(sch.__setstate__.called)

    @mock.patch.object(vobj, '_call_upgrader',
                       side_effect=fake_call_upgrader)
    def test_setstate_state_badversion(self, mock_call_upgrader):
        class TestVObject(vobj.VObject):
            pass
        sch = mock.Mock(__setstate__=mock.Mock())
        TestVObject.__vers_schemas__ = [
            mock.Mock(__version__=1),
            mock.Mock(__version__=2),
            mock.Mock(return_value=sch, __version__=3),
        ]
        vobject = TestVObject()

        self.assertRaises(TypeError, vobject.__setstate__, {
            '__version__': "bad",
            'attr': 'value',
        })
        self.assertFalse(mock_call_upgrader.called)
        self.assertFalse(sch.__setstate__.called)

    @mock.patch.object(vobj, '_call_upgrader',
                       side_effect=fake_call_upgrader)
    def test_setstate_exact(self, mock_call_upgrader):
        class TestVObject(vobj.VObject):
            pass
        sch = mock.Mock(__setstate__=mock.Mock())
        TestVObject.__vers_schemas__ = [
            mock.Mock(__version__=1),
            mock.Mock(return_value=sch, __version__=2),
        ]
        vobject = TestVObject()

        vobject.__setstate__({
            '__version__': 2,
            'attr': 'value',
        })

        self.assertFalse(mock_call_upgrader.called)
        sch.__setstate__.assert_called_once_with({
            '__version__': 2,
            'attr': 'value',
        })
        self.assertEqual(vobject.__vers_values__, sch)

    @mock.patch.object(vobj, '_call_upgrader',
                       side_effect=fake_call_upgrader)
    def test_setstate_upgrade(self, mock_call_upgrader):
        class TestVObject(vobj.VObject):
            pass
        sch = mock.Mock(__setstate__=mock.Mock())
        upgraders2 = {
            1: '1->2',
        }
        upgraders3 = {
            2: '2->3',
        }
        upgraders4 = {
            2: '2->4',
            3: '3->4',
        }
        upgraders5 = {
            4: '4->5',
        }
        TestVObject.__vers_schemas__ = [
            mock.Mock(__version__=1),
            mock.Mock(__version__=2, __vers_upgraders__=upgraders2),
            mock.Mock(__version__=3, __vers_upgraders__=upgraders3),
            mock.Mock(__version__=4, __vers_upgraders__=upgraders4),
            mock.Mock(return_value=sch, __version__=5,
                      __vers_upgraders__=upgraders5),
        ]
        vobject = TestVObject()

        vobject.__setstate__({
            '__version__': 2,
            'attr': 'value',
        })

        mock_call_upgrader.assert_has_calls([
            mock.call('2->4', {
                '__version__': 2,
                'attr': 'value',
            }),
            mock.call('4->5', {
                '__version__': 2,
                'attr': 'value',
                'upgraders': ['2->4'],
            }),
        ])
        sch.__setstate__.assert_called_once_with({
            '__version__': 2,
            'attr': 'value',
            'upgraders': ['2->4', '4->5'],
        })
        self.assertEqual(vobject.__vers_values__, sch)

    @mock.patch.object(vobj, '_call_upgrader',
                       side_effect=fake_call_upgrader)
    def test_setstate_upgrade_missing(self, mock_call_upgrader):
        class TestVObject(vobj.VObject):
            pass
        sch = mock.Mock(__setstate__=mock.Mock())
        upgraders2 = {
            1: '1->2',
        }
        upgraders3 = {
            2: '2->3',
        }
        upgraders4 = {
            2: '2->4',
            3: '3->4',
        }
        upgraders5 = {
        }
        TestVObject.__vers_schemas__ = [
            mock.Mock(__version__=1),
            mock.Mock(__version__=2, __vers_upgraders__=upgraders2),
            mock.Mock(__version__=3, __vers_upgraders__=upgraders3),
            mock.Mock(__version__=4, __vers_upgraders__=upgraders4),
            mock.Mock(return_value=sch, __version__=5,
                      __vers_upgraders__=upgraders5),
        ]
        vobject = TestVObject()

        self.assertRaises(TypeError, vobject.__setstate__, {
            '__version__': 2,
            'attr': 'value',
        })
        self.assertFalse(mock_call_upgrader.called)
        self.assertFalse(sch.__setstate__.called)

    @mock.patch.object(vobj.VObject, '__setstate__')
    def test_from_dict_abstract(self, mock_setstate):
        self.assertRaises(TypeError, vobj.VObject.from_dict, 'values')
        self.assertFalse(mock_setstate.called)

    @mock.patch.object(vobj.VObject, '__setstate__')
    def test_from_dict(self, mock_setstate):
        class TestVObject(vobj.VObject):
            pass
        TestVObject.__vers_schemas__ = ['schema']

        result = TestVObject.from_dict('values')

        self.assertTrue(isinstance(result, TestVObject))
        mock_setstate.assert_called_once_with('values')
