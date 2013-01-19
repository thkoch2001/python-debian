import re
from itertools import imap, ifilter, islice, repeat
from operator import itemgetter

# TODO also filter git diffstat/numstat from header!

class Header(object):

    """Fields of a dep3 patch header.

    Fields containing a hyphen are translated to attributes with underscore, e.g.
    last_update instead of last-update.
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

    def __repr__(self):
        self.format()

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
        return "\n".join(repr)

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
                cls._parse_patch_handle_match(header, key, match.group("data") or "")

            # add continuation lines if the last parsed field was a continuation field
            elif continuation_field and " " == line[0]:
                header.set(continuation_field, header.get(continuation_field) + "\n" + line[1:].rstrip())
            else:
                header.set("description", str(header.get("description")) + "\n" + line)

        # TODO strip diffstat from description

        return header

    @classmethod
    def _parse_patch_handle_match(cls, header, key, data):
        """Adds the data for key to the Dep3PatchHeader instance.

        key must be lowercase
        """

        if key in cls.SINGLE_FIELDS_LIST:
            header.set(key, data)
        elif key in cls.MULTI_FIELDS_LIST:
            header.get(key).append(data)
        elif key.startswith("bug-"):
            header.get("vendor-bugs")[key[4:]] = data
        else:
            raise "should not happen: " + key

