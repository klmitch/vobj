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


# Used to distinguish an unset default from any other value
unset = object()


class Attribute(object):
    """
    Describe an attribute.
    """

    def __init__(self, default=unset, validate=lambda x: x,
                 getstate=lambda x: x):
        """
        Initialize an ``Attribute`` object.

        :param default: The default value of the attribute.  If unset,
                        creating new objects will require a value for
                        the attribute.
        :param validate: A function that validates values passed in to
                         the constructor.  Should canonicalize the
                         value into the desired type, which it should
                         return.  Can raise ``TypeError`` or
                         ``ValueError`` if the value is invalid.
        :param getstate: A function that serializes the attribute
                         value when the versioned object state is
                         requested.  Should convert the attribute
                         value into a form acceptable to the
                         ``validate`` function.
        """

        self.default = default
        self.validate = validate
        self.getstate = getstate
