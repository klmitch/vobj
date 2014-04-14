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

from vobj import attribute
from vobj import schema


class SchemaMetaTest(unittest.TestCase):
    def test_bad_version_declared(self):
        namespace = {
            '__version__': '23',
            '__module__': 'test_vobject',
        }

        self.assertRaises(TypeError, schema.SchemaMeta, 'TestSchema',
                          (object,), namespace)

    def test_bad_version_inheritance(self):
        class SuperClass(object):
            __version__ = '23'

        namespace = {
            '__module__': 'test_vobject',
        }

        result = schema.SchemaMeta('TestSchema', (SuperClass,), namespace)

        self.assertEqual(result.__version__, None)

    def test_version_inheritance(self):
        class SuperClass(object):
            __version__ = 23

        namespace = {
            '__module__': 'test_vobject',
            'fake_upgrader': mock.Mock(__vers_upgrader__=None),
        }

        result = schema.SchemaMeta('TestSchema', (SuperClass,), namespace)

        self.assertEqual(result.__version__, 24)

    def test_attribute_inheritance(self):
        class SuperClass(object):
            __vers_attrs__ = dict(a=1, b=2, c=3)

        namespace = {
            '__module__': 'test_vobject',
        }

        result = schema.SchemaMeta('TestSchema', (SuperClass,), namespace)

        self.assertEqual(result.__vers_attrs__, dict(a=1, b=2, c=3))
        for attr_name in ('a', 'b', 'c'):
            self.assertFalse(hasattr(result, attr_name))

    def test_attribute_inheritance_override(self):
        attrs = dict(
            a=attribute.Attribute(),
            b=attribute.Attribute(),
            c=attribute.Attribute(),
            d=attribute.Attribute(),
            e=attribute.Attribute(),
        )

        class SuperClass(object):
            __vers_attrs__ = dict(a=attrs['a'], b=attrs['b'], c=attrs['c'])

        namespace = {
            '__module__': 'test_vobject',
            'b': None,
            'c': attrs['d'],
            'e': attrs['e'],
        }

        result = schema.SchemaMeta('TestSchema', (SuperClass,), namespace)

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

        result = schema.SchemaMeta('TestSchema', (SuperClass,), namespace)

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

        result = schema.SchemaMeta('TestSchema', (SuperClass,), namespace)

        self.assertEqual(result.__vers_properties__, set('acd'))
        self.assertEqual(result.b, None)
        self.assertTrue(isinstance(result.c, property))
        self.assertTrue(isinstance(result.d, property))

    def test_upgrader_abstract(self):
        namespace = {
            '__module__': 'test_vobject',
            'fake_upgrader': mock.Mock(__vers_upgrader__=None),
        }

        self.assertRaises(TypeError, schema.SchemaMeta, 'TestSchema',
                          (object,), namespace)

    def test_upgrader_version1(self):
        namespace = {
            '__module__': 'test_vobject',
            '__version__': 1,
            'fake_upgrader': mock.Mock(__vers_upgrader__=None),
        }

        self.assertRaises(TypeError, schema.SchemaMeta, 'TestSchema',
                          (object,), namespace)

    def test_upgrader_later(self):
        namespace = {
            '__module__': 'test_vobject',
            '__version__': 2,
            'fake_upgrader': mock.Mock(__vers_upgrader__=3),
        }

        self.assertRaises(TypeError, schema.SchemaMeta, 'TestSchema',
                          (object,), namespace)

    def test_upgrader(self):
        namespace = {
            '__module__': 'test_vobject',
            '__version__': 3,
            'fake_upgrader1': mock.Mock(__vers_upgrader__=1),
            'fake_upgrader2': mock.Mock(__vers_upgrader__=None),
        }

        result = schema.SchemaMeta('TestSchema', (object,), namespace)

        self.assertTrue(isinstance(result.__dict__['fake_upgrader1'],
                                   classmethod))
        self.assertTrue(isinstance(result.__dict__['fake_upgrader2'],
                                   classmethod))
        self.assertEqual(result.__vers_upgraders__, {
            1: result.fake_upgrader1,
            2: result.fake_upgrader2,
        })

    def test_upgrader_required(self):
        namespace = {
            '__module__': 'test_vobject',
            '__version__': 2,
        }

        self.assertRaises(TypeError, schema.SchemaMeta, 'TestSchema',
                          (object,), namespace)

    def test_upgrader_previous_required(self):
        namespace = {
            '__module__': 'test_vobject',
            '__version__': 3,
            'fake_upgrader': mock.Mock(__vers_upgrader__=1),
        }

        self.assertRaises(TypeError, schema.SchemaMeta, 'TestSchema',
                          (object,), namespace)

    def test_downgrader_abstract(self):
        namespace = {
            '__module__': 'test_vobject',
            'fake_downgrader': mock.Mock(__vers_downgrader__=1),
        }

        self.assertRaises(TypeError, schema.SchemaMeta, 'TestSchema',
                          (object,), namespace)

    def test_downgrader_version1(self):
        namespace = {
            '__module__': 'test_vobject',
            '__version__': 1,
            'fake_downgrader': mock.Mock(__vers_downgrader__=1),
        }

        self.assertRaises(TypeError, schema.SchemaMeta, 'TestSchema',
                          (object,), namespace)

    def test_downgrader_later(self):
        namespace = {
            '__module__': 'test_vobject',
            '__version__': 2,
            'fake_upgrader': mock.Mock(__vers_upgrader__=None),
            'fake_downgrader': mock.Mock(__vers_downgrader__=3),
        }

        self.assertRaises(TypeError, schema.SchemaMeta, 'TestSchema',
                          (object,), namespace)

    def test_downgrader(self):
        namespace = {
            '__module__': 'test_vobject',
            '__version__': 3,
            'fake_upgrader': mock.Mock(__vers_upgrader__=None),
            'fake_downgrader1': mock.Mock(__vers_downgrader__=1),
            'fake_downgrader2': mock.Mock(__vers_downgrader__=2),
        }

        result = schema.SchemaMeta('TestSchema', (object,), namespace)

        self.assertTrue(isinstance(result.__dict__['fake_downgrader1'],
                                   classmethod))
        self.assertTrue(isinstance(result.__dict__['fake_downgrader2'],
                                   classmethod))
        self.assertEqual(result.__vers_downgraders__, {
            1: result.fake_downgrader1,
            2: result.fake_downgrader2,
        })

    def test_values(self):
        namespace = {
            '__module__': 'test_vobject',
        }
        result = schema.SchemaMeta('TestSchema', (object,), namespace)

        self.assertEqual(result.__vers_values__, None)


