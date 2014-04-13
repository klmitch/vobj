=================
Versioned Objects
=================

A versioned object is a specialized data container, capable of
representing data when the schema for that data has gone through
several different revisions.  This may be useful when loading data
from a data store which may have older versions of the data, such as a
file or a database, or when communicating over the network with
servers implementing an older protocol version.

Declaring a Versioned Class
===========================

To declare a versioned class, create a class extending
``vobj.VObject``; then, declare one or more ``vobj.Schema`` classes
within that class, each containing ``vobj.Attribute`` instances,
i.e.::

    class Employee(vobj.VObject):
        class Version1(vobj.Schema):
	    __version__ = 1

	    first = vobj.Attribute()
	    last = vobj.Attribute()
	    salary = vobj.Attribute(0, validate=int)

To create a new object of this class, simply pass keyword arguments to
the constructor matching the declared attributes::

    >>> worker = Employee(first='Kevin', last='Mitchell', salary=15)

The data is available as attributes of the object::

    >>> worker.first
    'Kevin'
    >>> worker.salary
    15

The object may also be converted to and from a dictionary, using the
``to_dict()`` method and the ``from_dict()`` class method; these
dictionaries will contain a ``__version__`` key which indicates the
schema version.  When fed into ``from_dict()``, versioned objects are
able to upgrade data in older schema versions into the latest version.
Versioned objects also implement the pickle protocol, again embedding
the schema version to allow for later dynamic upgrades.

Attributes
----------

A schema of a versioned class contains attributes (instances of
``vobj.Attribute``), and can also contain properties.  Other
attributes are not available from instances of ``vobj.VObject`` (but
standard class attributes and methods *can* be declared on the
``vobj.VObject`` instance).  A ``vobj.Attribute`` instance can be
constructed with any of three optional parameters: the ``default``, a
``validate`` callable, and a ``getstate`` callable.

If the ``default`` is omitted, then a value for the attribute must be
provided when calling the versioned object constructor; otherwise,
that attribute will have exactly the default value if not provided.
(Take care with mutable values here; this acts similar to the defaults
of Python functions, in that accidentally updating a mutable default
will change the value for all instances of the versioned object.)

The ``validate`` callable can be used to validate that a value is of
the correct type.  It can also be used to transform a value into the
appropriate type, such as for the ``salary`` example above.  The
``validate`` callable should raise exceptions such as ``ValueError``
for invalid values, and return the desired value otherwise.  This
validation occurs at object construction time, when setting the value
of an attribute, and when deserializing an object, as with
``from_dict()``.

The ``getstate`` callable is used when serializing an attribute.  It
is passed the current value of the attribute, and must return a
serializable version.  For instance, the ``validate`` callable may be
used to translate an ID into an object; the ``getstate`` callable
would then be responsible for translating that object back into an ID
which can be transformed into a value on a dictionary.

Declaring New Versions
======================

Eventually, you will discover changes that need to be made to this
schema, such as the fact that some cultures do not use first or last
names.  To alter the schema for this, we'll create a new "name"
attribute and drop the "first" and "last" attributes.  We also need an
*upgrader* to convert values from the old schema to the new::

    class Employee(vobj.VObject):
        class Version1(vobj.Schema):
	    __version__ = 1

	    first = vobj.Attribute()
	    last = vobj.Attribute()
	    salary = vobj.Attribute(0, validate=int)

	class Version2(Version1):
	    # __version__ is automatically incremented here, but you
            # can set it explicitly

	    name = vobj.Attribute()

	    # salary is inherited, but so are first and last, so we
            # need to mask them...
	    first = None
	    last = None

	    # And we need an upgrader.  Note that every schema with
            # __version__ > 1 must provide an upgrader from the
            # previous version, like so...
	    @vobj.upgrader
	    def _upgrade_from_1_to_2(cls, state):
	        state['name'] = '%s %s' % (state['first'], state['last'])
		del state['first']
		del state['last']
		return state

