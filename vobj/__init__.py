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

import inspect

from vobj.attribute import Attribute
from vobj.decorators import upgrader, downgrader
from vobj.schema import Schema

from vobj import converters
from vobj.version import SmartVersion


__all__ = ['Attribute', 'upgrader', 'downgrader', 'Schema', 'VObject']


class _EmptyClass(object):
    """
    An empty class.  This is used by ``VObject.from_dict()`` when
    constructing a ``VObject`` subclass from a dictionary.
    """

    pass


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
                (vers, converters.Converters(versions[vers], down))
                for vers, down in last_schema.__vers_downgraders__.items()
            )
        else:
            downgraders = {}

        # Now make our additions to the namespace
        namespace['__vers_schemas__'] = schemas
        namespace['__vers_downgraders__'] = downgraders
        namespace['__version__'] = SmartVersion(len(schemas), last_schema)

        return super(VObjectMeta, mcs).__new__(mcs, name, bases, namespace)


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
        upgraders = converters.Converters(target)
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
        # proper order and get our schema object
        values = upgraders(state.copy())

        # We now have an appropriate state; generate the Schema
        # object and set our state
        self.__vers_init__(values)

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
