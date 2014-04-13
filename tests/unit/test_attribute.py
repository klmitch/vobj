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

import unittest

from vobj import attribute


class AttributeTest(unittest.TestCase):
    def test_init_defaults(self):
        attr = attribute.Attribute()

        self.assertEqual(attr.default, attribute.unset)
        self.assertTrue(callable(attr.validate))
        self.assertEqual(attr.validate('spam'), 'spam')
        self.assertTrue(callable(attr.getstate))
        self.assertEqual(attr.getstate('spam'), 'spam')

    def test_init(self):
        attr = attribute.Attribute('default', validate='validate',
                                   getstate='getstate')

        self.assertEqual(attr.default, 'default')
        self.assertEqual(attr.validate, 'validate')
        self.assertEqual(attr.getstate, 'getstate')
