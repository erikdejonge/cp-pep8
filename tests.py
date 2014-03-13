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
        #self.rmfile(self.testfile)

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

    def run_cp(self, fname):
        oldcode = open(fname).read()
        os.system("python cp.py -f " + fname)
        newcode = open(fname).read()
        return newcode, oldcode

    def test_cp(self):
        """
        test_cp
        """
        fname = self.testfile
        newcode, oldcode = self.run_cp(fname)
        vcode = open("./test/test.result").read()
        self.assertNotEqual(oldcode, newcode)
        self.assertEqual(vcode, newcode)

    def test_some_files(self):
        """
        test_some_files
        """
        testfiles = ["app_basic.coffee", "controller_base.coffee", "services.coffee", "couchdb_api.py"]

        for tf in testfiles:
            self.get_file(tf)
            oc, nc = self.run_cp(tf)
            self.assertEqual(oc, nc)
            self.rmfile(tf)
