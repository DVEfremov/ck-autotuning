#
# Collective Knowledge
#
# See CK LICENSE.txt for licensing details
# See CK COPYRIGHT.txt for copyright details
#

import unittest
import sys
import os
import shutil

ck=None           # Will be updated by CK (initialized CK kernel)
test_util=None    # Will be updated by CK (initialized CK test utils)
o=None            # Will be updated by CK (initialized CK test utils)

# Contains new ck-autotuning program tests. Add new tests here!
class TestProgram(unittest.TestCase):

    # ck compile program:cbench-automotive-susan
    def test_compile_origin(self):
        # Try to compile program
        r=ck.access({'action':'compile',
                     'module_uoa':'program',
                     'data_uoa':'cbench-automotive-susan',
                     'out':o})
        if r['return']>0:
            print r
        self.assertEqual(0, r['return']);

    # ck run program:cbench-automotive-susan
    def test_run(self):
        with test_util.tmp_sys('0\n0\n0\n'):
            # Try to run program
            r=ck.access({'action':'run',
                         'module_uoa':'program',
                         'data_uoa':'cbench-automotive-susan',
                         'out':o})
            if r['return']>0:
                print r
            self.assertEqual(0, r['return']);

    # todo: ck autotune program:cbench-automotive-susan
    # it takes more than 5 minutes so it's disabled now because tests run on every commit
    # def test_autotune(self):
    #     with test_util.tmp_sys('0\n0\n0\n0\n0\n'):
    #         r=ck.access({'action':'autotune',
    #                      'module_uoa':'program',
    #                      'data_uoa':'cbench-automotive-susan',
    #                      'out':o})
    #         if r['return']>0:
    #             print r
    #         self.assertEqual(0, r['return']);

    # todo: pipeline ck run pipeline:program program_uoa=polybench-cuda-2mm
    #ck run pipeline:program program_uoa=cbench-automotive-susan