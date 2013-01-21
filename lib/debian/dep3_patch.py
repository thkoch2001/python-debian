import re
from itertools import imap, ifilter, islice, repeat, dropwhile
import itertools
from operator import itemgetter

# TODO also filter git diffstat/numstat from header!

class Header(object):

    """Fields of a dep3 patch header.

    This class does not intend to retain a patch header verbatim. It would be
    a huge effort to do so with little benefit. After a parse-format cycle the
    following will have changed:

    - Fields have a fixed order regardless of the original order.
    - The description field is always formatted as continuation field
      with one space indentation. It does parse but not generate unindented
      description lines.
    - Field names are formatted in lowercase regardless of the original case.

    The module does not support dpatch, only quilt.  The module does not use
    the deb822 module of python-debian because it is rather hard to
    understand, provides more than needed and might fail to parse unindented
    description lines.

    see: http://dep.debian.net/deps/dep3 for the DEP3 specification
    """

    # taken from quilt/scripts/patchfns.in
    PATCH_HEADER_SEP_REGEX = re.compile(r"^---\s*|(\*\*\*|Index:)[ \t][^ \t]|^diff -")

    SINGLE_FIELDS = "origin|last-update|subject|description|forwarded"\
        "|applied-upstream|bug"
    MULTI_FIELDS = "author|from|reviewed-by|acked-by"
    VALID_FIELDS_PATTERN = SINGLE_FIELDS + "|" + MULTI_FIELDS + "|" r"bug-\S+"

    SINGLE_FIELDS_LIST = SINGLE_FIELDS.split("|")
    MULTI_FIELDS_LIST  = MULTI_FIELDS.split("|")

    FIELD_LINE_REGEX = re.compile(
        r"^(?P<key>" + VALID_FIELDS_PATTERN + r")\s*:\s*"
        + r"(?P<data>\S.*?)?\s*$",
        re.IGNORECASE )

    CONTINUATION_FIELDS = ("description")

    def __init__(self):

        fields = {}

        for field in self.SINGLE_FIELDS_LIST:
            fields[field] = None

        for field in self.MULTI_FIELDS_LIST:
            fields[field] = []

        fields['vendor-bugs'] = {}
        self.fields = fields

    def get(self, name):
        """Returns the value of a header field, taking care of hyphen/underscore translation."""
        return self.fields[name]

    def set(self, name, value):
        """Sets the value of a header field, taking care of hyphen/underscore translation."""
        self.fields[name] = value

    def append(self, name, item):
        """Appends item to the list of a multivalue field (from, author, reviewed-by, acked-by)."""
        self.fields[name].append(item)

    def _setdata(self, key, data):
        """Adds the data for key either appending to a list or setting for singe values."""
        if key in self.SINGLE_FIELDS_LIST:
            self.set(key, data)
        elif key in self.MULTI_FIELDS_LIST:
            self.append(key, data)
        elif key.startswith("bug-"):
            self.get("vendor-bugs")[key[4:]] = data
        else:
            raise "should not happen: " + key

    def __repr__(self):
        self.format()

    def add_missing_info(self, author, last_update):

        """Adds author and last-update info to the fields in case it's missing.

        If the last-update field is already set, it will not be overwritten.
        The author info is only added if there is an empty from or author field.
        """

        if not self.get("last-update"):
            self.set("last-update", last_update)

        for field in ['author', 'from']:
            targetlist = self.get(field)
            found = _replace_first_in_list(targetlist, "", author)
            if found:
                break

    def format(self):
        """Returns a dep3 conforming representation of this patch header."""
        repr = []

        emptyfilter = lambda x: not x[1] in (None, {}, [])
        formatter = lambda k,v: ("%s: %s" % (k,v)).strip()

        for field, value in ifilter(emptyfilter, self.fields.iteritems()):
            if "description" == field:
                lines = value.splitlines()
                repr.append("description: %s" % lines[0])
                repr.extend(imap(lambda x: " "+x, islice(lines, 1, None)))
            elif field in self.SINGLE_FIELDS_LIST:
                repr.append(formatter(field, value))
            elif field in self.MULTI_FIELDS_LIST:
                repr += imap(formatter, repeat(field), value)
            elif "vendor-bugs" == field:
                repr += imap(lambda x: "bug-%s: %s" % x, value.iteritems())
        return "\n".join(repr) + "\n"

    @classmethod
    def parse(cls, lines):
        """Returns a Header instance parsed from the lines iterator.

        After this function returns the iterator can still be used to read the patch from it.
        """
        header = cls()

        # Set to the name of a currently parsed continuation field (only Description actually)
        continuation_field = None

        for line in lines:
            if cls.PATCH_HEADER_SEP_REGEX.match(line):
                break

            match = cls.FIELD_LINE_REGEX.match(line)
            if match:
                key = match.group("key").lower()
                continuation_field = key if key in cls.CONTINUATION_FIELDS else None
                header._setdata(key, match.group("data") or "")

            # add continuation lines if the last parsed field was a continuation field
            elif continuation_field and " " == line[0]:
                header.set(continuation_field, header.get(continuation_field) + "\n" + line[1:].rstrip())
            else:
                header.set("description", str(header.get("description")) + "\n" + line)

        # TODO strip diffstat from description

        return header

# iterator returning only the first item for which pred evaluates to true
_filterfirst = lambda pred, it: islice(dropwhile(lambda x: not pred(x), it), 1)

def _replace_first_in_list(targetlist, searched, replacement):
    found = next(_filterfirst(lambda x: x[1]==searched, itertools.izip(itertools.count(), targetlist)), None)
    if found:
        targetlist[found[0]] = replacement
    return bool(found)