When you have more than two versions, you may find that there's an
easier way to upgrade from version 1 to version 5 than calling each
upgrader in turn (the default way versioned objects handle this case).
A numerical argument to ``@vobj.upgrader`` indicates that the
decorated function upgrades from the designated version.  Note that,
when computing the chain of upgraders to use, a greedy algorithm is
employed; that is, in an example such as the following::

    class Employee(vobj.VObject):
        class Version1(vobj.Schema):
            __version__ = 1
            ...

        class Version2(Version1):
            ...

            @vobj.upgrader
            def _upgrade_1_2(cls, state):
                ...

        class Version3(Version2):
            ...

            @vobj.upgrader
            def _upgrade_2_3(cls, state):
                ...

        class Version4(Version3):
            ...

            @vobj.upgrader(2)
            def _upgrade_2_4(cls, state):
                ...

            @vobj.upgrader
            def _upgrade_3_4(cls, state):
                ...

        class Version5(Version4):
            ...

            @vobj.upgrader
            def _upgrade_4_5(cls, state):
                ...

Upgrading a version from 2 to 5 would call the upgraders
``_upgrade_2_4()`` and ``_upgrade_4_5()``, but if ``_upgrade_3_5()``
existed, the call order would be ``_upgrade_2_3()`` and
``_upgrade_3_5()``.

Finally, a note on the upgrader calling convention: upgrader methods
are implicitly *class* methods; they are passed a dictionary
containing the attributes for an earlier version, and must return a
dictionary containing the attributes for the version they're upgrading
to.  They are welcome to modify the dictionary in place or to create a
new dictionary, whichever seems more convenient, but the resulting
dictionary must contain only the keys recognized by the target
version.  Note that these dictionaries do *not* contain the
``__version__`` key mentioned above, and the returned dictionary
should *not* contain ``__version__``.

Accessing an Older Representation
=================================

For network protocols using versioned objects to serialize protocol
data units, or for API backwards compatibility, it is sometimes
necessary to be able to communicate with an older server that does not
use the latest version of the protocol.  For these instances, it is
possible to declare a *downgrader*::

    class Employee(vobj.VObject):
        class Version1(vobj.Schema):
            __version__ = 1

            first = vobj.Attribute()
            last = vobj.Attribute()
            salary = vobj.Attribute(0, validate=int)

        class Version2(Version1):
            name = vobj.Attribute()
            first = None
            last = None

            @vobj.upgrader
            def _upgrade_from_1_to_2(cls, state):
                state['name'] = '%s %s' % (state['first'], state['last'])
                del state['first']
                del state['last']
                return state

            # A downgrader to version 1; downgraders are optional, and
            # are never chained: that is, if version 3 was declared
            # with a downgrader to version 2, and the caller asks for
            # version 1, an error will be raised.
            @vobj.downgrader(1)
            def _downgrade_from_2_to_1(cls, state):
                first, _sep, last = state['name'].partition(' ')
                del state['name']
                state['first'] = first
                state['last'] = last
                return state

To access an older form of the object, simply index the
``__version__`` attribute of the object::

    emp = Employee(name='Kevin Mitchell', salary=100000)
    emp_v1 = emp.__version__[1]

The ``emp_v1`` object is read-only; it is not possible to modify the
values contained.  It is, however, kept up-to-date; that is, if we
were to modify the value of ``emp.name``, that new value would be
automatically reflected in the values of ``emp_v1.first`` and
``emp_v1.last``.  (Note that changes to mutable objects may *not* be
properly reflected; that is, if, e.g., an element is added to a list
in an attribute, that change may or may not be reflected in the older
version, depending on if the downgrader manipulates that value.)

Finally, a note on the downgrader calling convention: downgrader
methods, like upgrader methods, are implicitly *class* methods; they
are passed a dictionary, like an upgrader, and must return a
dictionary.  Like an upgrader, a downgrader may modify the dictionary
in place or create a new dictionary, and these dictionaries will not
(and should not) contain a ``__version__`` key.

A Note on Versions
------------------

The ``__version__`` attribute of a versioned object appears as an
integer value of the schema version represented, but in addition to
the indexing illustrated above, it also responds to ``len()`` (number
of versions that can be accessed), the ``in`` operator (indicating the
ability to represent the requested version), and it has an
``available()`` method, which returns a set of all the version numbers
which can be retrieved.  For our example above,
``len(emp.__version__)`` would be 2, ``1 in emp.__version__`` would be
``True``, and ``emp.__version__.available()`` would return the set
``set([1, 2])``.  The ``emp_v1.__version__`` attribute acts
identically, but compares numerically equal to 1.
