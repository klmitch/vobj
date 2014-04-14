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

import six

from vobj import attribute


class SchemaMeta(type):
    """
    A metaclass for schemas.  A ``Schema`` subclass describes the
    recognized attributes and their defaults and validators.
    Properties, update methods, and regular methods are also
    recognized.
    """

    def __new__(mcs, name, bases, namespace):
        """
        Construct a new ``Schema`` subclass.

        :param name: The name of the ``Schema`` subclass.
        :param bases: A tuple of the base classes.
        :param namespace: A dictionary containing the namespace of the
                          class.

        :returns: The newly-constructed ``Schema`` subclass.
        """

        # Initialize the constructed data
        version = namespace.get('__version__')
        attrs = {}
        upgraders = {}
        downgraders = {}
        properties = set()

        # Sanity-check the __version__
        if (version is not None and
                (not isinstance(version, six.integer_types) or version < 1)):
            raise TypeError("Invalid value for __version__: %r" % version)

        # Inherit attributes from base classes; reverse order ensures
        # that an earlier base class overrides attributes from a later
        # base class
        for base in reversed(bases):
            attrs.update(getattr(base, '__vers_attrs__', {}))
            properties |= getattr(base, '__vers_properties__', set())

        # Inherit version from base classes if needed; we want the
        # first one found in the base classes
        if version is None:
            for base in bases:
                if hasattr(base, '__version__'):
                    tmp = base.__version__

                    # Prohibit inferring version from non-integer
                    # versions
                    if isinstance(tmp, six.integer_types):
                        version = tmp + 1
                        break

        # Explore the namespace and discover new attributes and
        # upgraders; we use list() to get a copy, since the namespace
        # is modified
        for key, value in list(namespace.items()):
            # Grab attributes first
            if value is None or isinstance(value, attribute.Attribute):
                # If value is None, make sure to remove it from attrs
                if value is None:
                    attrs.pop(key, None)
                else:
                    attrs[key] = value

                # Remove the attribute from the namespace, but only if
                # its not an inherited property; __getattr__ will
                # synthesize it later
                if key not in properties:
                    del namespace[key]

                # Also drop it from the properties list
                properties.discard(key)
            elif isinstance(value, property):
                # Keep a list of properties for the benefit of
                # __setattr__
                properties.add(key)
            elif hasattr(value, '__vers_upgrader__'):
                # Upgraders aren't permitted on abstract Schemas or
                # the version 1 schema
                if version is None:
                    raise TypeError("Upgraders prohibited on abstract schemas")
                elif version - 1 == 0:
                    raise TypeError("Cannot upgrade to version 1")

                # Determine the upgrader's version
                upgrade_version = value.__vers_upgrader__
                if upgrade_version is None:
                    upgrade_version = version - 1

                # Sanity-check that we aren't trying to "upgrade" from
                # a newer version
                if upgrade_version >= version:
                    raise TypeError("Cannot upgrade from a newer version")

                # Associate upgrader with the appropriate old version
                upgraders[upgrade_version] = key

                # Turn the upgrade method into a class method
                namespace[key] = classmethod(value)
            elif hasattr(value, '__vers_downgrader__'):
                # Downgraders aren't permitted on abstract Schemas or
                # the version 1 schema
                if version is None:
                    raise TypeError("Downgraders prohibited on "
                                    "abstract schemas")
                elif version - 1 == 0:
                    raise TypeError("Cannot downgrade from version 1")

                # Determine the downgrader's version
                downgrade_version = value.__vers_downgrader__

                # Sanity-check that we aren't trying to "downgrade" to
                # a newer version
                if downgrade_version >= version:
                    raise TypeError("Cannot downgrade to a newer version")

                # Associate downgrader with the appropriate old version
                downgraders[downgrade_version] = key

                # Turn the downgrade method into a class method
                namespace[key] = classmethod(value)

        # Make sure we have enough upgraders
        if (version is not None and version > 1 and
                version - 1 not in upgraders):
            raise TypeError("Schema requires an upgrader from version %d" %
                            (version - 1))

        # Add the extra data to the namespace
        namespace['__version__'] = version  # Have to shadow superclass value
        namespace['__vers_attrs__'] = attrs
        namespace['__vers_properties__'] = properties
        namespace['__vers_upgraders__'] = {}
        namespace['__vers_downgraders__'] = {}
        namespace['__vers_values__'] = None
        namespace['__vers_notify__'] = None

        # Construct the class
        cls = super(SchemaMeta, mcs).__new__(mcs, name, bases, namespace)

        # Now we have to add the upgraders; it has to wait until now,
        # because we want the bound method objects, which we can't get
        # until the class has been constructed
        for version, key in upgraders.items():
            cls.__vers_upgraders__[version] = getattr(cls, key)

        # Do the same construction for the downgraders...
        for version, key in downgraders.items():
            cls.__vers_downgraders__[version] = getattr(cls, key)

        return cls


