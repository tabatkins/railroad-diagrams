Railroad-diagram Generator
==========================

<a href="https://github.com/tabatkins/railroad-diagrams/blob/gh-pages/images/rr-title.svg"><img src="https://github.com/tabatkins/railroad-diagrams/raw/gh-pages/images/rr-title.svg?sanitize=true" alt="Diagram(Stack('Generate', 'some'), OneOrMore(NonTerminal('railroad diagrams'), Comment('and more')))" title="Diagram(Stack('Generate', 'some'), OneOrMore(NonTerminal('railroad diagrams'), Comment('and more')))" width=10000></a>

This is a small library for generating railroad diagrams
(like what [JSON.org](http://json.org) uses)
using SVG, with both JS and Python ports.

Railroad diagrams are a way of visually representing a grammar
in a form that is more readable than using regular expressions or BNF.
They can easily represent any context-free grammar, and some more powerful grammars.
There are several railroad-diagram generators out there, but none of them had the visual appeal I wanted, so I wrote my own.

[Here's an online dingus for you to play with and get SVG code from!](https://tabatkins.github.io/railroad-diagrams/generator.html)

Versions
--------

This library is supported both as a JS module and a Python module,
and the install and use instructions for each
are in their lang-specific READMEs.

* [JS-specific README](README-js.md)
* [Python-specific README](README-py.md)


Caveats
-------

SVG can't actually respond to the sizes of content; in particular, there's no way to make SVG adjust sizing/positioning based on the length of some text.  Instead, I guess at some font metrics, which mostly work as long as you're using a fairly standard monospace font.  This works pretty well, but long text inside of a construct might eventually overflow the construct.


License
-------

Standard MIT license; see [LICENSE](LICENSE).

Don't ask me for permission to use any part of this project, **just use it**.
I would appreciate attribution, but that is not required by the license.
If you're doing something cool with it, again I'd appreciate it if you let me know, but that's not required either.