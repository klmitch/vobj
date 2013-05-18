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

import mock
import unittest2

import vobj


class TestAttribute(unittest2.TestCase):
    def test_init_defaults(self):
        attr = vobj.Attribute()

        self.assertEqual(attr.default, vobj._unset)
        self.assertTrue(callable(attr.validate))
        self.assertEqual(attr.validate('spam'), 'spam')

    def test_init(self):
        attr = vobj.Attribute('default', validate='validate')

        self.assertEqual(attr.default, 'default')
        self.assertEqual(attr.validate, 'validate')


class TestSchemaMeta(unittest2.TestCase):
    def test_bad_version_declared(self):
        namespace = {
            '__version__': '23',
            '__module__': 'test_vobject',
        }

        self.assertRaises(TypeError, vobj.SchemaMeta, 'TestSchema',
                          (object,), namespace)

    def test_bad_version_inheritance(self):
        class SuperClass(object):
            __version__ = '23'

        namespace = {
            '__module__': 'test_vobject',
        }

        result = vobj.SchemaMeta('TestSchema', (SuperClass,), namespace)

        self.assertEqual(result.__version__, None)

    def test_version_inheritance(self):
        class SuperClass(object):
            __version__ = 23

        namespace = {
            '__module__': 'test_vobject',
            'fake_upgrader': mock.Mock(__vers_upgrader__=None),
        }

        result = vobj.SchemaMeta('TestSchema', (SuperClass,), namespace)

        self.assertEqual(result.__version__, 24)

    def test_attribute_inheritance(self):
        class SuperClass(object):
            __vers_attrs__ = dict(a=1, b=2, c=3)

        namespace = {
            '__module__': 'test_vobject',
        }

        result = vobj.SchemaMeta('TestSchema', (SuperClass,), namespace)

        self.assertEqual(result.__vers_attrs__, dict(a=1, b=2, c=3))
        for attr_name in ('a', 'b', 'c'):
            self.assertFalse(hasattr(result, attr_name))

    def test_attribute_inheritance_override(self):
        attrs = dict(
            a=vobj.Attribute(),
            b=vobj.Attribute(),
            c=vobj.Attribute(),
            d=vobj.Attribute(),
            e=vobj.Attribute(),
        )

        class SuperClass(object):
            __vers_attrs__ = dict(a=attrs['a'], b=attrs['b'], c=attrs['c'])

        namespace = {
            '__module__': 'test_vobject',
            'b': None,
            'c': attrs['d'],
            'e': attrs['e'],
        }

        result = vobj.SchemaMeta('TestSchema', (SuperClass,), namespace)

        self.assertEqual(result.__vers_attrs__, dict(
            a=attrs['a'],
            c=attrs['d'],
            e=attrs['e'],
        ))
        for attr_name in attrs:
            self.assertFalse(hasattr(result, attr_name))

    def test_property_inheritance(self):
        class SuperClass(object):
            __vers_properties__ = set('abc')

        namespace = {
            '__module__': 'test_vobject',
        }

        result = vobj.SchemaMeta('TestSchema', (SuperClass,), namespace)

        self.assertEqual(result.__vers_properties__, set('abc'))

    def test_property_inheritance_override(self):
        class SuperClass(object):
            __vers_properties__ = set('abc')

        namespace = {
            '__module__': 'test_vobject',
            'b': None,
            'c': property(lambda: 'c'),
            'd': property(lambda: 'd'),
        }

        result = vobj.SchemaMeta('TestSchema', (SuperClass,), namespace)

        self.assertEqual(result.__vers_properties__, set('acd'))
        self.assertEqual(result.b, None)
        self.assertIsInstance(result.c, property)
        self.assertIsInstance(result.d, property)

    def test_upgrader_abstract(self):
        namespace = {
            '__module__': 'test_vobject',
            'fake_upgrader': mock.Mock(__vers_upgrader__=None),
        }

        self.assertRaises(TypeError, vobj.SchemaMeta, 'TestSchema',
                          (object,), namespace)

    def test_upgrader_version1(self):
        namespace = {
            '__module__': 'test_vobject',
            '__version__': 1,
            'fake_upgrader': mock.Mock(__vers_upgrader__=None),
        }

        self.assertRaises(TypeError, vobj.SchemaMeta, 'TestSchema',
                          (object,), namespace)

    def test_upgrader_later(self):
        namespace = {
            '__module__': 'test_vobject',
            '__version__': 2,
            'fake_upgrader': mock.Mock(__vers_upgrader__=3),
        }

        self.assertRaises(TypeError, vobj.SchemaMeta, 'TestSchema',
                          (object,), namespace)

    def test_upgrader(self):
        namespace = {
            '__module__': 'test_vobject',
            '__version__': 3,
            'fake_upgrader1': mock.Mock(__vers_upgrader__=1),
            'fake_upgrader2': mock.Mock(__vers_upgrader__=None),
        }

        result = vobj.SchemaMeta('TestSchema', (object,), namespace)

        self.assertIsInstance(result.__dict__['fake_upgrader1'], classmethod)
        self.assertIsInstance(result.__dict__['fake_upgrader2'], classmethod)
        self.assertEqual(result.__vers_upgraders__, {
            1: result.fake_upgrader1,
            2: result.fake_upgrader2,
        })

    def test_upgrader_required(self):
        namespace = {
            '__module__': 'test_vobject',
            '__version__': 2,
        }

        self.assertRaises(TypeError, vobj.SchemaMeta, 'TestSchema',
                          (object,), namespace)

    def test_upgrader_previous_required(self):
        namespace = {
            '__module__': 'test_vobject',
            '__version__': 3,
            'fake_upgrader': mock.Mock(__vers_upgrader__=1),
        }

        self.assertRaises(TypeError, vobj.SchemaMeta, 'TestSchema',
                          (object,), namespace)

    def test_values(self):
        namespace = {
            '__module__': 'test_vobject',
        }
        result = vobj.SchemaMeta('TestSchema', (object,), namespace)

        self.assertEqual(result.__vers_values__, None)


