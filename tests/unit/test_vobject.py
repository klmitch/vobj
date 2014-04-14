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

from vobj import decorators
from vobj import proxy
from vobj import schema
from vobj import version
from vobj import vobject


class VObjectMetaTest(unittest.TestCase):
    def test_empty(self):
        namespace = {
            '__module__': 'test_vobject',
        }

        result = vobject.VObjectMeta('TestVObject', (object,), namespace)

        self.assertEqual(result.__vers_schemas__, [])
        self.assertEqual(result.__vers_downgraders__, {})
        self.assertEqual(result.__vers_upgraders__, {})
        self.assertEqual(result.__version__, 0)

    def test_duplicate_version(self):
        class TestSchema(schema.Schema):
            __version__ = 1

        namespace = {
            '__module__': 'test_vobject',
            'Schema1': TestSchema,
            'Schema2': TestSchema,
        }

        self.assertRaises(TypeError, vobject.VObjectMeta, 'TestVObject',
                          (object,), namespace)

    def test_missing_base(self):
        class TestSchema(schema.Schema):
            __version__ = 2

            @decorators.upgrader
            def upgrader(cls, old):
                pass

        namespace = {
            '__module__': 'test_vobject',
            'Schema': TestSchema,
        }

        self.assertRaises(TypeError, vobject.VObjectMeta, 'TestVObject',
                          (object,), namespace)

    def test_schema_gap(self):
        class TestSchema1(schema.Schema):
            __version__ = 1

        class TestSchema3(schema.Schema):
            __version__ = 3

            @decorators.upgrader
            def upgrader(cls, old):
                pass

        namespace = {
            '__module__': 'test_vobject',
            'Schema1': TestSchema1,
            'Schema3': TestSchema3,
        }

        self.assertRaises(TypeError, vobject.VObjectMeta, 'TestVObject',
                          (object,), namespace)

    @mock.patch('vobj.converters.Converters', side_effect=lambda x, *y: (x, y))
    def test_normal(self, mock_Converters):
        class TestSchema1(schema.Schema):
            __version__ = 1

        class TestSchema2(schema.Schema):
            __version__ = 2

            @decorators.upgrader
            def upgrader(cls, old):
                pass

        namespace = {
            '__module__': 'test_vobject',
            'Schema1': TestSchema1,
            'Schema2': TestSchema2,
            'AbstractSchema': schema.Schema,
        }

        result = vobject.VObjectMeta('TestVObject', (object,), namespace)

        self.assertEqual(result.__vers_schemas__, [TestSchema1, TestSchema2])
        self.assertEqual(result.__vers_downgraders__, {})
        self.assertEqual(result.__vers_upgraders__, {
            2: (TestSchema2, ()),
        })
        self.assertTrue(isinstance(result.__version__, version.SmartVersion))
        self.assertEqual(result.__version__, 2)
        mock_Converters.assert_called_once_with(TestSchema2)

    @mock.patch('vobj.converters.Converters', side_effect=lambda x, *y: (x, y))
    def test_downgraders(self, mock_Converters):
        class TestSchema1(schema.Schema):
            __version__ = 1

        class TestSchema2(schema.Schema):
            __version__ = 2

            @decorators.upgrader
            def upgrader(cls, old):
                pass

        class TestSchema3(schema.Schema):
            __version__ = 3

            @decorators.upgrader
            def upgrader(cls, old):
                pass

            @decorators.downgrader(1)
            def downgrader_1(cls, new):
                pass

            @decorators.downgrader(2)
            def downgrader_2(cls, new):
                pass

        namespace = {
            '__module__': 'test_vobject',
            'Schema1': TestSchema1,
            'Schema2': TestSchema2,
            'Schema3': TestSchema3,
        }

        result = vobject.VObjectMeta('TestVObject', (object,), namespace)

        self.assertEqual(result.__vers_schemas__, [
            TestSchema1,
            TestSchema2,
            TestSchema3,
        ])
        self.assertEqual(result.__vers_downgraders__, {
            1: (TestSchema1, (TestSchema3.downgrader_1,)),
            2: (TestSchema2, (TestSchema3.downgrader_2,)),
        })
        self.assertEqual(result.__vers_upgraders__, {
            3: (TestSchema3, ()),
        })
        self.assertTrue(isinstance(result.__version__, version.SmartVersion))
        self.assertEqual(result.__version__, 3)
        mock_Converters.assert_has_calls([
            mock.call(TestSchema1, TestSchema3.downgrader_1),
            mock.call(TestSchema2, TestSchema3.downgrader_2),
            mock.call(TestSchema3),
        ])


