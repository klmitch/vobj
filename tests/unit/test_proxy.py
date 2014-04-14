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

from vobj import proxy


class SchemaProxyTest(unittest.TestCase):
    def init_proxy(self, *args, **kwargs):
        if args:
            values = args[0]
        else:
            attrs = list(kwargs.keys()) + ['__contains__']
            values = mock.Mock(spec=attrs, **kwargs)
            values.__contains__ = mock.Mock(side_effect=lambda x: x in kwargs)
        prox = proxy.SchemaProxy()
        super(proxy.SchemaProxy, prox).__setattr__(
            '__vers_values__', values)

        return prox

    def test_getattr(self):
        prox = self.init_proxy(attr='value')

        self.assertEqual(prox.attr, 'value')

    def test_delattr_proxied(self):
        prox = self.init_proxy(attr='value')

        def test_func():
            del prox.attr

        self.assertRaises(AttributeError, test_func)

    def test_delattr_unproxied(self):
        prox = self.init_proxy(attr='value')
        super(proxy.SchemaProxy, prox).__setattr__(
            'other', 'value')

        del prox.other

        self.assertRaises(AttributeError, lambda: prox.other)

    def test_eq_equal(self):
        prox1 = self.init_proxy('value1')
        prox2 = self.init_proxy('value1')

        self.assertTrue(prox1 == prox2)

    def test_eq_unequal(self):
        prox1 = self.init_proxy('value1')
        prox2 = self.init_proxy('value2')

        self.assertFalse(prox1 == prox2)

    def test_ne_equal(self):
        prox1 = self.init_proxy('value1')
        prox2 = self.init_proxy('value1')

        self.assertFalse(prox1 != prox2)

    def test_ne_unequal(self):
        prox1 = self.init_proxy('value1')
        prox2 = self.init_proxy('value2')

        self.assertTrue(prox1 != prox2)

    def test_getstate(self):
        values = mock.Mock(__getstate__=mock.Mock(return_value='state'))
        prox = self.init_proxy(values)

        result = prox.__getstate__()

        self.assertEqual(result, 'state')

    def test_to_dict(self):
        values = mock.Mock(__getstate__=mock.Mock(return_value='state'))
        prox = self.init_proxy(values)

        result = prox.to_dict()

        self.assertEqual(result, 'state')

    def test_vers_set_values(self):
        prox = proxy.SchemaProxy()

        prox.__vers_set_values__('values')

        self.assertEqual(prox.__vers_values__, 'values')


class ReadOnlyLazySchemaProxyTest(unittest.TestCase):
    def init_proxy(self, *args, **kwargs):
        # Set up the values
        if args:
            values = args[0]
        else:
            attrs = list(kwargs.keys()) + ['__contains__']
            values = mock.Mock(spec=attrs, **kwargs)
            values.__contains__ = mock.Mock(side_effect=lambda x: x in kwargs)

        # Set up the master
        master = mock.Mock(__vers_cache_get__=mock.Mock(return_value=values))

        # Set up the version
        version = mock.Mock(_master=master, __int__=mock.Mock(return_value=23))

        # Set up the proxy
        prox = proxy.ReadOnlyLazySchemaProxy(version)

        return prox, {
            'values': values,
            'master': master,
            'version': version,
        }

    def test_init(self):
        prox, extra = self.init_proxy()

        self.assertEqual(prox.__version__, extra['version'])
        self.assertEqual(prox.__vers_master__, extra['master'])

    def test_setattr_proxied(self):
        prox, extra = self.init_proxy(attr='value')

        def test_func():
            prox.attr = 'other'

        self.assertRaises(AttributeError, test_func)
        self.assertEqual(prox.attr, 'value')

    def test_setattr_unproxied(self):
        prox, extra = self.init_proxy(attr='value')

        prox.other = 'something'

        self.assertEqual(prox.other, 'something')

    def test_vers_values(self):
        prox, extra = self.init_proxy()

        result = prox.__vers_values__

        self.assertEqual(result, extra['values'])
        extra['master'].__vers_cache_get__.assert_called_once_with(23)
