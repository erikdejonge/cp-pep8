# coding=utf-8
import os
import unittest


class CPTest(unittest.TestCase):

    def get_file(self, fname):
        """
        @type fname: str
        """
        os.system("cp ./test/" + fname + " .")

    def setUp(self):
        """
        setUp
        """
        self.testfile = "test.coffee"
        self.get_file(self.testfile)

    def rmfile(self, fname):
        """
        @type fname: str
        """
        os.system("rm " + fname)

    def tearDown(self):
        """
        tearDown
        """
        self.rmfile(self.testfile)

    def fexists(self, fname):
        """
        @type fname: str
        """
        e = os.path.exists(fname)
        self.assertTrue(e)
        return e

    def test_copy(self):
        """
        test_copy
        """
        fname = self.testfile
        self.fexists(fname)

    def test_cp(self):
        """
        test_cp
        """
        oldcode = open("test.coffee").read()
        os.system("python cp.py -f test.coffee")
        newcode = open("test.coffee").read()
        vcode = open("./test/test.result").read()
        self.assertNotEqual(oldcode, newcode)
        self.assertEqual(vcode, newcode)

    def test_some_files(self):
        """
        test_some_files
        """
        testfiles = ["app_basic.coffee", "controller_base.coffee", "services.coffee", "__init__.py"]

        for tf in testfiles:
            self.get_file(tf)
            print "tests.py:67", tf, self.fexists(tf)
            self.rmfile(tf)
