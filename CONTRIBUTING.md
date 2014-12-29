# How to contribute

With the many games the B3 project supports, third party patches are essential to keep the project great. There are a
few guidelines that we need contributors to follow so that we can have a chance of keeping B3 project as clean and 
organized as possible.

****************

## Contributing Issues

Issues submitted on Github must be technically documented with the aim that any contributor trying to fix your issue 
should have enough information to understand and reproduce the issue and validate the fix.

* Make sure you have a [GitHub account](https://github.com/signup/free).
* Search for a similar issue.
* Submit your issue, assuming one does not already exist.
* Clearly describe the issue including:
    * Steps to reproduce.
    * Expected results.
    * Actual results.
* Make sure you fill in the earliest version number of B3 that you know has the issue.

## Contributing Code

We prefer contributors to submit their code change throught GitHub [pull requests](http://help.github.com/send-pull-requests/). 
If you are not able to send pull requests,  you can submit patches on the B3 forums provided that your patch is small 
enough to be easily merged and tested.

* Make sure you have a [GitHub account](https://github.com/signup/free).
* [Fork](https://github.com/BigBrotherBot/big-brother-bot/fork) this repository on GitHub.
* Create a topic branch from where you want to base your work.
    * This is usually **NOT** the `master` branch. You should push your changes to a `release` branch. 
    * Please avoid working directly on the `master` branch.
* Make sure your code follows our [coding style](#coding-style)
* Make commits of logical units.
* Make sure your commit messages are in the proper format (example below): 
```
   [STORAGE] this commit is changing code in the storage module
   
   You can put a description of the changes being carried by the commit in the body of the 
   commit message while keeping the first line of the commit message as short as possible. 
   The first line is a real life imperative statement which may contain the link to the 
   issue being fixed by the commit. The body describes the behavior without the patch, why 
   this is a problem, and how the patch fixes the problem when applied.
```
* Make sure you have added all the necessary tests for your changes.
* Make sure that all the provided tests pass before sending a pull request.
* Squash multiple trivial commits into a single commit.

# Submitting Your Changes

* Push your changes to a topic branch in your fork of the repository.
* Submit a pull request to the BigBrotherBot/big-brother-bot repository.
* Update the issue to mark that you have submitted code and are ready for it to be reviewed.
* Include a link to the pull request in the issue.
* A pull request should contain a single feature/bugfix. If you need to send multiple features/bugfixes please
  use separate pull requests.

## Coding Style

Different programmers use to write code in different ways. Without the usage of coding conventions, a project source code
may become unreadable and eventually not understandable. While B3 doesn't strictly follows PEP-8 coding conventions, it 
is required that your code follows the following guidelines:

* Break long lines after 110 characters (max GitHub web-viewer capacity)
* Do not indent using `TAB`: use 4 spaces to indent your code.
* Do not use python built-in names to name your variables.
* Document your code (example below):
```python
def myFunc(self, param1, param2):
   """
   Put the description here.
   :param param1: The first parameter.
   :param param2: The second parameter.
   :raise MyError: The exception class if your function may raise an exception.
   :return: The return value of your function.
   """"
   ...
```
* Always use `self` for the first argument to instance methods.
* Always use `cls` for the first argument to class methods.
* Use uppercase for SQL keywords and lowercase for SQL identifiers.
* When catching exceptions, mention specific exceptions whenever possible instead of using only the `except` keyword.
* When you add new python modules remember to place the licensing on the top of the file.
* Remember to update the changelog you can find in python modules whenever you make changes.
* Last but not least: comment your code!

****************

# Additional Resources

* [Bug tracker](https://github.com/BigBrotherBot/big-brother-bot/issues)
* [General GitHub documentation](http://help.github.com/)
* [GitHub pull request documentation](http://help.github.com/send-pull-requests/)
