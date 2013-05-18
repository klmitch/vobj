=================
Versioned Objects
=================

A versioned object is a specialized data container, capable of
representing data when the schema for that data has gone through
several different revisions.  This is useful when loading data from a
data store which may have older versions of the data, such as a file
or a database.

To declare a versioned class, create a class extending ``VObject``;
then, declare one or more ``Schema`` classes within that class, i.e.::

    class Employee(VObject):
        class Version1(Schema):
	    __version__ = 1

	    first = Attribute()
	    last = Attribute()
	    salary = Attribute(0, validate=int)

To create a new object of this class, simply pass keyword arguments to
the constructor matching the attributes::

    >>> worker = Employee(first='Kevin', last='Mitchell', salary=15)

The data is available as attributes of the object::

    >>> worker.first
    'Kevin'
    >>> worker.salary
    15

Eventually, you will discover changes that need to be made to this
schema, such as the fact that some cultures do not use first or last
names.  To alter the schema for this, we'll create a new "name"
attribute and drop the "first" and "last" attributes.  We also need an
*upgrader* to convert values from the old schema to the new::

    class Employee(VObject):
        class Version1(Schema):
	    __version__ = 1

	    first = Attribute()
	    last = Attribute()
	    salary = Attribute(0, validate=int)

	class Version2(Version1):
	    # __version__ is automatically incremented here, but you
            # can set it explicitly

	    name = Attribute()

	    # salary is inherited, but so are first and last, so we
            # need to mask them...
	    first = None
	    last = None

	    # And we need an upgrader...
	    @upgrader
	    def _upgrade_from_1(cls, state):
	        state['name'] = '%s %s' % (state['first'], state['last'])
		del state['first']
		del state['last']
		return state

Versioned objects implement the pickle protocol, so that they can be
pickled and unpickled.  The pickle protocol implementation allows
older versions of the object to be converted into the newer version.
It is also possible to convert versioned objects directly to and from
dictionaries, allowing any serialization mechanism to be used.
