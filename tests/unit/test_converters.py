# Copyright 2014 Rackspace
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

from vobj import converters


class ConvertersTest(unittest.TestCase):
    def test_init(self):
        result = converters.Converters('target', 'conv3', 'conv2', 'conv1')

        self.assertEqual(result._target_schema, 'target')
        self.assertEqual(result, ['conv3', 'conv2', 'conv1'])

    def test_call(self):
        states = [{'from': 'conv%d' % i} for i in range(4)]
        states[0]['__version__'] = 5
        test_cvtrs = mock.Mock(**dict(
            ('%s.return_value' % state['from'], state)
            for state in states[1:]
        ))
        sch_obj = mock.Mock(__setstate__=mock.Mock())
        schema = mock.Mock(return_value=sch_obj, __version__=10)
        cvtr = converters.Converters(schema, test_cvtrs.conv3,
                                     test_cvtrs.conv2, test_cvtrs.conv1)

        result = cvtr(states[0])

        self.assertEqual(result, sch_obj)
        self.assertEqual(states[0], {'from': 'conv0'})
        test_cvtrs.assert_has_calls([
            mock.call.conv1(states[0]),
            mock.call.conv2(states[1]),
            mock.call.conv3(states[2]),
        ])
        self.assertEqual(len(test_cvtrs.method_calls), 3)
        self.assertEqual(states[3], {'__version__': 10, 'from': 'conv3'})
        schema.assert_called_once_with()
        sch_obj.__setstate__.assert_called_once_with(states[3])