class TestUpgrader(unittest2.TestCase):
    def test_no_arg(self):
        @vobj.upgrader
        def test():
            pass

        self.assertEqual(test.__vers_upgrader__, None)

    def test_empty_arg(self):
        @vobj.upgrader()
        def test():
            pass

        self.assertEqual(test.__vers_upgrader__, None)

    def test_int_arg(self):
        @vobj.upgrader(5)
        def test():
            pass

        self.assertEqual(test.__vers_upgrader__, 5)

    def test_int_arg_low(self):
        self.assertRaises(TypeError, vobj.upgrader, 0)

    def test_other_arg(self):
        self.assertRaises(TypeError, vobj.upgrader, 'other')


class EmptyClass(object):
    # Used to test __setstate__() on abstract Schemas
    pass


class TestSchema(unittest2.TestCase):
    def test_abstract_constructor(self):
        self.assertRaises(TypeError, vobj.Schema)

    def test_late_construction(self):
        class TestSchema(vobj.Schema):
            __version__ = 1

        sch = TestSchema()

        self.assertEqual(sch.__vers_values__, None)

    def test_required_args(self):
        class TestSchema(vobj.Schema):
            __version__ = 1
            required = vobj.Attribute()

        self.assertRaises(TypeError, TestSchema, {})

    def test_default_args(self):
        validator = mock.Mock()

        class TestSchema(vobj.Schema):
            __version__ = 1
            optional = vobj.Attribute('default', validate=validator)

        result = TestSchema({})

        self.assertEqual(result.__vers_values__, dict(optional='default'))
        self.assertFalse(validator.called)

    def test_validator(self):
        validator = mock.Mock(return_value='validated')

        class TestSchema(vobj.Schema):
            __version__ = 1
            optional = vobj.Attribute('default', validate=validator)

        result = TestSchema(dict(optional='value'))

        self.assertEqual(result.__vers_values__, dict(optional='validated'))
        validator.assert_called_once_with('value')

    def test_contains_none(self):
        class TestSchema(vobj.Schema):
            __version__ = 1

        result = TestSchema()

        self.assertFalse('attr' in result)

    def test_contains_attr(self):
        class TestSchema(vobj.Schema):
            __version__ = 1
            attr = vobj.Attribute()
        sch = TestSchema()

        self.assertTrue('attr' in sch)

    def test_contains_property(self):
        class TestSchema(vobj.Schema):
            __version__ = 1

            @property
            def prop(self):
                pass
        sch = TestSchema()

        self.assertTrue('prop' in sch)

    def test_getattr_uninit(self):
        class TestSchema(vobj.Schema):
            __version__ = 1
            attr = vobj.Attribute('default')
        sch = TestSchema()

        with self.assertRaises(RuntimeError):
            result = sch.attr

    def test_getattr(self):
        class TestSchema(vobj.Schema):
            __version__ = 1
            attr = vobj.Attribute('default')
        sch = TestSchema({})

        result = sch.attr

        self.assertEqual(result, 'default')

    def test_getattr_nosuch(self):
        class TestSchema(vobj.Schema):
            __version__ = 1
        sch = TestSchema({})

        with self.assertRaises(AttributeError):
            result = sch.attr

    def test_setattr_uninit(self):
        class TestSchema(vobj.Schema):
            __version__ = 1
            attr = vobj.Attribute('default')
        sch = TestSchema()

        with self.assertRaises(RuntimeError):
            sch.attr = 'value'

    def test_setattr(self):
        validator = mock.Mock(return_value='validated')

        class TestSchema(vobj.Schema):
            __version__ = 1
            attr = vobj.Attribute('default', validate=validator)
        sch = TestSchema({})

        sch.attr = 'new_value'

        validator.assert_called_once_with('new_value')
        self.assertEqual(sch.__vers_values__, dict(attr='validated'))

    def test_setattr_nosuch(self):
        class TestSchema(vobj.Schema):
            __version__ = 1
        sch = TestSchema({})

        sch.attr = 'new_value'

        self.assertEqual(sch.__vers_values__, {})
        self.assertEqual(sch.attr, 'new_value')

    def test_delattr_uninit(self):
        class TestSchema(vobj.Schema):
            __version__ = 1
            attr = vobj.Attribute('default')
        sch = TestSchema()

        with self.assertRaises(RuntimeError):
            del sch.attr

    def test_delattr(self):
        class TestSchema(vobj.Schema):
            __version__ = 1
            attr = vobj.Attribute('default')
        sch = TestSchema({})

        with self.assertRaises(AttributeError):
            del sch.attr

        self.assertEqual(sch.__vers_values__, dict(attr='default'))

    def test_delattr_nosuch(self):
        class TestSchema(vobj.Schema):
            __version__ = 1
        sch = TestSchema({})
        sch.attr = 'some value'

        del sch.attr

        self.assertFalse(hasattr(sch, 'attr'))
        self.assertEqual(sch.__vers_values__, {})

    def test_eq_uninit(self):
        class TestSchema(vobj.Schema):
            __version__ = 1
            attr1 = vobj.Attribute()
            attr2 = vobj.Attribute()

        sch1 = TestSchema()
        sch2 = TestSchema()

        with self.assertRaises(RuntimeError):
            result = (sch1 == sch2)

    def test_eq_equal(self):
        class TestSchema(vobj.Schema):
            __version__ = 1
            attr1 = vobj.Attribute()
            attr2 = vobj.Attribute()

        sch1 = TestSchema(dict(attr1=1, attr2=2))
        sch2 = TestSchema(dict(attr1=1, attr2=2))

        self.assertTrue(sch1 == sch2)

    def test_eq_unequal_class(self):
        class TestSchema1(vobj.Schema):
            __version__ = 1
            attr1 = vobj.Attribute()
            attr2 = vobj.Attribute()

        class TestSchema2(vobj.Schema):
            __version__ = 1
            attr1 = vobj.Attribute()
            attr2 = vobj.Attribute()

        sch1 = TestSchema1(dict(attr1=1, attr2=2))
        sch2 = TestSchema2(dict(attr1=1, attr2=2))

        self.assertFalse(sch1 == sch2)

    def test_eq_unequal_value(self):
        class TestSchema(vobj.Schema):
            __version__ = 1
            attr1 = vobj.Attribute()
            attr2 = vobj.Attribute()

        sch1 = TestSchema(dict(attr1=1, attr2=2))
        sch2 = TestSchema(dict(attr1=2, attr2=1))

        self.assertFalse(sch1 == sch2)

    def test_ne_uninit(self):
        class TestSchema(vobj.Schema):
            __version__ = 1
            attr1 = vobj.Attribute()
            attr2 = vobj.Attribute()

        sch1 = TestSchema()
        sch2 = TestSchema()

        with self.assertRaises(RuntimeError):
            result = (sch1 != sch2)

    def test_ne_equal(self):
        class TestSchema(vobj.Schema):
            __version__ = 1
            attr1 = vobj.Attribute()
            attr2 = vobj.Attribute()

        sch1 = TestSchema(dict(attr1=1, attr2=2))
        sch2 = TestSchema(dict(attr1=1, attr2=2))

        self.assertFalse(sch1 != sch2)

    def test_ne_unequal_class(self):
        class TestSchema1(vobj.Schema):
            __version__ = 1
            attr1 = vobj.Attribute()
            attr2 = vobj.Attribute()

        class TestSchema2(vobj.Schema):
            __version__ = 1
            attr1 = vobj.Attribute()
            attr2 = vobj.Attribute()

        sch1 = TestSchema1(dict(attr1=1, attr2=2))
        sch2 = TestSchema2(dict(attr1=1, attr2=2))

        self.assertTrue(sch1 != sch2)

    def test_ne_unequal_value(self):
        class TestSchema(vobj.Schema):
            __version__ = 1
            attr1 = vobj.Attribute()
            attr2 = vobj.Attribute()

        sch1 = TestSchema(dict(attr1=1, attr2=2))
        sch2 = TestSchema(dict(attr1=2, attr2=1))

        self.assertTrue(sch1 != sch2)

    def test_getstate_uninit(self):
        class TestSchema(vobj.Schema):
            __version__ = 1
            attr1 = vobj.Attribute()
            attr2 = vobj.Attribute()
        sch = TestSchema()

        with self.assertRaises(RuntimeError):
            state = sch.__getstate__()

    def test_getstate(self):
        class TestSchema(vobj.Schema):
            __version__ = 1
            attr1 = vobj.Attribute()
            attr2 = vobj.Attribute()
        sch = TestSchema(dict(attr1=1, attr2=2))

        state = sch.__getstate__()

        self.assertEqual(state, dict(__version__=1, attr1=1, attr2=2))
        self.assertEqual(sch.__vers_values__, dict(attr1=1, attr2=2))

    def test_setstate_abstract(self):
        sch = EmptyClass()
        sch.__class__ = vobj.Schema

        self.assertRaises(TypeError, sch.__setstate__, {})

    def test_setstate_unversioned(self):
        class TestSchema(vobj.Schema):
            __version__ = 1
        sch = TestSchema()

        self.assertRaises(ValueError, sch.__setstate__, {})

    def test_setstate_version_mismatch(self):
        class TestSchema(vobj.Schema):
            __version__ = 1
        sch = TestSchema()

        self.assertRaises(ValueError, sch.__setstate__, dict(__version__=2))

    def test_setstate_unexpected_attr(self):
        class TestSchema(vobj.Schema):
            __version__ = 1
        sch = TestSchema()

        self.assertRaises(ValueError, sch.__setstate__,
                          dict(__version__=1, attr=1))

    def test_setstate_missing_attr(self):
        class TestSchema(vobj.Schema):
            __version__ = 1
            attr = vobj.Attribute('default')
        sch = TestSchema()

        self.assertRaises(ValueError, sch.__setstate__, dict(__version__=1))

    def test_setstate(self):
        validator = mock.Mock(return_value='validated')

        class TestSchema(vobj.Schema):
            __version__ = 1
            attr = vobj.Attribute('default', validate=validator)
        sch = TestSchema()

        sch.__setstate__(dict(__version__=1, attr='value'))

        self.assertEqual(sch.__vers_values__, dict(attr='validated'))
        validator.assert_called_once_with('value')


class TestVObjectMeta(unittest2.TestCase):
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

    def test_normal(self):
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
        self.assertEqual(result.__version__, 2)


class TestCallUpgrader(unittest2.TestCase):
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


class TestVObject(unittest2.TestCase):
    def test_abstract_constructor(self):
        self.assertRaises(TypeError, vobj.VObject)

    def test_init(self):
        class TestVObject(vobj.VObject):
            pass
        TestVObject.__vers_schemas__ = [
            mock.Mock(return_value={'__version__': 1}),
            mock.Mock(return_value={'__version__': 2}),
        ]

        result = TestVObject(a=1, b=2, c=3)

        self.assertEqual(result.__vers_values__, {'__version__': 2})
        self.assertFalse(TestVObject.__vers_schemas__[0].called)
        TestVObject.__vers_schemas__[1].assert_called_once_with(
            dict(a=1, b=2, c=3))

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

        with self.assertRaises(AttributeError):
            del vobject.attr

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

        self.assertIsInstance(result, TestVObject)
        mock_setstate.assert_called_once_with('values')
