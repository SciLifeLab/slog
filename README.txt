slog: simple lab tracking system
================================

Overview
--------

The basic architectural idea for the slog system is to build the LIMS
on a specific but modifiable ontology, i.e. a view of the types of
entities that exist in the lab world, and their relationships with
each other. The ontology (types of entities) is viewed as the primary
level of the LIMS, while the workflows (processes, methods) are seen
as the secondary level. 

We believe that this is the appropriate design choice for a lab
environment employing cutting-edge technology, which evolves
continuously. The lab entities are more fundamental and less subject
to change than workflows. The methods used in the lab typically evolve
more rapidly than the actual things (samples, projects, etc) the
methods are applied to.

As a consequence of this architectural decision, the entities and
their information can be entered in any order (subject to the
relationships defined as required). As the LIMS system matures,
workflows can be added that aid or control the input of data in a
specific order. This is viewed as a refinement of the LIMS system, not
a fundamental property. 

The technical architecture is based on entities whose data is stored
in a document database. This decision was based on the observation
that an entity is more naturally represented by a document in a
database than in a set of tables in a traditional RDBMS.

The properties of a traditional RDBMS require that the data for
any specific entity type be split up in a number of tables. As long as
all data items for an entity are singleton values (a float, a string,
etc), a single table with columns for the data items suffices. But as
soon as composite data structures (lists, sets, dictionaries) are
required for storing the information of an entity, multiple tables
involving foreign-key relationships must be used to store the data for
an entity. This creates complexity in the design, and fragility in the
evolution of the entity definitions.

A document database can be used to store all data for an entity in a
single document, where it is straightforward to represent composite
data structures.

Terminology
-----------

account 
    An entity type representing a user in the system, including
    customers.

action
    Brief description in a log entry of the modification for an entity.

admin
    Role value: Allowed to do anything.

customer
    Role value: Read-only of its own project and samples.

engineer
    Role value: Allowed to create and edit samples within a project.

manager
    Role value: Allowed to do add customers and projects.

name
    One-word name for an entity, alphabetical first character, the rest
    alphanumerical or underscore '_'. Must be unique within its entity type.

role
    Hard-coded level for access privilege.
    Possible values are: admin, manager, engineer, customer.

sample
    Specific material to be analyzed.

tag
    A simple name or phrase attached to an entity, for classification and
    for search purposes.

title
    A one-line description of an entity.
    May contain several words, be non-unique, or empty.

timestamp
    Date and time (ISO format) of the modification producing the current
    revision of the document.

tool
    A software component that operates on a sample, project, or other
    entity to change it, produce other entities, or to do something else.
    The available tools depend on the site.

user
    A person interacting with the system.
    All access to slog requires login to an existing account.

xref
    A cross reference from an entity to an external item. May be an explicit
    URL (http://...) or a URN (urn:database:key), which may be processed by
    the system into a clickable URL link.
