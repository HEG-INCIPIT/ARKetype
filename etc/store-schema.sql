-- ============================================================================
--
-- Store database schema.  The store database serves as a backup for
-- the primary "bind" noid database.  It also supports identifier
-- harvesting.
--
-- The 'identifier' table stores all identifiers and associated
-- metadata.  As in noid, identifier records are keyed by the
-- identifiers themselves (in the case of ARKs) or by the identifiers'
-- shadow ARKs (otherwise); identifiers are stored in scheme-less,
-- normalized form (e.g., "13030/foo").  Identifier owners are stored
-- as qualified, normalized ARK identifiers (e.g.,
-- "ark:/99166/p92z12p14").  For index efficiency the 'ownerMapping'
-- table maps identifier owners to local integer keys.  The metadata
-- for an identifier is stored as a single line of text that has been
-- UTF-8 encoded and then gzipped.  The line uses the space-separated
-- format
--
--    label value label value ...
--
-- where field labels and values are encoded as they are in noid
-- (util.encode4 for labels and util.encode3 for values).  Note that
-- empty values will result in adjacent spaces in the line.
--
-- Author:
--   Greg Janee <gjanee@ucop.edu>
--
-- License:
--   Copyright (c) 2013, Regents of the University of California
--   http://creativecommons.org/licenses/BSD/
--
-- ----------------------------------------------------------------------------

CREATE TABLE ownerMapping (
  ownerKey INTEGER NOT NULL PRIMARY KEY,
  owner TEXT NOT NULL UNIQUE
);

CREATE TABLE identifier (
  identifier TEXT NOT NULL PRIMARY KEY,
  ownerKey INTEGER NOT NULL REFERENCES ownerMapping,
  metadata BLOB NOT NULL
);

CREATE INDEX identifierOwnerIndex ON identifier (ownerKey, identifier ASC);