@six.add_metaclass(SchemaMeta)
class Schema(object):
    """
    Describe a single version of a versioned object.  A ``Schema``
    describes all attributes, along with properties and methods
    (including upgrader methods).  Inheritance is respected.

    To declare an attribute, simply assign an instance of
    ``Attribute`` to the appropriate attribute.  To override an
    attribute inherited from an older schema, simply assign it the
    value ``None``.  Other attributes will be readable on the
    versioned object, but not writable.  Also note that only the
    attributes, properties, and methods of the most recent schema will
    be accessible via the versioned object.

    The ``Schema`` subclass has one required attribute: "__version__".
    This attribute must be set to a positive integer (greater than 0);
    if it is not set, the ``Schema`` subclass is considered abstract,
    and will not define an actual version of the object.  Note that
    "__version__" can be inherited from superclasses; its value will
    automatically be incremented by 1.

    Any ``Schema`` subclass with a "__version__" value greater than 1
    must define an "upgrader" method from the previous version.  The
    upgrader method is declared using the ``@upgrader`` decorator, and
    will be passed a dictionary of the values from the older version.
    The upgrader method must return another dictionary containing all
    the values required by the ``Schema`` subclass of which it is a
    member.  It is safe for the upgrader method to modify the
    dictionary in place, as long as it returns the modified
    dictionary.
    """

    def __new__(cls, values=None):
        """
        Construct a new instance of the ``Schema`` subclass.  Verifies
        that the ``Schema`` subclass is not abstract.  Raises a
        ``TypeError`` if it is.

        :param values: A dictionary of values.  If not provided, a
                       blank object is returned; the
                       ``__setstate__()`` method must be called on the
                       result before use.

        :returns: A newly constructed instance of the ``Schema``
                  subclass.
        """

        if getattr(cls, '__version__', None) is None:
            raise TypeError("cannot instantiate abstract schema class '%s'" %
                            cls.__name__)

        return super(Schema, cls).__new__(cls)

    def __init__(self, values=None):
        """
        Initializes a ``Schema`` object.

        :param values: A dictionary of values.  If not provided, a
                       blank object is returned; the
                       ``__setstate__()`` method must be called on the
                       result before use.
        """

        if values is None:
            # Initialization will be handled by __setstate__()
            return

        super(Schema, self).__setattr__('__vers_values__', {})

        for key, attr in self.__vers_attrs__.items():
            # Set up default value for the attribute
            if key not in values:
                if attr.default is attribute.unset:
                    raise TypeError("missing required argument '%s'" % key)
                self.__vers_values__[key] = attr.default

            # Validate the value from values
            else:
                self.__vers_values__[key] = attr.validate(values[key])

    def __contains__(self, key):
        """
        Check if a given key exists among the declared attributes or
        properties of the object.

        :param key: The name of the attribute or property.

        :returns: ``True`` if the key names a declared attribute or
                  property, or ``False`` otherwise.
        """

        return key in self.__vers_attrs__ or key in self.__vers_properties__

    def __getattr__(self, name):
        """
        Retrieve the value of a declared attribute.

        :param name: The name of the attribute.

        :returns: The value of the declared attribute.
        """

        # Be careful about uninitialized schemas
        if self.__vers_values__ is None:
            raise RuntimeError("'%s' is uninitialized" %
                               self.__class__.__name__)

        # Delegate to the values
        if name not in self.__vers_attrs__:
            raise AttributeError("'%s' object has no attribute '%s'" %
                                 (self.__class__.__name__, name))

        return self.__vers_values__[name]

    def __setattr__(self, name, value):
        """
        Sets the value of an attribute.

        :param name: The name of the attribute.
        :param value: The new value of the attribute.
        """

        # Be careful about uninitialized schemas
        if self.__vers_values__ is None:
            raise RuntimeError("'%s' is uninitialized" %
                               self.__class__.__name__)

        # Try sets into the values dictionary...
        if name in self.__vers_attrs__:
            value = self.__vers_attrs__[name].validate(value)
            self.__vers_values__[name] = value

            # Send a notification on update
            if self.__vers_notify__:
                self.__vers_notify__()
        else:
            super(Schema, self).__setattr__(name, value)

    def __delattr__(self, name):
        """
        Deletes an attribute.  This cannot be called on a declared
        attribute; if it is, an ``AttributeError`` will be raised.

        :param name: The name of the attribute.
        """

        # Be careful about uninitialized schemas
        if self.__vers_values__ is None:
            raise RuntimeError("'%s' is uninitialized" %
                               self.__class__.__name__)

        # Don't allow deletes of specially declared attributes
        if name in self.__vers_attrs__:
            raise AttributeError("cannot delete attribute '%s' of '%s' "
                                 "object" % (name, self.__class__.__name__))

        super(Schema, self).__delattr__(name)

    def __eq__(self, other):
        """
        Compare two ``Schema`` objects to determine if they are equal.

        :param other: The other ``Schema`` object to compare to.

        :returns: ``True`` if the objects have the same class and
                  values, ``False`` otherwise.
        """

        # Be careful about uninitialized schemas
        if self.__vers_values__ is None:
            raise RuntimeError("'%s' is uninitialized" %
                               self.__class__.__name__)

        # Always unequal if other isn't of the same class
        if self.__class__ is not other.__class__:
            return False

        return self.__vers_values__ == other.__vers_values__

    def __ne__(self, other):
        """
        Compare two ``Schema`` objects to determine if they are not
        equal.

        :param other: The other ``Schema`` object to compare to.

        :returns: ``False`` if the objects have the same class and
                  values, ``True`` otherwise.
        """

        # Be careful about uninitialized schemas
        if self.__vers_values__ is None:
            raise RuntimeError("'%s' is uninitialized" %
                               self.__class__.__name__)

        # Always unequal if other isn't of the same class
        if self.__class__ is not other.__class__:
            return True

        return self.__vers_values__ != other.__vers_values__

    def __getstate__(self):
        """
        Retrieve a dictionary describing the value of the ``Schema``
        object.  This dictionary will have the values of all declared
        attributes, along with a ``__version__`` key set to the
        version of the ``Schema`` object.

        :returns: A dictionary of attribute values.
        """

        # Be careful about uninitialized schemas
        if self.__vers_values__ is None:
            raise RuntimeError("'%s' is uninitialized" %
                               self.__class__.__name__)

        # Copy __vers_values__ and add the __version__ to it
        state = dict(__version__=self.__version__)
        for key, value in self.__vers_values__.items():
            attr = self.__vers_attrs__[key]
            state[key] = attr.getstate(value)

        return state

    def __setstate__(self, state):
        """
        Reset the state of the object to reflect the values contained
        in the passed in ``state`` dictionary.

        :param state: The ``state`` dictionary.  The version of the
                      dictionary (contained in the "__version__" key)
                      must match the version of the schema, and all
                      attribute values will be passed through the
                      appropriate validators.
        """

        # Make sure we're not abstract
        if getattr(self, '__version__', None) is None:
            raise TypeError("cannot instantiate abstract schema class '%s'" %
                            self.__class__.__name__)

        # Verify the version is valid
        if ('__version__' not in state or
                state['__version__'] != self.__version__):
            raise ValueError("version mismatch setting state; "
                             "version %r, expecting %s" %
                             (state.get('__version__'), self.__version__))

        # Set up the values dictionary
        values = {}

        # Walk through all the keys
        for key in set(state.keys()) | set(self.__vers_attrs__.keys()):
            if key == '__version__':
                continue
            elif key not in state:
                raise ValueError("missing attribute '%s'" % key)
            elif key not in self.__vers_attrs__:
                raise ValueError("unexpected attribute '%s'" % key)

            # Set up the value
            attr = self.__vers_attrs__[key]
            values[key] = attr.validate(state[key])

        # Now we know everything's all set, so set up __vers_values__
        super(Schema, self).__setattr__('__vers_values__', values)
