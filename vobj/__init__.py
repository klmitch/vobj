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

import inspect

from vobj.attribute import Attribute
from vobj.schema import Schema

from vobj.attribute import unset as _unset


__all__ = ['Attribute', 'upgrader', 'Schema', 'VObject']


def upgrader(version=None):
    """
    A decorator for marking a method as an upgrader from an older
    version of a given object.  Can be used in two different ways:

    ``@upgrader``
        In this usage, the decorated method updates from the previous
        schema version to this schema version.

    ``@upgrader(number)``
        In this usage, the decorated method updates from the
        designated schema version to this schema version.

    Note that upgrader methods are implicitly class methods, as the
    ``Schema`` object has not been constructed at the time the
    upgrader method is called.  Also note that upgraders take a single
    argument--a dictionary of attributes--and must return a
    dictionary.  Upgraders may modify the argument in place, if
    desired.

    :param version: The version number the upgrader converts from.
    """

    def decorator(func):
        # Save the version to update from
        func.__vers_upgrader__ = version
        return func

    # What is version?  It can be None, an int, or a callable,
    # depending on how @upgrader() was called
    if version is None:
        # Called as @upgrader(); return the decorator
        return decorator
    elif isinstance(version, (int, long)):
        # Called as @upgrader(1); sanity-check version and return the
        # decorator
        if version < 1:
            raise TypeError("Invalid upgrader version number %r" % version)
        return decorator
    elif callable(version):
        # Called as @upgrader; use version = None and call the
        # decorator
        func = version
        version = None
        return decorator(func)
    else:
        # Called with an invalid version
        raise TypeError("Invalid upgrader version number %r" % version)


def downgrader(version):
    """
    A decorator for marking a method as a downgrader to an older
    version of a given object.  Note that downgrader methods are
    implicitly class methods.  Also note that downgraders take a
    single argument--a dictionary of attributes--and must return a
    dictionary.  Downgraders may modify the argument in place, if
    desired.

    :param version: The version number the downgrader returns the
                    attributes for.  Must be provided.
    """

    def decorator(func):
        # Save the version to downgrade to
        func.__vers_downgrader__ = version
        return func

    # Sanity-check the version number
    if not isinstance(version, (int, long)) or version < 1:
        raise TypeError("Invalid downgrader version number %r" % version)

    return decorator


class _EmptyClass(object):
    """
    An empty class.  This is used by ``VObject.from_dict()`` when
    constructing a ``VObject`` subclass from a dictionary.
    """

    pass


