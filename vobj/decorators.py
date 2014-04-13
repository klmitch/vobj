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

import six


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

    :returns: If called with no arguments or with an integer version,
              returns a decorator.  If called with a callable, returns
              the callable.
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
    elif isinstance(version, six.integer_types):
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

    :returns: A decorator.
    """

    def decorator(func):
        # Save the version to downgrade to
        func.__vers_downgrader__ = version
        return func

    # Sanity-check the version number
    if not isinstance(version, six.integer_types) or version < 1:
        raise TypeError("Invalid downgrader version number %r" % version)

    return decorator