class VObjectTest(unittest.TestCase):
    @mock.patch('vobj.converters.Converters')
    def test_upgrader_get_cached(self, mock_Converters):
        class TestVObject(vobject.VObject):
            pass
        TestVObject.__vers_schemas__ = [
            mock.Mock(__version__=1),
            mock.Mock(__version__=2),
        ]
        TestVObject.__vers_upgraders__[2] = 'upgrader'

        result = TestVObject.__vers_upgrader_get__(2)

        self.assertEqual(result, 'upgrader')
        self.assertFalse(mock_Converters.called)
        self.assertEqual(TestVObject.__vers_upgraders__, {
            2: 'upgrader',
        })

    @mock.patch('vobj.converters.Converters')
    def test_upgrader_get_exact(self, mock_Converters):
        class TestVObject(vobject.VObject):
            pass
        TestVObject.__vers_schemas__ = [
            mock.Mock(__version__=1),
            mock.Mock(__version__=2),
        ]
        cvt = mock_Converters.return_value

        result = TestVObject.__vers_upgrader_get__(2)

        self.assertEqual(result, cvt)
        mock_Converters.assert_called_once_with(
            TestVObject.__vers_schemas__[1])
        self.assertFalse(cvt.append.called)
        self.assertEqual(TestVObject.__vers_upgraders__, {
            2: cvt,
        })

    @mock.patch('vobj.converters.Converters')
    def test_upgrader_get_upgrade(self, mock_Converters):
        class TestVObject(vobject.VObject):
            pass
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
            mock.Mock(__version__=5, __vers_upgraders__=upgraders5),
        ]
        cvt = mock_Converters.return_value

        result = TestVObject.__vers_upgrader_get__(2)

        self.assertEqual(result, cvt)
        mock_Converters.assert_called_once_with(
            TestVObject.__vers_schemas__[4])
        cvt.append.assert_has_calls([
            mock.call('4->5'),
            mock.call('2->4'),
        ])
        self.assertEqual(cvt.append.call_count, 2)
        self.assertEqual(TestVObject.__vers_upgraders__, {
            2: cvt,
        })

    @mock.patch('vobj.converters.Converters')
    def test_upgrader_get_missing(self, mock_Converters):
        class TestVObject(vobject.VObject):
            pass
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
            mock.Mock(__version__=5, __vers_upgraders__=upgraders5),
        ]
        cvt = mock_Converters.return_value

        self.assertRaises(TypeError, TestVObject.__vers_upgrader_get__, 2)

        mock_Converters.assert_called_once_with(
            TestVObject.__vers_schemas__[4])
        self.assertFalse(cvt.append.called)
        self.assertEqual(TestVObject.__vers_upgraders__, {})

    def test_abstract_constructor(self):
        self.assertRaises(TypeError, vobject.VObject)

    @mock.patch.object(vobject.VObject, '__vers_cache_invalidate__')
    @mock.patch.object(version, 'SmartVersion')
    @mock.patch.object(vobject.VObject, '__vers_set_values__')
    def test_init(self, mock_set_values, mock_SmartVersion,
                  mock_cache_invalidate):
        class TestVObject(vobject.VObject):
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
        self.assertEqual(values.__vers_notify__,
                         result.__vers_cache_invalidate__)
        mock_set_values.assert_called_once_with(values)
        mock_SmartVersion.assert_called_once_with(
            2, schema, result)
        mock_cache_invalidate.assert_called_once_with()
        self.assertEqual(result.__vers_proxies__, {})

    def test_setattr_delegated(self):
        class TestVObject(vobject.VObject):
            pass
        sch = mock.MagicMock()
        sch.__contains__.return_value = True
        TestVObject.__vers_schemas__ = [
            mock.Mock(return_value=sch),
        ]
        obj = TestVObject()

        obj.attr = 'value'

        sch.__contains__.assert_called_once_with('attr')
        self.assertEqual(sch.attr, 'value')
        self.assertFalse('attr' in obj.__dict__)

    def test_setattr_undelegated(self):
        class TestVObject(vobject.VObject):
            pass
        sch = mock.MagicMock(attr='schema')
        sch.__contains__.return_value = False
        TestVObject.__vers_schemas__ = [
            mock.Mock(return_value=sch),
        ]
        obj = TestVObject()

        obj.attr = 'value'

        sch.__contains__.assert_called_once_with('attr')
        self.assertEqual(sch.attr, 'schema')
        self.assertEqual(obj.__dict__['attr'], 'value')

    @mock.patch.object(proxy, 'ReadOnlyLazySchemaProxy', return_value='proxy')
    def test_accessor_cached(self, mock_ReadOnlyLazySchemaProxy):
        class TestVObject(vobject.VObject):
            pass
        TestVObject.__vers_schemas__ = [
            mock.Mock(return_value=mock.Mock()),
        ]
        obj = TestVObject()
        obj.__vers_proxies__[1] = 'cached'

        with mock.patch.object(version, 'SmartVersion',
                               return_value='version') as mock_SmartVersion:
            result = obj.__vers_accessor__(1)

        self.assertEqual(result, 'cached')
        self.assertFalse(mock_SmartVersion.called)
        self.assertFalse(mock_ReadOnlyLazySchemaProxy.called)
        self.assertEqual(obj.__vers_proxies__, {
            1: 'cached',
        })

    @mock.patch.object(proxy, 'ReadOnlyLazySchemaProxy', return_value='proxy')
    def test_accessor_uncached(self, mock_ReadOnlyLazySchemaProxy):
        class TestVObject(vobject.VObject):
            pass
        TestVObject.__vers_schemas__ = [
            mock.Mock(return_value=mock.Mock()),
        ]
        obj = TestVObject()

        with mock.patch.object(version, 'SmartVersion',
                               return_value='version') as mock_SmartVersion:
            result = obj.__vers_accessor__(1)

        self.assertEqual(result, 'proxy')
        mock_SmartVersion.assert_called_once_with(
            1, TestVObject.__vers_schemas__[0], obj)
        mock_ReadOnlyLazySchemaProxy.assert_called_once_with('version')
        self.assertEqual(obj.__vers_proxies__, {
            1: 'proxy',
        })

    @mock.patch.object(vobject.VObject, '__getstate__', return_value='state')
    def test_cache_get_cached(self, mock_getstate):
        class TestVObject(vobject.VObject):
            pass
        TestVObject.__vers_schemas__ = [
            mock.Mock(return_value=mock.Mock()),
        ]
        TestVObject.__vers_downgraders__[1] = mock.Mock(return_value='values')
        obj = TestVObject()
        obj.__vers_cache__[1] = 'cached'

        result = obj.__vers_cache_get__(1)

        self.assertEqual(result, 'cached')
        self.assertFalse(TestVObject.__vers_downgraders__[1].called)
        self.assertEqual(obj.__vers_cache__, {
            1: 'cached',
        })

    @mock.patch.object(vobject.VObject, '__getstate__', return_value='state')
    def test_cache_get_uncached(self, mock_getstate):
        class TestVObject(vobject.VObject):
            pass
        TestVObject.__vers_schemas__ = [
            mock.Mock(return_value=mock.Mock()),
        ]
        TestVObject.__vers_downgraders__[1] = mock.Mock(return_value='values')
        obj = TestVObject()

        result = obj.__vers_cache_get__(1)

        self.assertEqual(result, 'values')
        TestVObject.__vers_downgraders__[1].assert_called_once_with('state')
        self.assertEqual(obj.__vers_cache__, {
            1: 'values',
        })

    def test_cache_invalidate(self):
        class TestVObject(vobject.VObject):
            pass
        TestVObject.__vers_schemas__ = [
            mock.Mock(return_value=mock.Mock()),
        ]
        obj = TestVObject()
        obj.__vers_cache__.update({
            1: 'one',
            2: 'two',
        })

        obj.__vers_cache_invalidate__()

        self.assertEqual(obj.__vers_cache__, {})

    @mock.patch.object(vobject.VObject, '__vers_upgrader_get__')
    def test_setstate_abstract(self, mock_upgrader_get):
        class TestVObject(vobject.VObject):
            pass
        obj = vobject.EmptyClass()
        obj.__class__ = TestVObject

        self.assertRaises(TypeError, obj.__setstate__, {
            '__version__': 1,
            'attr': 'value',
        })
        self.assertFalse(mock_upgrader_get.called)

    @mock.patch.object(vobject.VObject, '__vers_upgrader_get__')
    def test_setstate_state_unversioned(self, mock_upgrader_get):
        class TestVObject(vobject.VObject):
            pass
        TestVObject.__vers_schemas__ = [
            mock.Mock(__version__=1),
        ]
        obj = TestVObject()

        self.assertRaises(TypeError, obj.__setstate__, {
            'attr': 'value',
        })
        self.assertFalse(mock_upgrader_get.called)

    @mock.patch.object(vobject.VObject, '__vers_upgrader_get__')
    def test_setstate_state_lowversion(self, mock_upgrader_get):
        class TestVObject(vobject.VObject):
            pass
        TestVObject.__vers_schemas__ = [
            mock.Mock(__version__=1),
        ]
        obj = TestVObject()

        self.assertRaises(TypeError, obj.__setstate__, {
            '__version__': 0,
            'attr': 'value',
        })
        self.assertFalse(mock_upgrader_get.called)

    @mock.patch.object(vobject.VObject, '__vers_upgrader_get__')
    def test_setstate_state_highversion(self, mock_upgrader_get):
        class TestVObject(vobject.VObject):
            pass
        TestVObject.__vers_schemas__ = [
            mock.Mock(__version__=1),
            mock.Mock(__version__=2),
            mock.Mock(__version__=3),
        ]
        obj = TestVObject()

        self.assertRaises(TypeError, obj.__setstate__, {
            '__version__': 4,
            'attr': 'value',
        })
        self.assertFalse(mock_upgrader_get.called)

    @mock.patch.object(vobject.VObject, '__vers_upgrader_get__')
    def test_setstate_state_badversion(self, mock_upgrader_get):
        class TestVObject(vobject.VObject):
            pass
        TestVObject.__vers_schemas__ = [
            mock.Mock(__version__=1),
            mock.Mock(__version__=2),
            mock.Mock(__version__=3),
        ]
        obj = TestVObject()

        self.assertRaises(TypeError, obj.__setstate__, {
            '__version__': "bad",
            'attr': 'value',
        })
        self.assertFalse(mock_upgrader_get.called)

    @mock.patch.object(vobject.VObject, '__vers_upgrader_get__')
    def test_setstate_normal(self, mock_upgrader_get):
        class TestVObject(vobject.VObject):
            pass
        TestVObject.__vers_schemas__ = [
            mock.Mock(__version__=1),
            mock.Mock(__version__=2),
        ]
        obj = TestVObject()
        upgraders = mock_upgrader_get.return_value
        values = upgraders.return_value

        obj.__setstate__({
            '__version__': 2,
            'attr': 'value',
        })

        mock_upgrader_get.assert_called_once_with(2)
        upgraders.assert_called_once_with({
            '__version__': 2,
            'attr': 'value',
        })
        self.assertEqual(values.__vers_notify__, obj.__vers_cache_invalidate__)
        self.assertEqual(obj.__vers_values__, values)

    @mock.patch.object(vobject.VObject, '__setstate__')
    def test_from_dict_abstract(self, mock_setstate):
        self.assertRaises(TypeError, vobject.VObject.from_dict, 'values')
        self.assertFalse(mock_setstate.called)

    @mock.patch.object(vobject.VObject, '__setstate__')
    def test_from_dict(self, mock_setstate):
        class TestVObject(vobject.VObject):
            pass
        TestVObject.__vers_schemas__ = ['schema']

        result = TestVObject.from_dict('values')

        self.assertTrue(isinstance(result, TestVObject))
        mock_setstate.assert_called_once_with('values')
