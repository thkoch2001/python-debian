import re
from itertools import imap, ifilter, islice, repeat
from operator import itemgetter

# TODO also filter git diffstat/numstat from header!

class Dep3PatchHeader(object):

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

    __slots__ = map(lambda x: x.replace("-", "_"), MULTI_FIELDS_LIST + SINGLE_FIELDS_LIST + [ 'vendor_bugs' ])

    def __init__(self):
        for field in type(self).SINGLE_FIELDS_LIST:
            self.set(field, None)

        for field in type(self).MULTI_FIELDS_LIST:
            self.set(field, [])

        self.vendor_bugs = {}

    def get(self, name):
        return getattr(self, name.replace("-", "_", 1))

    def set(self, name, value):
        setattr(self, name.replace("-", "_", 1), value)

    def __repr__(self):
        repr = []
        for slot in Dep3PatchHeader.__slots__:
            repr.append("%s: %s" % (slot, getattr(header, slot)))
        return "\n".join(repr)

    def format(self):
        repr = []
        keyvalue = imap(lambda x: (x, getattr(self, x)), self.__slots__)
        filtered = ifilter(itemgetter(1), keyvalue)
        formatter = lambda k,v: ("%s: %s" % (k,v)).strip()

        for field, value in filtered:
            if "description" == field:
                lines = value.splitlines()
                repr.append("description: %s" % lines[0])
                repr.extend(imap(lambda x: " "+x, islice(lines, 1, None)))
            elif field in self.SINGLE_FIELDS_LIST:
                repr.append(formatter(field, value))
            elif field in self.MULTI_FIELDS_LIST:
                repr += imap(formatter, repeat(field), value)
            elif "vendor_bugs" == field:
                repr += imap(lambda x: "bug-%s: %s" % x, value.iteritems())
        return "\n".join(repr)

    @classmethod
    def parse_patch(cls, lines):

        header = Dep3PatchHeader()

        # Set to the name of a currently parsed continuation field (only Description actually)
        continuation_field = None

        for line in lines:
            if cls.PATCH_HEADER_SEP_REGEX.match(line):
                break

            match = cls.FIELD_LINE_REGEX.match(line)
            if match:
                key = match.group("key").lower()
                continuation_field = key if key in cls.CONTINUATION_FIELDS else None
                cls._parse_patch_handle_match(header, key, match.group("data") or " ")

            # add continuation lines if the last parsed field was a continuation field
            elif continuation_field and " " == line[0]:
                header.set(continuation_field, header.get(continuation_field) + "\n" + line[1:].rstrip())
            else:
                header.description = str(header.description) + "\n" + line

        # TODO strip diffstat from description

        return header

    @classmethod
    def _parse_patch_handle_match(cls, header, key, data):
        """adds the data for key to the Dep3PatchHeader instance

        key must be lowercase
        """

        if key in cls.SINGLE_FIELDS_LIST:
            header.set(key, data)
        elif key in cls.MULTI_FIELDS_LIST:
            header.get(key).append(data)
        elif key.startswith("bug-"):
            header.vendor_bugs[key[4:]] = data
        else:
            raise "should not happen: " + key

if __name__ == '__main__':
    test = """Bug: bug feld  
Author: thomas
author: koch
from: somebody
from: else
last-updatEd: now
    
description: here is a description
 continued on the next line
bug-ubuntu:ubuntu fehler
bug-fedora:fedora bug
moredescrptio: with a colon
subject: hello
forwarded:
---

from: should not come here
    """

    header = Dep3PatchHeader.parse_patch(test.splitlines())
    print(header.description)
    print(header)
    print("----------------------------")
    print(header.format())
