# argfarce

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
