# encoding: utf-8

"""
Test at Windows environments required to invoke from py module because of
multiprocessing module:
http://py.readthedocs.io/en/latest/faq.html?highlight=cmdline#issues-with-py-test-multiprocess-and-setuptools
"""

import sys
import py


if __name__ == '__main__':
    sys.exit(py.test.cmdline.main())
