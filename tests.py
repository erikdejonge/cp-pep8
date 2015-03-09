from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import open
from future import standard_library
standard_library.install_aliases()
from builtins import range
# coding=utf-8
import os
import unittest


class CPTest(unittest.TestCase):
    """
    CPTest
    """

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

    def run_cp(self, fname):
        """
        @type fname: str
        @type cp: str
        """
        oldcode = open(fname).read()
        cmd = "python cp.py -f " + fname
        os.system(cmd)
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
        testfiles = ["app_basic.coffee", "controller_base.coffee", "services.coffee", "crypto_data.py"]

        for tf in testfiles:
            self.get_file(tf)
            oc, nc = self.run_cp(tf)

            if not oc == nc:
                print("tests.py:83", tf)

            self.assertEqual(oc, nc)
            self.rmfile(tf)

    def test_directory(self):
        """
        test_directory
        """
        os.system("rm -Rf ./crypto_api")
        os.system("cp -r ./test/crypto_api .")
        os.system("cp cp.py ./crypto_api")
        fname = "./crypto_api/__init__.py"
        oc = open(fname).read()

        for i in range(0, 3):
            cmd = "cd crypto_api; python cp.py -f __init__.py"
            os.system(cmd)
            nc = open(fname).read()
            self.assertEqual(oc, nc)

        os.system("rm -Rf ./crypto_api")