class SmartVersion(object):
    """
    Used as the value of the special ``__version__`` attribute of
    VObject.  For all operations defined for integers, acts as a
    simple integer with the value of the latest version of the object.
    Additionally implements some item access protocol elements
    corresponding to defined downgraders; this allows read-only access
    to attributes defined in older schemas.  In particular, ``len()``
    reports the total number of versions that may be accessed; the
    ``in`` operator reports whether a particular version is available;
    item access retrieves an object corresponding to the matching
    version; and the ``available()`` method returns a set of all
    recognized versions.
    """

    def __init__(self, version, schema, master=None):
        """
        Initialize a ``SmartVersion`` object.

        :param version: The integer version to express.
        :param schema: The latest schema.
        :param master: If provided, the object containing the master
                       data.  If not provided, no downgraded versions
                       of the data will be available; item access will
                       result in a ``RuntimeError`` exception.
        """

        self._version = version
        self._schema = schema
        self._master = master

    def __repr__(self):
        """
        Return a representation of the version.
        """

        return repr(self._version)

    def __str__(self):
        """
        Return the version as a string.
        """

        return str(self._version)

    def __unicode__(self):
        """
        Return the version as unicode.
        """

        return unicode(self._version)

    def __complex__(self):
        """
        Convert the version to a complex object.
        """

        return complex(self._version)

    def __int__(self):
        """
        Convert the version to an integer.
        """

        return self._version

    def __long__(self):
        """
        Convert the version to a long.
        """

        return long(self._version)

    def __float__(self):
        """
        Convert the version to a float.
        """

        return float(self._version)

    def __oct__(self):
        """
        Convert the version to an octal string.
        """

        return oct(self._version)

    def __hex__(self):
        """
        Convert the version to a hexadecimal string.
        """

        return hex(self._version)

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
        """

        return hash(self._version)

    def __nonzero__(self):
        """
        Since version numbers must always be greater than 0, returns
        ``True``.
        """

        return True

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

    def __div__(self, other):
        """
        Perform an arithmetic operation with something else.

        :param other: The something else to operate with.

        :returns: The result of the arithmetic operation.
        """

        if isinstance(other, SmartVersion):
            return self._version // other._version
        return self._version // other
    __floordiv__ = __div__

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

    def __pow__(self, other, modulo=_unset):
        """
        Perform an arithmetic operation with something else.

        :param other: The something else to operate with.
        :param modulo: If provided, a modulus value to use in the
                       calculation.

        :returns: The result of the arithmetic operation.
        """

        if modulo is _unset:
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

    def __rdiv__(self, other):
        """
        Perform a reflected arithmetic operation with something else.

        :param other: The something else to operate with.

        :returns: The result of the arithmetic operation.
        """

        return other // self._version
    __rfloordiv__ = __rdiv__

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

    def __index__(self):
        """
        Return the index of the version.
        """

        return self._version

    def __len__(self):
        """
        Return the number of available versions.
        """

        if not self._schema:
            return 0
        return len(self._schema.__vers_downgraders__) + 1

    def __contains__(self, key):
        """
        Determine whether the designated version is available.

        :param key: The version to check.
        """

        if not self._schema:
            return False
        elif key == self._schema.__version__:
            return True

        return key in self._schema.__vers_downgraders__

    def __getitem__(self, key):
        """
        Retrieve an object with the designated version.

        :param key: The desired version.

        :returns: An object containing the designated version.
        """

        if self._master is None:
            raise RuntimeError("Cannot get an older version of this class")
        elif not self._schema:
            raise KeyError(key)  # shouldn't ever happen, though

        # If key is the schema version, return the master object
        if key == self._schema.__version__:
            return self._master

        # Check if the version is available
        elif key not in self._schema.__vers_downgraders__:
            raise KeyError(key)

        # Check if we have the accessor cached
        if key not in self._master.__vers_cache__:
            # XXX allocate a new accessor
            pass

        return self._master.__vers_cache__[key]

    def available(self):
        """
        Returns a set of the available versions.
        """

        if not self._schema:
            return set()

        avail = set(self._schema.__vers_downgraders__.keys())
        avail.add(self._schema.__version__)
        return avail


class Downgrader(object):
    """
    Represent a downgrader that will be called to obtain a specific
    schema.  This is called to regenerate a cached older-version
    object.
    """

    def __init__(self, downgrader, schema):
        """
        Initialize a ``Downgrader``.

        :param downgrader: The class method that will be called.
        :param schema: The schema class to generate.
        """

        self.downgrader = downgrader
        self.schema = schema

    def __call__(self, state):
        """
        Called to regenerate the ``Schema`` object corresponding to an
        older version of the versioned object.

        :param state: A dictionary containing the current state.  This
                      dictionary will be mutated.

        :returns: A ``Schema`` object.
        """

        # Drop the __version__; we know state is a copy, so this is
        # safe
        del state['__version__']

        # Call the downgrader
        state = self.downgrader(state)

        # Update the version in the resultant state
        state['__version__'] = self.schema.__version__

        # Now, let's construct the Schema object that will store this
        # state
        values = self.schema()
        values.__setstate__(state)

        # Return the result
        return values


class VObjectMeta(type):
    """
    A metaclass for versioned objects.  A ``VObject`` subclass
    describes an object with several variants, expressed as ``Schema``
    subclasses that are members of the ``VObject`` subclass.  Each
    ``Schema`` subclass additionally expresses how to convert a
    dictionary describing an older version of the data object into
    that schema.
    """

    def __new__(mcs, name, bases, namespace):
        """
        Construct a new ``VObject`` subclass.

        :param name: The name of the ``VObject`` subclass.
        :param bases: A tuple of the base classes.
        :param namespace: A dictionary containing the namespace of the
                          class.

        :returns: The newly-constructed ``VObject`` subclass.
        """

        versions = {}

        # Collect all schemas...
        for key, value in namespace.items():
            if inspect.isclass(value) and issubclass(value, Schema):
                if getattr(value, '__version__', None) is None:
                    # Ignore abstract schemas
                    continue

                # Make sure we don't have a multiply-defined schema
                # version
                if value.__version__ in versions:
                    raise TypeError("Version %s defined by schemas %r and %r" %
                                    (versions[value.__version__].__name__,
                                     key))

                versions[value.__version__] = value

        # Make sure there are no gaps
        if set(versions.keys()) != set(range(1, len(versions) + 1)):
            raise TypeError("Gaps are present in the schema versions")

        # Condense versions into a list
        schemas = [v for k, v in sorted(versions.items(), key=lambda x: x[0])]
        last_schema = schemas[-1] if schemas else None

        # Set up downgraders
        if last_schema:
            downgraders = dict(
                (vers, Downgrader(down, versions[vers]))
                for vers, down in last_schema.__vers_downgraders__.items()
            )
        else:
            downgraders = {}

        # Now make our additions to the namespace
        namespace['__vers_schemas__'] = schemas
        namespace['__vers_downgraders__'] = downgraders
        namespace['__version__'] = SmartVersion(len(schemas), last_schema)

        return super(VObjectMeta, mcs).__new__(mcs, name, bases, namespace)


def _call_upgrader(upgrader, state):
    """
    Call an upgrader.  Handles updating of the state's "__version__"
    key.

    :param upgrader: The upgrader method.
    :param state: The state dictionary.

    :returns: The upgraded state dictionary.
    """

    # Copy the state and drop its __version__...
    state = state.copy()
    del state['__version__']

    # Call the upgrader
    state = upgrader(state)

    # Now, update the version in the resultant state
    state['__version__'] = upgrader.im_self.__version__

    return state


class VObject(object):
    """
    Describe a versioned object.  A ``VObject`` subclass describes all
    recognized versions of the object, through ``Schema`` subclasses
    defined as part of the ``VObject`` subclass.  Versioned objects
    can be safely pickled and unpickled; the ``Schema`` update methods
    make it possible to unpickle an older version of the object
    safely.  Versioned objects can also be converted to and from raw
    dictionaries using the ``to_dict()`` and ``from_dict()`` methods.
    """

    __metaclass__ = VObjectMeta

    def __new__(cls, **kwargs):
        """
        Construct a new instance of the ``VObject`` subclass.
        Verifies that the ``VObject`` subclass is not abstract (has no
        schemas).  Raises a ``TypeError`` if it is.

        :returns: A newly constructed instance of the ``VObject``
                  subclass.
        """

        # Prohibit instantiating abstract versioned objects
        if not getattr(cls, '__vers_schemas__', None):
            raise TypeError("cannot instantiate abstract versioned object "
                            "class %r" % cls.__name__)

        return super(VObject, cls).__new__(cls)

    def __init__(self, **kwargs):
        """
        Initialize a ``VObject`` instance.  The keyword arguments
        specify the values of declared attributes.  If an attribute is
        left out, the declared default (if any) will be used.  If no
        default was declared, a ``TypeError`` will be raised.
        """

        values = self.__vers_schemas__[-1](kwargs)

        # Save the values
        self.__vers_init__(values)

    def __vers_init__(self, values, version=None):
        """
        Initialize a ``VObject`` instance.  This contains all the
        common initialization routines, including those called by such
        methods as ``__setstate__()``, when ``__init__()`` doesn't get
        called.

        :param values: An initialized ``Schema`` object.
        :param version: The version to advertise in ``__version__``.
                        If not specified, the version of the latest
                        schema will be used.
        """

        # Save the values
        super(VObject, self).__setattr__('__vers_values__', values)

        # Set up the local version
        if not version:
            version = int(self.__version__)
        version = SmartVersion(version, self.__vers_schemas__[-1], self)
        super(VObject, self).__setattr__('__version__', version)

    def __getattr__(self, name):
        """
        Retrieve the value of a declared attribute.

        :param name: The name of the attribute.

        :returns: The value of the declared attribute.
        """

        # Delegate to the Schema object; this covers not just the data
        # attributes, but also any methods or descriptors
        return getattr(self.__vers_values__, name)

    def __setattr__(self, name, value):
        """
        Sets the value of an attribute or property.

        :param name: The name of the attribute.
        :param value: The new value of the attribute.
        """

        # If it's in the Schema object, delegate to it
        if name in self.__vers_values__:
            setattr(self.__vers_values__, name, value)
        else:
            super(VObject, self).__setattr__(name, value)

    def __delattr__(self, name):
        """
        Deletes an attribute.  This cannot be called on a declared
        attribute; if it is, an ``AttributeError`` will be raised.

        :param name: The name of the attribute.
        """

        # Don't allow deletes of specially declared attributes
        if name in self.__vers_values__:
            raise AttributeError("cannot delete attribute %r of %r object" %
                                 (name, self.__class__.__name__))

        super(VObject, self).__delattr__(name)

    def __eq__(self, other):
        """
        Compare two ``VObject`` objects to determine if they are
        equal.

        :param other: The other ``VObject`` object to compare to.

        :returns: ``True`` if the objects have the same class and
                  values, ``False`` otherwise.
        """

        # Always unequal if other isn't of the same class
        if self.__class__ is not other.__class__:
            return False

        return self.__vers_values__ == other.__vers_values__

    def __ne__(self, other):
        """
        Compare two ``VObject`` objects to determine if they are not
        equal.

        :param other: The other ``VObject`` object to compare to.

        :returns: ``False`` if the objects have the same class and
                  values, ``True`` otherwise.
        """

        # Always unequal if other isn't of the same class
        if self.__class__ is not other.__class__:
            return True

        return self.__vers_values__ != other.__vers_values__

    def __getstate__(self):
        """
        Retrieve a dictionary describing the value of the ``VObject``
        object.  This dictionary will have the values of all declared
        attributes, along with a ``__version__`` key set to the
        version of the ``VObject`` object.

        :returns: A dictionary of attribute values.
        """

        return self.__vers_values__.__getstate__()

    def __setstate__(self, state):
        """
        Reset the state of the object to reflect the values contained
        in the passed in ``state`` dictionary.

        :param state: The state dictionary.  All attribute values will
                      be passed through the appropriate validators.
                      Schema upgraders will be called to convert the
                      dictionary to the current version.
        """

        # Prohibit instantiating abstract versioned objects
        if not getattr(self, '__vers_schemas__', None):
            raise TypeError("cannot instantiate abstract versioned object "
                            "class %r" % self.__class__.__name__)

        target = schema = self.__vers_schemas__[-1]
        schema_vers = schema.__version__

        # First step, get the state version
        if '__version__' not in state:
            raise TypeError("schema version not available in state")
        version = state['__version__']
        if (not isinstance(version, (int, long)) or
                version < 1 or version > schema_vers):
            raise TypeError("invalid schema version %s in state" % version)

        # Now, start with the desired schema and build up a pipeline
        # of upgraders
        upgraders = []
        while version != schema_vers:
            # Find the upgrader that most closely matches the target
            # version
            for trial_vers in range(version, schema_vers):
                if trial_vers in schema.__vers_upgraders__:
                    # Add the upgrader we want
                    upgraders.append(schema.__vers_upgraders__[trial_vers])

                    # Now select the appropriate ancestor schema and
                    # update schema_vers
                    schema = self.__vers_schemas__[trial_vers - 1]
                    schema_vers = trial_vers

                    # We're done with the for loop, but not the while
                    break
            else:
                raise TypeError("missing upgrader for schema version %s" %
                                schema.__version__)

        # OK, we now have a pipeline of upgraders; call them in the
        # proper order
        for upgrader in reversed(upgraders):
            state = _call_upgrader(upgrader, state)

        # We now have an appropriate state; generate the Schema
        # object and set our state
        self.__vers_init__(target())
        self.__vers_values__.__setstate__(state)

    to_dict = __getstate__

    @classmethod
    def from_dict(cls, values):
        """
        Construct a ``VObject`` instance from a dictionary.

        :param values: The state dictionary.  All attribute values
                       will be passed through the appropriate
                       validators.  Schema upgraders will be called to
                       convert the dictionary to the current version.

        :returns: A new instance of the ``VObject`` subclass.
        """

        # Prohibit instantiating abstract versioned objects
        if not getattr(cls, '__vers_schemas__', None):
            raise TypeError("cannot instantiate abstract versioned object "
                            "class %r" % cls.__name__)

        # We have to construct a new instance of the class while
        # avoiding calling __init__(); this trick is borrowed from the
        # pure-Python pickle code
        obj = _EmptyClass()
        obj.__class__ = cls

        # Now we can just __setstate__()
        obj.__setstate__(values)

        return obj
