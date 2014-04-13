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


class SchemaProxy(object):
    """
    Base class for schema proxies.  A schema proxy proxies to an
    instantiated schema object, allowing access to the schema's
    attributes.
    """

    def __getattr__(self, name):
        """
        Retrieve the value of a declared attribute.

        :param name: The name of the attribute.

        :returns: The value of the declared attribute.
        """

        # Proxy to the Schema object stored in __vers_values__; this
        # covers not just the data attributes, but also any methods or
        # descriptors.
        return getattr(self.__vers_values__, name)

    def __delattr__(self, name):
        """
        Deletes an attribute.  This cannot be called on a declared
        attribute; if it is, an ``AttributeError`` will be raised.

        :param name: The name of the attribute.
        """

        # Don't allow deletes of specially declared attributes
        if name in self.__vers_values__:
            raise AttributeError("type object '%s' attribute '%s' cannot "
                                 "be deleted" %
                                 (self.__class__.__name__, name))

        super(SchemaProxy, self).__delattr__(name)

    def __eq__(self, other):
        """
        Compare two ``SchemaProxy`` objects to determine if they are
        equal.

        :param other: The other ``SchemaProxy`` object to compare to.

        :returns: ``True`` if the objects have the same values,
                  ``False`` otherwise.
        """

        return self.__vers_values__ == other.__vers_values__

    def __ne__(self, other):
        """
        Compare two ``SchemaProxy`` objects to determine if they are
        not equal.

        :param other: The other ``SchemaProxy`` object to compare to.

        :returns: ``False`` if the objects have the same values,
                  ``True`` otherwise.
        """

        return self.__vers_values__ != other.__vers_values__

    def __getstate__(self):
        """
        Retrieve a dictionary describing the value of the
        ``SchemaProxy`` object.  This dictionary will have the values
        of all declared attributes, along with a ``__version__`` key
        set to the version of the ``SchemaProxy`` object.

        :returns: A dictionary of attribute values.
        """

        return self.__vers_values__.__getstate__()

    to_dict = __getstate__

    def __vers_set_values__(self, values):
        """
        Convenience method for setting the ``__vers_values__``
        and ``__version__`` attributes.

        :param values: The value to set the ``__vers_values__``
                       attribute to.
        """

        super(SchemaProxy, self).__setattr__('__vers_values__', values)


class ReadOnlyLazySchemaProxy(SchemaProxy):
    """
    A read-only, lazy resolving schema proxy.  A schema proxy proxies
    to an instantiated schema object, allowing access to the schema's
    attributes.  This variation prohibits writing to the schema
    object's attributes, and relies on a schema object defined in the
    master object.
    """

    def __init__(self, version):
        """
        Initialize a ``ReadOnlyLazySchemaProxy`` object.

        :param version: The version the proxy is for.
        """

        # Set up our special attributes
        super(ReadOnlyLazySchemaProxy, self).__setattr__(
            '__version__', version)
        super(ReadOnlyLazySchemaProxy, self).__setattr__(
            '__vers_master__', version._master)

    def __setattr__(self, name, value):
        """
        Sets the value of an attribute or property.  Values on the
        underlying Schema object will be rejected, as this is a
        read-only proxy.

        :param name: The name of the attribute.
        :param value: The new value of the attribute.
        """

        # If it's in the Schema object, reject the set
        if name in self.__vers_values__:
            raise AttributeError("type object '%s' attribute '%s' is "
                                 "read only" %
                                 (self.__class__.__name__, name))
        else:
            super(ReadOnlyLazySchemaProxy, self).__setattr__(name, value)

    @property
    def __vers_values__(self):
        """
        Retrieve the schema object from the master.
        """

        return self.__vers_master__.__vers_cache_get__(int(self.__version__))
