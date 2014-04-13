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


class SmartVersion(int):
    """
    Used as the value of special ``__version__`` attributes.  For all
    operations defined for integers, acts as a simple integer with the
    declared version.  Additionally implements some item access
    protocol elements to allow access to representations in older
    versions.
    """

    def __new__(cls, version, schema, master=None):
        """
        Initialize a ``SmartVersion`` object.

        :param version: The integer version to advertise.
        :param schema: The latest schema.
        :param master: If provided, the object containing the master
                       data.  If not provided, no downgraded version
                       of the data will be available; item access will
                       result in a ``RuntimeError`` exception.
        """

        obj = super(SmartVersion, cls).__new__(cls, version)
        obj._schema = schema
        obj._master = master

        return obj

    def __len__(self):
        """
        Return the number of available versions.

        :returns: The number of available versions.
        """

        # Short-circuit
        if not self._schema:
            return 0

        return len(self._schema.__vers_downgraders__) + 1

    def __contains__(self, key):
        """
        Determine whether the designated version is available.

        :param key: The version to check.

        :returns: A ``True`` value if the designated version is
                  available, ``False`` otherwise.
        """

        # Short-circuit
        if not self._schema:
            return False
        elif key == self._schema.__version__:
            # Schema version
            return True

        return key in self._schema.__vers_downgraders__

    def __getitem__(self, key):
        """
        Retrieve an object with the designated version.

        :param key: The desired version.

        :returns: An object containing the designated version.
        """

        if self._master is None:
            raise RuntimeError("Cannot get an older version of a class")
        elif not self._schema:
            raise KeyError(key)

        # If key is the schema version, return the master object
        if key == self._schema.__version__:
            return self._master

        # Check if the version is available
        elif key not in self._schema.__vers_downgraders__:
            raise KeyError(key)

        # Get the accessor from the master object
        return self._master.__vers_accessor__(key)

    def available(self):
        """
        Returns a set of the available versions.

        :returns: A set of integers giving the available versions.
        """

        # Short-circuit
        if not self._schema:
            return set()

        # Build up the set of available versions
        avail = set(self._schema.__vers_downgraders__.keys())
        avail.add(self._schema.__version__)

        return avail