class SchemaTest(unittest.TestCase):
    def test_abstract_constructor(self):
        self.assertRaises(TypeError, schema.Schema)

    def test_late_construction(self):
        class TestSchema(schema.Schema):
            __version__ = 1

        sch = TestSchema()

        self.assertEqual(sch.__vers_values__, None)
        self.assertEqual(sch.__vers_notify__, None)

    def test_required_args(self):
        class TestSchema(schema.Schema):
            __version__ = 1
            required = attribute.Attribute()

        self.assertRaises(TypeError, TestSchema, {})

    def test_default_args(self):
        validator = mock.Mock()

        class TestSchema(schema.Schema):
            __version__ = 1
            optional = attribute.Attribute('default', validate=validator)

        result = TestSchema({})

        self.assertEqual(result.__vers_values__, dict(optional='default'))
        self.assertFalse(validator.called)

    def test_validator(self):
        validator = mock.Mock(return_value='validated')

        class TestSchema(schema.Schema):
            __version__ = 1
            optional = attribute.Attribute('default', validate=validator)

        result = TestSchema(dict(optional='value'))

        self.assertEqual(result.__vers_values__, dict(optional='validated'))
        validator.assert_called_once_with('value')

    def test_contains_none(self):
        class TestSchema(schema.Schema):
            __version__ = 1

        result = TestSchema()

        self.assertFalse('attr' in result)

    def test_contains_attr(self):
        class TestSchema(schema.Schema):
            __version__ = 1
            attr = attribute.Attribute()
        sch = TestSchema()

        self.assertTrue('attr' in sch)

    def test_contains_property(self):
        class TestSchema(schema.Schema):
            __version__ = 1

            @property
            def prop(self):
                pass
        sch = TestSchema()

        self.assertTrue('prop' in sch)

    def test_getattr_uninit(self):
        class TestSchema(schema.Schema):
            __version__ = 1
            attr = attribute.Attribute('default')
        sch = TestSchema()

        self.assertRaises(RuntimeError, lambda: sch.attr)

    def test_getattr(self):
        class TestSchema(schema.Schema):
            __version__ = 1
            attr = attribute.Attribute('default')
        sch = TestSchema({})

        result = sch.attr

        self.assertEqual(result, 'default')

    def test_getattr_nosuch(self):
        class TestSchema(schema.Schema):
            __version__ = 1
        sch = TestSchema({})

        self.assertRaises(AttributeError, lambda: sch.attr)

    def test_setattr_uninit(self):
        class TestSchema(schema.Schema):
            __version__ = 1
            attr = attribute.Attribute('default')
        sch = TestSchema()

        def test_func():
            sch.attr = 'value'

        self.assertRaises(RuntimeError, test_func)

    def test_setattr(self):
        validator = mock.Mock(return_value='validated')

        class TestSchema(schema.Schema):
            __version__ = 1
            attr = attribute.Attribute('default', validate=validator)
        sch = TestSchema({})

        sch.attr = 'new_value'

        validator.assert_called_once_with('new_value')
        self.assertEqual(sch.__vers_values__, dict(attr='validated'))

    def test_setattr_notify(self):
        validator = mock.Mock(return_value='validated')
        notify = mock.Mock()

        class TestSchema(schema.Schema):
            __version__ = 1
            attr = attribute.Attribute('default', validate=validator)
        sch = TestSchema({})
        sch.__vers_notify__ = notify

        sch.attr = 'new_value'

        validator.assert_called_once_with('new_value')
        self.assertEqual(sch.__vers_values__, dict(attr='validated'))
        notify.assert_called_once_with()

    def test_setattr_nosuch(self):
        class TestSchema(schema.Schema):
            __version__ = 1
        sch = TestSchema({})

        sch.attr = 'new_value'

        self.assertEqual(sch.__vers_values__, {})
        self.assertEqual(sch.attr, 'new_value')

    def test_delattr_uninit(self):
        class TestSchema(schema.Schema):
            __version__ = 1
            attr = attribute.Attribute('default')
        sch = TestSchema()

        def test_func():
            del sch.attr

        self.assertRaises(RuntimeError, test_func)

    def test_delattr(self):
        class TestSchema(schema.Schema):
            __version__ = 1
            attr = attribute.Attribute('default')
        sch = TestSchema({})

        def test_func():
            del sch.attr

        self.assertRaises(AttributeError, test_func)
        self.assertEqual(sch.__vers_values__, dict(attr='default'))

    def test_delattr_nosuch(self):
        class TestSchema(schema.Schema):
            __version__ = 1
        sch = TestSchema({})
        sch.attr = 'some value'

        del sch.attr

        self.assertFalse(hasattr(sch, 'attr'))
        self.assertEqual(sch.__vers_values__, {})

    def test_eq_uninit(self):
        class TestSchema(schema.Schema):
            __version__ = 1
            attr1 = attribute.Attribute()
            attr2 = attribute.Attribute()

        sch1 = TestSchema()
        sch2 = TestSchema()

        self.assertRaises(RuntimeError, lambda: (sch1 == sch2))

    def test_eq_equal(self):
        class TestSchema(schema.Schema):
            __version__ = 1
            attr1 = attribute.Attribute()
            attr2 = attribute.Attribute()

        sch1 = TestSchema(dict(attr1=1, attr2=2))
        sch2 = TestSchema(dict(attr1=1, attr2=2))

        self.assertTrue(sch1 == sch2)

    def test_eq_unequal_class(self):
        class TestSchema1(schema.Schema):
            __version__ = 1
            attr1 = attribute.Attribute()
            attr2 = attribute.Attribute()

        class TestSchema2(schema.Schema):
            __version__ = 1
            attr1 = attribute.Attribute()
            attr2 = attribute.Attribute()

        sch1 = TestSchema1(dict(attr1=1, attr2=2))
        sch2 = TestSchema2(dict(attr1=1, attr2=2))

        self.assertFalse(sch1 == sch2)

    def test_eq_unequal_value(self):
        class TestSchema(schema.Schema):
            __version__ = 1
            attr1 = attribute.Attribute()
            attr2 = attribute.Attribute()

        sch1 = TestSchema(dict(attr1=1, attr2=2))
        sch2 = TestSchema(dict(attr1=2, attr2=1))

        self.assertFalse(sch1 == sch2)

    def test_ne_uninit(self):
        class TestSchema(schema.Schema):
            __version__ = 1
            attr1 = attribute.Attribute()
            attr2 = attribute.Attribute()

        sch1 = TestSchema()
        sch2 = TestSchema()

        self.assertRaises(RuntimeError, lambda: (sch1 != sch2))

    def test_ne_equal(self):
        class TestSchema(schema.Schema):
            __version__ = 1
            attr1 = attribute.Attribute()
            attr2 = attribute.Attribute()

        sch1 = TestSchema(dict(attr1=1, attr2=2))
        sch2 = TestSchema(dict(attr1=1, attr2=2))

        self.assertFalse(sch1 != sch2)

    def test_ne_unequal_class(self):
        class TestSchema1(schema.Schema):
            __version__ = 1
            attr1 = attribute.Attribute()
            attr2 = attribute.Attribute()

        class TestSchema2(schema.Schema):
            __version__ = 1
            attr1 = attribute.Attribute()
            attr2 = attribute.Attribute()

        sch1 = TestSchema1(dict(attr1=1, attr2=2))
        sch2 = TestSchema2(dict(attr1=1, attr2=2))

        self.assertTrue(sch1 != sch2)

    def test_ne_unequal_value(self):
        class TestSchema(schema.Schema):
            __version__ = 1
            attr1 = attribute.Attribute()
            attr2 = attribute.Attribute()

        sch1 = TestSchema(dict(attr1=1, attr2=2))
        sch2 = TestSchema(dict(attr1=2, attr2=1))

        self.assertTrue(sch1 != sch2)

    def test_getstate_uninit(self):
        class TestSchema(schema.Schema):
            __version__ = 1
            attr1 = attribute.Attribute()
            attr2 = attribute.Attribute()
        sch = TestSchema()

        self.assertRaises(RuntimeError, sch.__getstate__)

    def test_getstate(self):
        class TestSchema(schema.Schema):
            __version__ = 1
            attr1 = attribute.Attribute()
            attr2 = attribute.Attribute(getstate=str)
        sch = TestSchema(dict(attr1=1, attr2=2))

        state = sch.__getstate__()

        self.assertEqual(state, dict(__version__=1, attr1=1, attr2='2'))
        self.assertEqual(sch.__vers_values__, dict(attr1=1, attr2=2))

    def test_setstate_abstract(self):
        class EmptyClass(object):
            pass

        sch = EmptyClass()
        sch.__class__ = schema.Schema

        self.assertRaises(TypeError, sch.__setstate__, {})

    def test_setstate_unversioned(self):
        class TestSchema(schema.Schema):
            __version__ = 1
        sch = TestSchema()

        self.assertRaises(ValueError, sch.__setstate__, {})

    def test_setstate_version_mismatch(self):
        class TestSchema(schema.Schema):
            __version__ = 1
        sch = TestSchema()

        self.assertRaises(ValueError, sch.__setstate__, dict(__version__=2))

    def test_setstate_unexpected_attr(self):
        class TestSchema(schema.Schema):
            __version__ = 1
        sch = TestSchema()

        self.assertRaises(ValueError, sch.__setstate__,
                          dict(__version__=1, attr=1))

    def test_setstate_missing_attr(self):
        class TestSchema(schema.Schema):
            __version__ = 1
            attr = attribute.Attribute('default')
        sch = TestSchema()

        self.assertRaises(ValueError, sch.__setstate__, dict(__version__=1))

    def test_setstate(self):
        validator = mock.Mock(return_value='validated')

        class TestSchema(schema.Schema):
            __version__ = 1
            attr = attribute.Attribute('default', validate=validator)
        sch = TestSchema()

        sch.__setstate__(dict(__version__=1, attr='value'))

        self.assertEqual(sch.__vers_values__, dict(attr='validated'))
        validator.assert_called_once_with('value')
