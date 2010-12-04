# =============================================================================
#
# EZID :: util.py
#
# Utility functions.
#
# Author:
#   Greg Janee <gjanee@ucop.edu>
#
# License:
#   Copyright (c) 2010, Regents of the University of California
#   http://creativecommons.org/licenses/BSD/
#
# -----------------------------------------------------------------------------

import re

_doiPattern = re.compile("10\.\d{4}/[!->@-~]+$")
def validateDoi (doi):
  """
  If the supplied string (e.g., "10.5060/foo") is a syntactically
  valid scheme-less DOI identifier, returns the canonical form of the
  identifier (namely, uppercased).  Otherwise, returns None.
  """
  # Our validation is generally more restrictive than what is allowed
  # by the DOI Handbook <doi:10.1000/186>, though not in any way that
  # should be limiting in practice.  The Handbook allows virtually any
  # prefix; we allow only four digits.  The Handbook allows all
  # printable Unicode characters in the suffix; we allow all graphic
  # ASCII characters except (?).  (Question marks are excluded to
  # eliminate any possible confusion over whether a dx.doi.org-style
  # "urlappend" argument is part of the identifier or not; our
  # position is that it is not.)  But our validation is also more
  # permissive in one aspect: we don't check that the suffix does
  # *not* match "./.*", which the Handbook claims is reserved (only in
  # the appendix, not in the main text, though).
  if _doiPattern.match(doi) and doi[-1] != "\n":
    return doi.upper()
  else:
    return None

_arkPattern1 = re.compile("((?:\d|b)\d{4}(?:\d{4})?/)([!-~]+)$")
_arkPattern2 = re.compile("([./])[./]+")
_arkPattern3 = re.compile("^[./]|[./]$")
_arkPattern4 = re.compile("%[0-9a-fA-F][0-9a-fA-F]|.")
_arkPattern5 = re.compile("[0-9a-zA-Z=#*+@_$]")
_arkPattern6 = re.compile("[0-9a-zA-Z=#*+@_$./]")

def _normalizeArkPercentEncoding (m):
  s = m.group(0)
  if len(s) == 3:
    c = chr(int(s[1:], 16))
    if _arkPattern5.match(c):
      return c
    else:
      return s.lower()
  else:
    assert s != "%", "malformed percent-encoding"
    if _arkPattern6.match(s):
      return s
    else:
      return "%%%02x" % ord(s)

def validateArk (ark):
  """
  If the supplied string (e.g., "13030/foo") is a syntactically valid
  scheme-less ARK identifier, returns the canonical form of the
  identifier.  Otherwise, returns None.
  """
  # Our validation diverges from the ARK specification
  # <http://wiki.ucop.edu/display/Curation/ARK> in that it is not as
  # restrictive: we allow all graphic ASCII characters; we place no
  # limit on length; we allow the first character to be a 'b'; and we
  # allow variant paths to be intermixed with component paths.  All
  # these relaxations are intended to support shadow ARKs and
  # relatively direct transformation of DOIs into shadow ARKs.  The
  # normalizations performed here follow the rules given in the
  # specification except that we don't re-order variant paths, which
  # would conflict with transformation of DOIs into shadow ARKs (since
  # order of period-delimited components in DOIs is significant).
  m = _arkPattern1.match(ark)
  if not m or ark[-1] == "\n": return None
  p = m.group(1)
  s = m.group(2)
  # Hyphens are insignificant.
  s = s.replace("-", "")
  # Consolidate adjacent structural characters.
  s = _arkPattern2.sub("\\1", s)
  # Eliminate leading and trailing structural characters.
  s = _arkPattern3.sub("", s)
  if len(s) == 0: return None
  # Normalize percent-encodings.
  try:
    s = _arkPattern4.sub(_normalizeArkPercentEncoding, s)
  except AssertionError:
    return None
  return p+s

def _percentEncodeCdr (m):
  s = m.group(0)
  return s[0] + "".join("%%%02x" % ord(c) for c in s[1:])

