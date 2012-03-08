"""
Argfarce library.

Copyright (C) 2008 Ken Kinder

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

Argfarce will also work with subparsers:

>>> class SandwichParser(ArgumentParser):
...     class Meta:
...         prog = 'sandwich.py'
...         subparser_help = 'Use one of the following commands:'
...     
...     class MakeSandwichParser(ArgumentParser):
...         class Meta:
...             subparser_argument = 'make'
...             
...         cheese = Argument('-c', '--use-cheese', choices=('cheddar', 'provolone', 'swiss'), help="Cheese to use on your sandwich")
...         protein = Argument('-p', '--use-protein', choices=('tempeh', 'chicken', 'beef'), help="Protein for your meal")
...         extras = Argument('-x', '--extras', nargs="+", choices=('lettuce', 'tomato', 'olives', 'peppers', 'pickles', 'oil'), help="Fixings you want")
...     
...     class EatSandwichParser(ArgumentParser):
...         class Meta:
...             subparser_argument = 'eat'
...             
...         speed = Argument('-s', choices=('fast', 'slow'), help="How fast to eat the sandwich")
... 
>>> p = SandwichParser()
>>> p.parse_args('make -c swiss -p beef -x lettuce tomato olives'.split())
>>> print p.cheese
swiss
>>> print p.protein
beef
>>> print p.extras
['lettuce', 'tomato', 'olives']
>>> 
>>> p.parse_args('eat -s fast'.split())
>>> print p.speed
fast
"""

import argparse
import inspect
import sys
import warnings

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
    def __init__(self, parser=None):
        self._subparsers = None
        
        if parser:
            self._parser = parser
        else:
            parser_args = self._getmeta()
            self._parser = argparse.ArgumentParser(**parser_args)
        
        if hasattr(self, 'Meta') and hasattr(self.Meta, 'subparser_help'):
            self._subparser_help = getattr(self.Meta, 'subparser_help')
        else:
            self._subparser_help = None
        
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
        
    def _handleargs(self, parser):
        for k in dir(self):
            v = getattr(self, k, None)
            if isinstance(v, Argument):
                v.kwargs['dest'] = k
                parser.add_argument(*v.args, **v.kwargs)
            if (not k.startswith('__')) and inspect.isclass(v) and issubclass(v, ArgumentParser):
                
                if not self._subparsers:
                    if self._subparser_help:
                        self._subparsers = parser.add_subparsers()
                    else:
                        self._subparsers = parser.add_subparsers(help=self._subparser_help)
                
                subparser_args = []
                if hasattr(v, 'Meta') and hasattr(v.Meta, 'subparser_argument'):
                    subparser_args.append(v.Meta.subparser_argument)
                else:
                    subparser_args.append(v.__name__.lower())
                
                subparser = self._subparsers.add_parser(*subparser_args)
                instance = v(parser=subparser)
    
    def _namespacify(self, namespace):
        for k, v in namespace.__dict__.items():
            setattr(self, k, getattr(namespace, k))
    
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
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        
if __name__ == "__main__":
    import doctest
    doctest.testmod()
