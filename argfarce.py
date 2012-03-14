"""
Argfarce library.

Copyright (C) 2008-2012 by
    Ken Kinder <http://kkinder.com>
    Unai Zalakain <http://www.gisa-elkartea.org/hasiera>

---------------------------------------------------------------------------------
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
---------------------------------------------------------------------------------

Argfarce makes it easy to declare argparse structures. Consider this example:

>>> class PersonalInfoParser(ArgumentParser):
...     class Meta:
...         prog = 'person.py'
...     
...     profession = Argument('-p', '--profession', choices=('developer', 'programmer', 'software engineer'), help="These are all pretty much the same")
...     action = Argument('-a', '--action')
...     name = Argument('full_name')
...     comments = Argument(nargs='*')
... 
>>> parser = PersonalInfoParser()
>>> parser.parse_args('-p programmer -a salute Ken foo bar spam'.split())
>>> print parser.action
salute
>>> print parser.name
Ken
>>> print parser.profession
programmer
>>> print parser.comments
['foo', 'bar', 'spam']

Argfarce will also work with subparsers and subparser level calls:

>>> class SandwichParser(ArgumentParser):
...     class Meta:
...         prog = 'sandwich.py'
...         subparser_help = 'Use one of the following commands:'
...     
...     class MakeSandwichParser(ArgumentParser):
...         class Meta:
...             subparser_argument = 'make'
...             call = 'func'
...             
...         cheese = Argument('-c', '--use-cheese', choices=('cheddar', 'provolone', 'swiss'), help="Cheese to use on your sandwich")
...         protein = Argument('-p', '--use-protein', choices=('tempeh', 'chicken', 'beef'), help="Protein for your meal")
...         extras = Argument('-x', '--extras', nargs="+", choices=('lettuce', 'tomato', 'olives', 'peppers', 'pickles', 'oil'), help="Fixings you want")
...     
...         def func(self, args):
...             return args.cheese.upper()
...
...
...     class EatSandwichParser(ArgumentParser):
...         class Meta:
...             subparser_argument = 'eat'
...             call = 'func'
...             
...         speed = Argument('-s', choices=('fast', 'slow'), help="How fast to eat the sandwich")
...
...         def func(self, args):
...             if args.speed == 'fast':
...                 return 'speed of light!'
...             else:
...                 return 'slow motion'
... 
>>> p = SandwichParser()
>>> p.parse_args('make -c swiss -p beef -x lettuce tomato olives'.split())
>>> print p.cheese
swiss
>>> print p.protein
beef
>>> print p.extras
['lettuce', 'tomato', 'olives']
>>> print p.call(p)
SWISS
>>> p.parse_args('eat -s fast'.split())
>>> print p.speed
fast
>>> print p.call(p)
speed of light!
"""

import argparse
import inspect
import sys
import warnings
from collections import OrderedDict

class _DeclarativeMeta(type):
    ##
    ## Ian Bicking's example, IIRC
    ##
    def __new__(meta, class_name, bases, new_attrs):
        cls = type.__new__(meta, class_name, bases, new_attrs)
        if new_attrs.has_key('__classinit__'):
            cls.__classinit__ = staticmethod(cls.__classinit__.im_func)
        cls.__classinit__(cls, new_attrs)
        return cls

class _DefaultValue(object):
    pass

_argumentParserOptions = (
    'description',
    'epilog',
    'prog',
    'usage',
    'version',
    'add_help',
    'argument_default',
    'parents',
    'prefix_chars',
    'conflict_handler',
    'formatter_class')

