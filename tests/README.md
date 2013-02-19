# Dependencies

To run test, you need python modules installed :

 - mock: http://www.voidspace.org.uk/python/mock/
 - nose: http://pypi.python.org/pypi/nose
 - mockito: http://pypi.python.org/pypi/mockito

and all modules from the pip-requires.txt file


# Running the test suite

```
$ cd tests
$ python run.py
```


# Advanced use

`run.py` will run nosetests. Any command line argument passed to `run.py` will be passed over to the nosetests command.

Run `$ python run.py --help` to get the list of all nosetests supported options and plugins.

For instance if you want to generate the test coverage report, run `$ python run.py --with-xunit --cover-package=b3 --with-xcover`.