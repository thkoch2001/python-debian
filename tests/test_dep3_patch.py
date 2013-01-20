from __future__ import absolute_import

import sys
import unittest
import textwrap
import itertools

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


    TESTPATCHFORMATED = "\n".join(map(lambda x: x[8:],"""\
        bug-fedora: fedora bug
        bug-ubuntu: ubuntu fehler
        from: somebody
        from: else
        description: here is a description
         continued on the next line
         moredescrptio: with a colon
        author: thomas
        author: koch
        last-update: now
        subject: hello
        bug: bug feld
        forwarded:
        """.splitlines()))

    def test_parse(self):
        header = dep3.Header.parse(self.TESTPATCH.splitlines())

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

    def test_format(self):
        header = dep3.Header.parse(self.TESTPATCH.splitlines())
        self.assertEqual(header.format(), self.TESTPATCHFORMATED)

    def test_filterfirstiter(self):
        testiter = itertools.izip(itertools.count(), [0, 1, 2, 1, 1, 2, 3, 3, 1])
        pred = lambda x: x[1]==3
        l = list(dep3._filterfirst(pred, testiter))

        self.assertEqual([(6,3)], l)

    def test_replace_first_in_list(self):
        testlist = list(range(5))
        found = dep3._replace_first_in_list(testlist, 2, "hi")
        self.assertTrue(found)
        self.assertEqual([0,1,"hi",3,4], testlist)

        found = dep3._replace_first_in_list(testlist, 6, "ho")
        self.assertFalse(found)
        self.assertEqual([0,1,"hi",3,4], testlist)

    def test_add_missing_info(self):
        header = dep3.Header()
        authorlist = header.get("author")
        authorlist += ["first", "second", "", "fourth", ""]

        header.add_missing_info(author="me", last_update="today")
        self.assertEqual(["first", "second", "me", "fourth", ""], authorlist)
        self.assertEqual("today", header.get("last-update"))

