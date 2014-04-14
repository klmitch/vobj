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


class Converters(list):
    """
    Represents a list of converters (upgraders or downgraders) that
    perform a series of state conversions to generate a desired target
    schema object.  The ``__call__()`` method is implemented to
    perform the complete conversion.  Note that the conversions are
    applied to a state in reverse order; that is, the last is applied,
    then the next to last, etc.
    """

    def __init__(self, target, *conversions):
        """
        Initialize a ``Converters`` object.

        :param target: The target schema, a ``Schema`` subclass.
        :param conversions: An initial list of conversions to apply.
        """

        super(Converters, self).__init__(conversions)

        self._target_schema = target

    def __call__(self, state):
        """
        Apply conversions to a given state.  The conversions are
        applied in reverse order.

        :param state: The state to apply the conversions to.  Note
                      that this state will be modified in place.

        :returns: An instance of the target schema passed to the
                  constructor.
        """

        # Start by dropping the __version__
        del state['__version__']

        # Now, call each converter in turn
        for converter in reversed(self):
            state = converter(state)

        # We now have an appropriate state; set the version...
        state['__version__'] = self._target_schema.__version__

        # Generate the schema object
        sch_obj = self._target_schema()
        sch_obj.__setstate__(state)

        return sch_obj
