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

from __future__ import division

import six


# Used to distinguish an unset default from any other value
unset = object()


class SmartVersion(object):
    """
    Used as the value of special ``__version__`` attributes.  For all
    operations defined for integers, acts as a simple integer with the
    declared version.  Additionally implements some item access
    protocol elements to allow access to representations in older
    versions.
    """

    def __init__(self, version, schema, master=None):
        """
        Initialize a ``SmartVersion`` object.

        :param version: The integer version to advertise.
        :param schema: The latest schema.
        :param master: If provided, the object containing the master
                       data.  If not provided, no downgraded version
                       of the data will be available; item access will
                       result in a ``RuntimeError`` exception.
        """

        self._version = version
        self._schema = schema
        self._master = master

    def __repr__(self):
        """
        Return a representation of the version.

        :returns: A representation of the version.
        """

        return repr(self._version)

    def __str__(self):
        """
        Return the version as a string.

        :returns: The version as a string.
        """

        return str(self._version)

    def __unicode__(self):
        """
        Return the version as unicode.

        :returns: The version as unicode.
        """

        return six.text_type(self._version)  # pragma: no cover

    def __lt__(self, other):
        """
        Compare the smart version to something else.

        :param other: The something else to compare to.

        :returns: The result of the comparison.
        """

        if isinstance(other, SmartVersion):
            return self._version < other._version
        return self._version < other

    def __le__(self, other):
        """
        Compare the smart version to something else.

        :param other: The something else to compare to.

        :returns: The result of the comparison.
        """

        if isinstance(other, SmartVersion):
            return self._version <= other._version
        return self._version <= other

    def __eq__(self, other):
        """
        Compare the smart version to something else.

        :param other: The something else to compare to.

        :returns: The result of the comparison.
        """

        if isinstance(other, SmartVersion):
            return self._version == other._version
        return self._version == other

    def __ne__(self, other):
        """
        Compare the smart version to something else.

        :param other: The something else to compare to.

        :returns: The result of the comparison.
        """

        if isinstance(other, SmartVersion):
            return self._version != other._version
        return self._version != other

    def __gt__(self, other):
        """
        Compare the smart version to something else.

        :param other: The something else to compare to.

        :returns: The result of the comparison.
        """

        if isinstance(other, SmartVersion):
            return self._version > other._version
        return self._version > other

    def __ge__(self, other):
        """
        Compare the smart version to something else.

        :param other: The something else to compare to.

        :returns: The result of the comparison.
        """

        if isinstance(other, SmartVersion):
            return self._version >= other._version
        return self._version >= other

    def __hash__(self):
        """
        Return the hash value of the version.

        :returns: The hash value of the version.
        """

        return hash(self._version)

    def __bool__(self):
        """
        Since version numbers must always be greater than 0, returns
        ``True``.

        :returns: The value ``True``.
        """

        return True

    __nonzero__ = __bool__

    def __add__(self, other):
        """
        Perform an arithmetic operation with something else.

        :param other: The something else to operate with.

        :returns: The result of the arithmetic operation.
        """

        if isinstance(other, SmartVersion):
            return self._version + other._version
        return self._version + other

    def __sub__(self, other):
        """
        Perform an arithmetic operation with something else.

        :param other: The something else to operate with.

        :returns: The result of the arithmetic operation.
        """

        if isinstance(other, SmartVersion):
            return self._version - other._version
        return self._version - other

    def __mul__(self, other):
        """
        Perform an arithmetic operation with something else.

        :param other: The something else to operate with.

        :returns: The result of the arithmetic operation.
        """

        if isinstance(other, SmartVersion):
            return self._version * other._version
        return self._version * other

    def __floordiv__(self, other):
        """
        Perform an arithmetic operation with something else.

        :param other: The something else to operate with.

        :returns: The result of the arithmetic operation.
        """

        if isinstance(other, SmartVersion):
            return self._version // other._version
        return self._version // other

    __div__ = __floordiv__

    def __truediv__(self, other):
        """
        Perform an arithmetic operation with something else.

        :param other: The something else to operate with.

        :returns: The result of the arithmetic operation.
        """

        if isinstance(other, SmartVersion):
            return self._version / other._version
        return self._version / other

    def __mod__(self, other):
        """
        Perform an arithmetic operation with something else.

        :param other: The something else to operate with.

        :returns: The result of the arithmetic operation.
        """

        if isinstance(other, SmartVersion):
            return self._version % other._version
        return self._version % other

    def __divmod__(self, other):
        """
        Perform an arithmetic operation with something else.

        :param other: The something else to operate with.

        :returns: The result of the arithmetic operation.
        """

        if isinstance(other, SmartVersion):
            return divmod(self._version, other._version)
        return divmod(self._version, other)

    def __pow__(self, other, modulo=unset):
        """
        Perform an arithmetic operation with something else.

        :param other: The something else to operate with.
        :param modulo: If provided, a modulus value to use in the
                       calculation.

        :returns: The result of the arithmetic operation.
        """

        if modulo is unset:
            if isinstance(other, SmartVersion):
                return pow(self._version, other._version)
            return pow(self._version, other)

        if isinstance(modulo, SmartVersion):
            modulo = modulo._version

        if isinstance(other, SmartVersion):
            return pow(self._version, other._version, modulo)
        return pow(self._version, other, modulo)

    def __lshift__(self, other):
        """
        Perform an arithmetic operation with something else.

        :param other: The something else to operate with.

        :returns: The result of the arithmetic operation.
        """

        if isinstance(other, SmartVersion):
            return self._version << other._version
        return self._version << other

    def __rshift__(self, other):
        """
        Perform an arithmetic operation with something else.

        :param other: The something else to operate with.

        :returns: The result of the arithmetic operation.
        """

        if isinstance(other, SmartVersion):
            return self._version >> other._version
        return self._version >> other

    def __and__(self, other):
        """
        Perform an arithmetic operation with something else.

        :param other: The something else to operate with.

        :returns: The result of the arithmetic operation.
        """

        if isinstance(other, SmartVersion):
            return self._version & other._version
        return self._version & other

    def __xor__(self, other):
        """
        Perform an arithmetic operation with something else.

        :param other: The something else to operate with.

        :returns: The result of the arithmetic operation.
        """

        if isinstance(other, SmartVersion):
            return self._version ^ other._version
        return self._version ^ other

    def __or__(self, other):
        """
        Perform an arithmetic operation with something else.

        :param other: The something else to operate with.

        :returns: The result of the arithmetic operation.
        """

        if isinstance(other, SmartVersion):
            return self._version | other._version
        return self._version | other

    def __radd__(self, other):
        """
        Perform a reflected arithmetic operation with something else.

        :param other: The something else to operate with.

        :returns: The result of the arithmetic operation.
        """

        return other + self._version

    def __rsub__(self, other):
        """
        Perform a reflected arithmetic operation with something else.

        :param other: The something else to operate with.

        :returns: The result of the arithmetic operation.
        """

        return other - self._version

    def __rmul__(self, other):
        """
        Perform a reflected arithmetic operation with something else.

        :param other: The something else to operate with.

        :returns: The result of the arithmetic operation.
        """

        return other * self._version

    def __rfloordiv__(self, other):
        """
        Perform a reflected arithmetic operation with something else.

        :param other: The something else to operate with.

        :returns: The result of the arithmetic operation.
        """

        return other // self._version

    __rdiv__ = __rfloordiv__

    def __rtruediv__(self, other):
        """
        Perform a reflected arithmetic operation with something else.

        :param other: The something else to operate with.

        :returns: The result of the arithmetic operation.
        """

        return other / self._version

    def __rmod__(self, other):
        """
        Perform a reflected arithmetic operation with something else.

        :param other: The something else to operate with.

        :returns: The result of the arithmetic operation.
        """

        return other % self._version

    def __rdivmod__(self, other):
        """
        Perform a reflected arithmetic operation with something else.

        :param other: The something else to operate with.

        :returns: The result of the arithmetic operation.
        """

        return divmod(other, self._version)

    def __rpow__(self, other):
        """
        Perform a reflected arithmetic operation with something else.

        :param other: The something else to operate with.

        :returns: The result of the arithmetic operation.
        """

        return pow(other, self._version)

    def __rlshift__(self, other):
        """
        Perform a reflected arithmetic operation with something else.

        :param other: The something else to operate with.

        :returns: The result of the arithmetic operation.
        """

        return other << self._version

    def __rrshift__(self, other):
        """
        Perform a reflected arithmetic operation with something else.

        :param other: The something else to operate with.

        :returns: The result of the arithmetic operation.
        """

        return other >> self._version

    def __rand__(self, other):
        """
        Perform a reflected arithmetic operation with something else.

        :param other: The something else to operate with.

        :returns: The result of the arithmetic operation.
        """

        return other & self._version

    def __rxor__(self, other):
        """
        Perform a reflected arithmetic operation with something else.

        :param other: The something else to operate with.

        :returns: The result of the arithmetic operation.
        """

        return other ^ self._version

    def __ror__(self, other):
        """
        Perform a reflected arithmetic operation with something else.

        :param other: The something else to operate with.

        :returns: The result of the arithmetic operation.
        """

        return other | self._version

    def __neg__(self):
        """
        Perform a unary arithmetic operation on the version.

        :returns: The result of the arithmetic operation.
        """

        return -self._version

    def __pos__(self):
        """
        Perform a unary arithmetic operation on the version.

        :returns: The result of the arithmetic operation.
        """

        return +self._version

    def __abs__(self):
        """
        Perform a unary arithmetic operation on the version.

        :returns: The result of the arithmetic operation.
        """

        return abs(self._version)

    def __invert__(self):
        """
        Perform a unary arithmetic operation on the version.

        :returns: The result of the arithmetic operation.
        """

        return ~self._version

    def __complex__(self):
        """
        Convert the version to a complex object.

        :returns: The version as a complex object.
        """

        return complex(self._version)

    def __int__(self):
        """
        Convert the version to an integer.

        :returns: The version as an integer.
        """

        return int(self._version)

    def __long__(self):
        """
        Convert the version to a long.  Note that this is undefined in
        Python 3.

        :returns: The version as a long.
        """

        return long(self._version)  # pragma: no cover

    def __float__(self):
        """
        Convert the version to a float.

        :returns: The version as a float.
        """

        return float(self._version)

    def __round__(self, n=0):
        """
        Round the value to an integer.

        :returns: The version rounded to the specified number of
                  decimal places.
        """

        return round(self._version, n)  # pragma: no cover

    def __oct__(self):
        """
        Convert the version to an octal string.

        :returns: The octal string for the version.
        """

        return oct(self._version)  # pragma: no cover

    def __hex__(self):
        """
        Convert the version to a hexadecimal string.

        :returns: The hexadecimal string for the version.
        """

        return hex(self._version)  # pragma: no cover

    def __index__(self):
        """
        Return the index of the version.

        :returns: The integer value of the version.
        """

        return self._version

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
