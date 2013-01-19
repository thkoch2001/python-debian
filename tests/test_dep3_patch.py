from __future__ import absolute_import

import sys
import unittest
import textwrap

sys.path.insert(0, '../lib/')

from debian import dep3_patch as dep3

class HeaderTest(unittest.TestCase):

    TESTPATCH = "\n".join(map(lambda x: x[8:], """\
        Bug: bug feld  
        Author: thomas
        author: koch
        from: somebody
        from: else
        last-updatE: now
             
        description: here is a description
         continued on the next line
        bug-ubuntu:ubuntu fehler
        bug-fedora:  fedora bug
        moredescrptio: with a colon
        subject: hello
        forwarded:
        ---
         
        from: should not come here
        """.splitlines()))

    def test_parse(self):
        header = dep3.Header.parse(self.TESTPATCH.splitlines())
        print header.fields
        self.assertEqual(header.get('bug'), "bug feld")
        self.assertEqual(header.get('last-update'), "now")
        self.assertEqual(header.get('description'), "here is a description\ncontinued on the next line\n"
                                                    "moredescrptio: with a colon")
        self.assertEqual(header.get('subject'), "hello")
        self.assertEqual(header.get('forwarded'), "")
        self.assertEqual(header.get('author')[0], "thomas")
        self.assertEqual(header.get('author')[1], "koch")
        self.assertEqual(header.get('from')[0], "somebody")
        self.assertEqual(header.get('from')[1], "else")
        self.assertEqual(header.get('vendor-bugs')["ubuntu"], "ubuntu fehler")
        self.assertEqual(header.get('vendor-bugs')["fedora"], "fedora bug")
        self.assertEqual(len(header.get('from')), 2)
        self.assertEqual(len(header.get('author')), 2)
        self.assertEqual(len(header.get('vendor-bugs')), 2)