def doi2shadow (doi):
  """
  Given a scheme-less DOI identifier (e.g., "10.5060/FOO"), returns
  the corresponding scheme-less shadow ARK identifier (e.g.,
  "b5060/foo").  The returned identifier is in canonical form.  If the
  conversion cannot be performed, None is returned.  Note that the
  conversion is *not* in general reversible by shadow2doi.
  """
  # The conversion of DOIs to ARKs is a little tricky because ARKs
  # place semantics on certain characters in suffixes while DOIs do
  # not, and because ARKs use a restricted character set.  Our
  # conversion here is essentially direct mapping, on the assumption
  # that DOI identifiers will tend to more or less follow ARK
  # practices anyway.  Character conversion is handled by using
  # percent-encoding as specified in ARK normalization rules, but note
  # that we escape percent signs here because in DOIs percent signs do
  # *not* signify percent-encoding.  In addition, DOIs are lowercased
  # to match ARKs minted by noid, which are always lowercase (that is,
  # minted DOIs are formed from minted ARKs; to preserve the
  # programmatic conversion of DOIs to shadow ARKs for all DOIs, the
  # mapping to lowercase must be uniform).  It is possible for the
  # conversion to fail, but this should occur only in pathological
  # cases.
  # Update: to prevent different DOIs from mapping to the same shadow
  # ARK, we percent-encode characters (and only those characters) that
  # would otherwise be removed by the ARK normalization process.
  p = "b" + doi[3:8]
  s = doi[8:].replace("%", "%25").replace("-", "%2d").lower()
  s = _arkPattern3.sub(lambda c: "%%%02x" % ord(c.group(0)), s)
  s = _arkPattern2.sub(_percentEncodeCdr, s)
  a = validateArk(p + s)
  assert a != None, "shadow ARK failed validation"
  return a

def shadow2doi (ark):
  """
  Given a scheme-less shadow ARK identifier (e.g., "b5060/foo"),
  returns the corresponding scheme-less DOI identifier
  (e.g. "10.5060/FOO").  The returned identifier is in canonical form.
  This function is intended to be used for noid-minted ARK identifiers
  only; it is not in general the inverse of doi2shadow.
  """
  return ("10." + ark[1:]).upper()

def _encode (pattern, s):
  return pattern.sub(lambda c: "%%%02X" % ord(c.group(0)), s.encode("UTF-8"))

_pattern1 = re.compile("%|[^ -~]")
def encode1 (s):
  """
  UTF-8 encodes a Unicode string, then percent-encodes all non-graphic
  ASCII characters except space.  This form of encoding is used for
  log file exception strings.
  """
  return _encode(_pattern1, s)

_pattern2 = re.compile("%|[^!-~]")
def encode2 (s):
  """
  Like encode1, but percent-encodes spaces as well.  This form of
  encoding is used for log file record fields other than exception
  strings.
  """
  return _encode(_pattern2, s)

_pattern3 = re.compile("[%'\"]|[^!-~]")
def encode3 (s):
  """
  Like encode2, but percent-encodes (') and (") as well.  This form of
  encoding is used for noid arguments other than element names.
  """
  return _encode(_pattern3, s)

_pattern4 = re.compile("[%'\":]|[^!-~]")
def encode4 (s):
  """
  Like encode3, but percent-encodes (:) as well.  This form of
  encoding is used for noid element names.
  """
  return _encode(_pattern4, s)

class PercentDecodeError (Exception):
  pass

_decodePattern = re.compile("%([0-9a-fA-F][0-9a-fA-F])?")

def _decodeRewriter (m):
  if len(m.group(0)) == 3:
    return chr(int(m.group(0)[1:], 16))
  else:
    raise PercentDecodeError

def decode (s):
  """
  Decodes a string that was encoded by encode{1,2,3,4}.  Raises
  PercentDecodeError (defined in this module) and UnicodeDecodeError.
  """
  return _decodePattern.sub(_decodeRewriter, s).decode("UTF-8")
