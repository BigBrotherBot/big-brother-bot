"""
Run the all the tests using nosetests.
Eventual command line arguments will be passed over to nosetests.
"""

if __name__ == '__main__':
    import os
    import sys
    from nose.core import TestProgram

    argv = ['nosetests', os.path.dirname(__file__)]
    argv.extend(sys.argv)
    TestProgram(argv=argv)
