pep8-coffee-docstrings
=========================

pretty printer for coffeescript and python

Python
==============
Adds docstrings to functions and methods and makes the code adhere pep8

python cp.py -f yourfile.py

<pre>


def value_to_json(self, key, value, raw):
    ...
    if error:
        raise MyException
    return key, value
    
def value_to_json(self, key, value, raw):
    """
    @type key: str
    @type value: str
    @type raw: bool
    @return: (str, str) @raise MyException:
    """
    ...
    return key, value
</pre>


Coffeescript
==============
reformats coffeescript in a consistant way, usage

python cp.py -f yourfile.coffee

Also ads debugging info to printstatements (linenumber and sourcefile)

<pre>
print "hello world"
</pre>

becomes

<pre>
print "yourfile.cf:1", "helloworld"
</pre>


