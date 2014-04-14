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

import inspect

import six

from vobj import converters
from vobj import proxy
from vobj import schema
from vobj import version


class EmptyClass(object):
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
        for key, value in list(namespace.items()):
            # If value isn't a Schema, or if it's an abstract Schema,
            # skip it
            if (not inspect.isclass(value) or
                    not issubclass(value, schema.Schema) or
                    getattr(value, '__version__', None) is None):
                continue

            # Make sure we don't have a multiply-defined schema
            # version
            if value.__version__ in versions:
                raise TypeError("Version %s defined by schemas '%s' "
                                "and '%s'" %
                                (value.__version__,
                                 versions[value.__version__].__name__, key))

            versions[value.__version__] = value

        # Make sure there are no gaps
        if set(versions.keys()) != set(range(1, len(versions) + 1)):
            raise TypeError("Gaps are present in the schema versions")

        # Condense versions into a list
        schemas = [v for k, v in sorted(versions.items(), key=lambda x: x[0])]
        last_schema = schemas[-1] if schemas else None

        # Set up downgraders and upgraders
        if last_schema:
            downgraders = dict(
                (vers, converters.Converters(versions[vers], down))
                for vers, down in last_schema.__vers_downgraders__.items()
            )
            upgraders = {
                len(schemas): converters.Converters(schemas[-1]),
            }
        else:
            downgraders = {}
            upgraders = {}

        # Now make our additions to the namespace
        namespace['__vers_schemas__'] = schemas
        namespace['__vers_downgraders__'] = downgraders
        namespace['__vers_upgraders__'] = upgraders
        namespace['__version__'] = version.SmartVersion(len(schemas),
                                                        last_schema)

        return super(VObjectMeta, mcs).__new__(mcs, name, bases, namespace)


@six.add_metaclass(VObjectMeta)
class VObject(proxy.SchemaProxy):
    """
    Describe a versioned object.  A ``VObject`` subclass describes all
    recognized versions of the object, through ``Schema`` subclasses
    defined as part of the ``VObject`` subclass.  Versioned objects
    can be safely pickled and unpickled; the ``Schema`` update methods
    make it possible to unpickle an older version of the object
    safely.  Versioned objects can also be converted to and from raw
    dictionaries using the ``to_dict()`` and ``from_dict()`` methods.
    """

    @classmethod
    def __vers_upgrader_get__(cls, vers):
        """
        Look up the ``vobj.converters.Converters`` instance needed to
        convert states from the given version to the latest version
        for this ``VObject``.

        :param vers: The version of the state for which a converter is
                     needed.

        :returns: An instance of ``vobj.converters.Converters``.
        """

        # Do we need to generate the converter?
        if vers not in cls.__vers_upgraders__:
            # Initialize loop variables
            sch = cls.__vers_schemas__[-1]
            sch_vers = sch.__version__

            # Initialize a landing pad
            cvt = converters.Converters(sch)

            # Use a greedy algorithm to compute the chain of schema
            # upgraders
            while vers != sch_vers:
                # Find the upgrader that most closely matches the
                # target version
                for trial_vers in range(vers, sch_vers):
                    if trial_vers in sch.__vers_upgraders__:
                        # Add the upgrader to the converter
                        cvt.append(sch.__vers_upgraders__[trial_vers])

                        # Select the appropriate ancestor schema and
                        # update sch_vers
                        sch = cls.__vers_schemas__[trial_vers - 1]
                        sch_vers = trial_vers

                        # We're done with the for loop, but not the
                        # while
                        break
                else:
                    # Shouldn't happen
                    raise TypeError("missing upgrader for schema version %s" %
                                    sch.__version__)

            # OK, save the converter set into the cache
            cls.__vers_upgraders__[vers] = cvt

        return cls.__vers_upgraders__[vers]

    def __new__(cls, **kwargs):
        """
        Construct a new instance of the ``VObject`` subclass.
        Verifies that the ``VObject`` subclass is not abstract (has at
        least one schema defined).  Raises a ``TypeError`` if it is
        abstract.

        :returns: A newly constructed instance of the ``VObject``
                  subclass.
        """

        # Prohibit instantiating abstract versioned objects
        if not getattr(cls, '__vers_schemas__', None):
            raise TypeError("cannot instantiate abstract versioned object "
                            "class '%s'" % cls.__name__)

        return super(VObject, cls).__new__(cls)

    def __init__(self, **kwargs):
        """
        Initialize a ``VObject`` instance.  The keyword arguments
        specify the values of declared attributes.  If an attribute is
        left out, the declared default (if any) will be used.  If no
        default was declared, a ``TypeError`` will be raised.
        """

        # Construct the Schema instance and set up __vers_values__
        values = self.__vers_schemas__[-1](kwargs)
        values.__vers_notify__ = self.__vers_cache_invalidate__
        self.__vers_set_values__(values)

        # Set up the smart version field
        vers = version.SmartVersion(
            int(self.__version__), self.__vers_schemas__[-1], self)
        super(VObject, self).__setattr__('__version__', vers)

        # Also need to set up the downgrade cache
        self.__vers_cache_invalidate__()
        super(VObject, self).__setattr__('__vers_proxies__', {})

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

    def __vers_accessor__(self, vers):
        """
        Retrieve a proxy for the given version.

        :param vers: The integer version to generate a proxy for.

        :returns: A read-only, lazy translating proxy for the given
                  version.
        """

        # Do we need to generate it?
        if vers not in self.__vers_proxies__:
            smart_version = version.SmartVersion(
                vers, self.__vers_schemas__[vers - 1], self)
            self.__vers_proxies__[vers] = proxy.ReadOnlyLazySchemaProxy(
                smart_version)

        return self.__vers_proxies__[vers]

    def __vers_cache_get__(self, vers):
        """
        Retrieve the schema object for the given version.

        :param vers: The integer version to generate the schema
                        object for.

        :returns: A schema object for the given version.
        """

        # Do we need to generate it?
        if vers not in self.__vers_cache__:
            sch_obj = self.__vers_downgraders__[vers](self.__getstate__())
            self.__vers_cache__[vers] = sch_obj

        return self.__vers_cache__[vers]

    def __vers_cache_invalidate__(self):
        """
        Invalidate the version cache.
        """

        # Just clear the cache; the proxy will invoke a regeneration
        # if need be
        super(VObject, self).__setattr__('__vers_cache__', {})

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
                            "class '%s'" % self.__class__.__name__)

        # First step, get the state version
        if '__version__' not in state:
            raise TypeError("schema version not available in state")
        vers = state['__version__']

        # Next, sanity-check the version
        max_vers = self.__vers_schemas__[-1].__version__
        if (not isinstance(vers, six.integer_types) or
                vers < 1 or vers > max_vers):
            raise TypeError("invalid schema version %r in state" % vers)

        # Now, get the upgraders
        upgraders = self.__vers_upgrader_get__(vers)

        # OK, we now have a pipeline of upgraders; call them in the
        # proper order and get our schema object
        values = upgraders(state.copy())
        values.__vers_notify__ = self.__vers_cache_invalidate__

        # Set the values
        self.__vers_set_values__(values)

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
                            "class '%s'" % cls.__name__)

        # We have to construct a new instance of the class while
        # avoiding calling __init__(); this trick is borrowed from the
        # pure-Python pickle code
        obj = EmptyClass()
        obj.__class__ = cls

        # Now we can just __setstate__()
        obj.__setstate__(values)

        return obj
