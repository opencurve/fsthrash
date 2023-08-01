===================================================
`Fsthrash` -- The storage integration test framework
===================================================

``fsthrash`` is an automation stress test framework, written in `Python
<https://www.python.org/>`__. It is used for mixed pressure measurement in various scenarios,
The use cases contained in the current fsthrash are basically used for the pressure test of the storage system
,Of course, you can also use this framework to develop your own test cases

Overview
========

When testing, it is common to group many jobs together to form a test run

Provided Utilities
==================

* :ref:`fsthrash-results` - Examing the result of a running or finished test
* :ref:`fsthrash-suite` - Schedule a full run based on suites

Installation
============

pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

./bootstrap install

Test Suites
===========

Test directory contains subdirectories and yaml files, which, when assembled, produce valid tests that can be run. The test suite application generates combinations of these files and thus ends up running a set of tests based off the data in the directory for the suite.

To run a suite, enter::
    
    fsthrash-suite --suite_path  <suite_path>  --testdir  <testdir>   --numjobs <numjobs>

where:

suite_path: the name of the suite dir (the directory in fsthrash/suites)
testdir: Stress test paths that need to be tested,Multiple test paths can be specified, separated by commas. The yaml file dir.1 corresponds to the first directory
numjobs: Number of parallel tests

For example, consider::

    ./virtualenv/bin/fsthrash-suite --suite_path /home/fsthrash/suites --testdir /home/fsthrash/test5,/home/fsthrash/test6 --numjobs 2

These logs are also publically available at output dir.
