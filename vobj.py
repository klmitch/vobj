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


__all__ = ['Attribute', 'upgrader', 'Schema', 'VObject']


# Used to distinguish an unset default from any other value
_unset = object()


class Attribute(object):
    """
    Describe an attribute.
    """

    def __init__(self, default=_unset, validate=lambda x: x):
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
        """

        self.default = default
        self.validate = validate


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
        properties = set()

        # Inherit attributes and version from base classes
        for base in reversed(bases):
            attrs.update(getattr(base, '__vers_attrs__', {}))
            properties |= getattr(base, '__vers_properties__', set())

            if version is None and hasattr(base, '__version__'):
                tmp = base.__version__

                # Prohibit inferring version from non-integer versions
                if isinstance(tmp, (int, long)):
                    version = tmp + 1

        # Sanity-check the __version__
        if (version is not None and
                (not isinstance(version, (int, long)) or version < 1)):
            raise TypeError("Invalid value for __version__: %r" % version)

        # Explore the namespace and discover new attributes and
        # upgraders
        for key, value in namespace.items():
            # Grab attributes first
            if value is None or isinstance(value, Attribute):
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
                    raise TypeError("Cannot update to version 1")

                # Determine the upgrader's version
                update_version = value.__vers_upgrader__
                if update_version is None:
                    update_version = version - 1

                # Sanity-check that we aren't trying to "update" from
                # a newer version
                if update_version >= version:
                    raise TypeError("Cannot update from a newer version")

                # Associate upgrader with the appropriate old version
                upgraders[update_version] = key

                # Turn the update method into a class method
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
        namespace['__vers_values__'] = None

        # Construct the class
        cls = super(SchemaMeta, mcs).__new__(mcs, name, bases, namespace)

        # Now we have to add the upgraders; it has to wait until now,
        # because we want the bound method objects, which we can't get
        # until the class has been constructed
        if upgraders:
            for version, key in upgraders.items():
                cls.__vers_upgraders__[version] = getattr(cls, key)

        return cls


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

    __metaclass__ = SchemaMeta

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
            raise TypeError("cannot instantiate abstract schema class %r" %
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
                if attr.default is _unset:
                    raise TypeError("missing required argument %r" % key)
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
            raise RuntimeError("%r is uninitialized" % self.__class__.__name__)

        # Delegate to the values
        if name not in self.__vers_attrs__:
            raise AttributeError("%r object has no attribute %r" %
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
            raise RuntimeError("%r is uninitialized" % self.__class__.__name__)

        # Try sets into the values dictionary...
        if name in self.__vers_attrs__:
            value = self.__vers_attrs__[name].validate(value)
            self.__vers_values__[name] = value
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
            raise RuntimeError("%r is uninitialized" % self.__class__.__name__)

        # Don't allow deletes of specially declared attributes
        if name in self.__vers_attrs__:
            raise AttributeError("cannot delete attribute %r of %r object" %
                                 (name, self.__class__.__name__))

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
            raise RuntimeError("%r is uninitialized" % self.__class__.__name__)

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
            raise RuntimeError("%r is uninitialized" % self.__class__.__name__)

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
            raise RuntimeError("%r is uninitialized" % self.__class__.__name__)

        # Copy __vers_values__ and add the __version__ to it
        state = self.__vers_values__.copy()
        state['__version__'] = self.__version__

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
            raise TypeError("cannot instantiate abstract schema class %r" %
                            self.__class__.__name__)

        # Verify the version is valid
        if ('__version__' not in state or
                state['__version__'] != self.__version__):
            raise ValueError("version mismatch setting state; "
                             "version %s, expecting %s" %
                             (state.get('__version__'), self.__version__))

        # Set up the values dictionary
        values = {}

        # Walk through all the keys
        for key in set(state.keys()) | set(self.__vers_attrs__.keys()):
            if key == '__version__':
                continue
            elif key not in state:
                raise ValueError("missing attribute %r" % key)
            elif key not in self.__vers_attrs__:
                raise ValueError("unexpected attribute %r" % key)

            # Set up the value
            attr = self.__vers_attrs__[key]
            values[key] = attr.validate(state[key])

        # Now we know everything's all set, so set up __vers_values__
        super(Schema, self).__setattr__('__vers_values__', values)


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

        # Condense versions into a list and store it in the namespace
        schemas = [v for k, v in sorted(versions.items(), key=lambda x: x[0])]
        namespace['__vers_schemas__'] = schemas
        namespace['__version__'] = len(schemas)

        return super(VObjectMeta, mcs).__new__(mcs, name, bases, namespace)


class _EmptyClass(object):
    """
    An empty class.  This is used by ``VObject.from_dict()`` when
    constructing a ``VObject`` subclass from a dictionary.
    """

    pass


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
        super(VObject, self).__setattr__('__vers_values__', values)

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
        if version < 1 or version > schema_vers:
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
        super(VObject, self).__setattr__('__vers_values__', target())
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