class ArgumentParser(object):
    _creation_counter = 0

    def __init__(self, parser=None):
        self._creation_counter = Argument._creation_counter
        Argument._creation_counter += 1

        self._arguments = OrderedDict()
        self._children = OrderedDict()
        self._namespace_translations = {}
        self._subparsers = None
        
        if parser:
            self._parser = parser
        else:
            parser_args = self._getmeta()
            self._parser = argparse.ArgumentParser(**parser_args)
        
        if hasattr(self, 'Meta'):
            if hasattr(self.Meta, 'subparser_help'):
                self._subparser_help = getattr(self.Meta, 'subparser_help')
            else:
                self._subparser_help = None
            if hasattr(self.Meta, 'call'):
                call = getattr(self, self.Meta.call)
                parser.set_defaults(call=call)

        self._orderargs()
        self._handleargs(self._parser)
        
    def _getmeta(self):
        parser_args = {}
        if hasattr(self, 'Meta'):
            for k, v in self.Meta.__dict__.items():
                if not k.startswith('_'):
                    if k in _argumentParserOptions:
                        parser_args[k] = v
                    elif k in ('subparser_argument', 'subparser_help'):
                        # These are special meta variables for subparsers
                        pass
                    else:
                        warnings.warn('Unexpected attribute on ArgumentParser %r Meta class: %r' % \
                                      (k, self))
        return parser_args
        
    def _orderargs(self):
        arguments = {}
        children = {}
        for k in dir(self):
            v = getattr(self, k, None)
            if isinstance(v, Argument):
                arguments[k] = v
            elif (not k.startswith('__')) and inspect.isclass(v) and issubclass(v, ArgumentParser):
                children[k] = v
        self._arguments.update(sorted(arguments.items(), key=lambda a: a[1]._creation_counter))
        self._children.update(sorted(children.items(), key=lambda s: s[1]._creation_counter))

    def _handleargs(self, parser):
        for k, v in self._arguments.items():

            # If positional argument
            if len(v.args) == 1 and v.args[0][0] not in parser.prefix_chars:
                # If argument name and class attribute name differs
                if k != v.args[0]:
                    # Add it for future namespace translation
                    self._namespace_translations[v.args[0]] = k
            else:
                v.kwargs['dest'] = k
            parser.add_argument(*v.args, **v.kwargs)
                
        if self._children:
            if not self._subparsers:
                if self._subparser_help:
                    self._subparsers = parser.add_subparsers(help=self._subparser_help)
                else:
                    self._subparsers = parser.add_subparsers()
                
            for k, v in self._children.items():
                subparser_args = []
                if hasattr(v, 'Meta') and hasattr(v.Meta, 'subparser_argument'):
                    subparser_args.append(v.Meta.subparser_argument)
                else:
                    subparser_args.append(v.__name__.lower())
                
                subparser = self._subparsers.add_parser(*subparser_args)
                instance = v(parser=subparser)
    
    def _namespacify(self, namespace):
        for k, v in namespace.__dict__.items():
            if k in self._namespace_translations:
                k = self._namespace_translations[k]
            setattr(self, k, v)
    
    ###################################################
    ## Wrapper functions pointing up to self._parser ##
    ###################################################
    def parse_args(self, args=None):
        self._namespace = self._parser.parse_args(args=args)
        self._namespacify(self._namespace)
    
    def parse_known_args(self, args=None):
        self._namespace = self._parser.parse_known_args(args=args)
        self._namespacify(self._namespace)
        
    def convert_arg_line_to_args(self, arg_line):
        return [arg_line]
    
    def format_usage(self):
        return self._parser.format_usage()

    def format_help(self):
        return self._parser.format_help()

    def format_version(self):
        return self._parser.format_version()
    
    def print_usage(self, file=None):
        return self._parser.print_usage(file=file)

    def print_help(self, file=None):
        return self._parser.print_help(file=file)

    def print_version(self, file=None):
        return self._parser.print_version(file=file)
    
    def exit(self, status=0, message=None):
        return self._parser.exit(status=status, message=message)

class Argument(object):
    # Track each time an Argument is created. Used to retain order.
    _creation_counter = 0

    def __init__(self, *args, **kwargs):
        self._creation_counter = Argument._creation_counter
        Argument._creation_counter += 1

        self.args = args
        self.kwargs = kwargs
        

if __name__ == "__main__":
    import doctest
    doctest.testmod()
