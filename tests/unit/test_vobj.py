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
from vobj import version


class EmptyClass(object):
    # Used to test __setstate__() on abstract Schemas
    pass


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

    @mock.patch('vobj.converters.Converters', side_effect=lambda x, y: (x, y))
    def test_normal(self, mock_Converters):
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
        self.assertTrue(isinstance(result.__version__, version.SmartVersion))
        self.assertEqual(result.__version__, 2)
        self.assertFalse(mock_Converters.called)

    @mock.patch('vobj.converters.Converters', side_effect=lambda x, y: (x, y))
    def test_downgraders(self, mock_Converters):
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
            1: (TestSchema1, TestSchema3.downgrader_1),
            2: (TestSchema2, TestSchema3.downgrader_2),
        })
        self.assertTrue(isinstance(result.__version__, version.SmartVersion))
        self.assertEqual(result.__version__, 3)
        mock_Converters.assert_has_calls([
            mock.call(TestSchema1, TestSchema3.downgrader_1),
            mock.call(TestSchema2, TestSchema3.downgrader_2),
        ])


class TestVObject(unittest.TestCase):
    def test_abstract_constructor(self):
        self.assertRaises(TypeError, vobj.VObject)

    @mock.patch.object(version, 'SmartVersion')
    @mock.patch.object(vobj.VObject, '__vers_set_values__')
    def test_init(self, mock_set_values, mock_SmartVersion):
        class TestVObject(vobj.VObject):
            pass
        TestVObject.__vers_schemas__ = [
            mock.Mock(return_value=mock.Mock()),
            mock.Mock(return_value=mock.Mock()),
        ]
        TestVObject.__version__ = '2'
        schema = TestVObject.__vers_schemas__[1]
        values = schema.return_value
        mock_SmartVersion.reset_mock()

        result = TestVObject(a=1, b=2, c=3)

        schema.assert_called_once_with({'a': 1, 'b': 2, 'c': 3})
        mock_set_values.assert_called_once_with(values)
        mock_SmartVersion.assert_called_once_with(
            2, schema, result)

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

    @mock.patch('vobj.converters.Converters')
    def test_setstate_abstract(self, mock_Converters):
        class TestVObject(vobj.VObject):
            pass
        vobject = EmptyClass()
        vobject.__class__ = TestVObject

        self.assertRaises(TypeError, vobject.__setstate__, {
            '__version__': 1,
            'attr': 'value',
        })
        self.assertFalse(mock_Converters.called)

    @mock.patch('vobj.converters.Converters')
    def test_setstate_state_unversioned(self, mock_Converters):
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
        self.assertFalse(mock_Converters.called)

    @mock.patch('vobj.converters.Converters')
    def test_setstate_state_lowversion(self, mock_Converters):
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
        self.assertFalse(mock_Converters.called)

    @mock.patch('vobj.converters.Converters')
    def test_setstate_state_highversion(self, mock_Converters):
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
        self.assertFalse(mock_Converters.called)

    @mock.patch('vobj.converters.Converters')
    def test_setstate_state_badversion(self, mock_Converters):
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
        self.assertFalse(mock_Converters.called)

    @mock.patch('vobj.converters.Converters')
    def test_setstate_exact(self, mock_Converters):
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

        upgraders = mock_Converters.return_value
        values = upgraders.return_value
        mock_Converters.assert_called_once_with(
            TestVObject.__vers_schemas__[1])
        self.assertFalse(upgraders.append.called)
        upgraders.assert_called_once_with({
            '__version__': 2,
            'attr': 'value',
        })
        self.assertEqual(vobject.__vers_values__, values)

    @mock.patch('vobj.converters.Converters')
    def test_setstate_upgrade(self, mock_Converters):
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

        upgraders = mock_Converters.return_value
        values = upgraders.return_value
        mock_Converters.assert_called_once_with(
            TestVObject.__vers_schemas__[4])
        upgraders.append.assert_has_calls([
            mock.call('4->5'),
            mock.call('2->4'),
        ])
        self.assertEqual(upgraders.append.call_count, 2)
        upgraders.assert_called_once_with({
            '__version__': 2,
            'attr': 'value',
        })
        self.assertEqual(vobject.__vers_values__, values)

    @mock.patch('vobj.converters.Converters')
    def test_setstate_upgrade_missing(self, mock_Converters):
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

        upgraders = mock_Converters.return_value
        mock_Converters.assert_called_once_with(
            TestVObject.__vers_schemas__[4])
        self.assertFalse(upgraders.append.called)
        self.assertFalse(upgraders.called)

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
