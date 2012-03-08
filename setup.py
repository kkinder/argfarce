from distutils.core import setup
setup(name='argfarce',
      version='1.1',
      py_modules=['argfarce'],
      author = "Ken Kinder",
      author_email = "kkinder@gmail.com",
      url = "http://kkinder.com/argfarce",
      keywords = ["argument parsing", "argparse", "optparse"],
      classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      long_description = """\
Argfarce
--------

Argfarce makes it easy to declare argparse structures.  Consider this example:

>>> class PersonalInfoParser(ArgumentParser):
...     class Meta:
...         prog = 'person.py'
...     
...     name = Argument('-n', help="Cheese to use on your sandwich", required=False)
...     profession = Argument('-p', '--profession', choices=('developer', 'programmer', 'software engineer'), help="These are all pretty much the same", required=False)
...     comments = Argument(nargs='*')
... 
>>> parser = PersonalInfoParser()
>>> parser.parse_args('-p programmer -n Ken foo bar spam'.split())
>>> print parser.name
Ken
>>> print parser.profession
programmer
>>> print parser.comments
['foo', 'bar', 'spam']

This software is not yet compatible with Python 3.
"""
      )
