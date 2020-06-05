Railroad-Diagram Generator
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

(This is the README for the Python port;
to see the JS README, visit <https://github.com/tabatkins/railroad-diagrams>.)

Diagrams
--------

Constructing a diagram is a set of nested calls:

```python
from railroad import Diagram, Choice
d = Diagram("foo", Choice(0, "bar", "baz"))
d.writeSvg(sys.stdout.write)
```

A railroad diagram must be started as a `Diagram` object,
which takes a list of diagram items,
defined below.

The `Diagram()` constructor also optionally takes some keyword arguments:

* `css`: If passed, is the CSS you would like the diagram to include.
    If you don't pass anything, it defaults to including `railroad.DEFAULT_STYLE`.
    If you don't want it to include any css at all in the diagram
    (perhaps because you're including the `railroad.css` file manually in your page, and don't need each diagram to duplicate the CSS in itself),
    pass `css=None`.
* `type`: JSON.org, the inspiration for these diagram's styling, technically has two varieties of Diagrams: a "simple" kind it uses for "leaf" types like numbers, and a "complex" kind which is used for container types like arrays. The only difference is the shape of the start/end indicators of the diagram.

    Diagrams default to being "simple", but you can manually choose by passing `type="simple"` or `type="complex"`.

After constructing a Diagram, you can call `.format(...padding)` on it, specifying 0-4 padding values (just like CSS) for some additional "breathing space" around the diagram (the paddings default to 20px).

To output the diagram, call `.writeSvg(cb)` on it, passing a function that'll get called repeatedly to produce the SVG markup. `sys.stdout.write` (or the `.write` property of any file object) is a great value to pass if you're directly outputting it; if you need it as a plain string, a `StringIO` can be used.

If you need to walk the component tree of a diagram for some reason, `Diagram` has a `.walk(cb)` method as well, which will call your callback on every node in the diagram, in a "pre-order depth-first traversal" (the node first, then each child).

Components
----------

Components are either leaves (containing only text or similar)
or containers (containing other components).

The leaves:
* Terminal(text, href?, title?, cls?) or a bare string - represents literal text.

    All arguments past the first are optional:
    * 'href' makes the text a hyperlink with the given URL
    * 'title' adds an SVG `<title>` element to the element,
        giving it "hover text"
        and a description for screen-readers and other assistive tech
    * 'cls' is additional classes to apply to the element,
        beyond the default `'terminal'`

* NonTerminal(text, href) - represents an instruction or another production.

    The optional arguments have the same meaning as for Terminal,
    except that the default class is `'non-terminal'`.

* Comment(text, href) - a comment.

    The optional arguments have the same meaning as for Terminal,
    except that the default class is `'non-terminal'`.

* Skip() - an empty line

* Start(type, label) and End(type) - the start/end shapes. These are supplied by default, but if you want to supply a label to the diagram, you can create a Start() explicitly (as the first child of the Diagram!). The "type" attribute takes either "simple" (the default) or "complex", a la Diagram() and ComplexDiagram(). All arguments are optional.

The containers:
* Sequence(...children) - like simple concatenation in a regex.

    ![Sequence('1', '2', '3')](https://github.com/tabatkins/railroad-diagrams/raw/gh-pages/images/rr-sequence.svg?sanitize=true "Sequence('1', '2', '3')")

* Stack(...children) - identical to a Sequence, but the items are stacked vertically rather than horizontally. Best used when a simple Sequence would be too wide; instead, you can break the items up into a Stack of Sequences of an appropriate width.

    ![Stack('1', '2', '3')](https://github.com/tabatkins/railroad-diagrams/raw/gh-pages/images/rr-stack.svg?sanitize=true "Stack('1', '2', '3')")

* OptionalSequence(...children) - a Sequence where every item is *individually* optional, but at least one item must be chosen

    ![OptionalSequence('1', '2', '3')](https://github.com/tabatkins/railroad-diagrams/raw/gh-pages/images/rr-optionalsequence.svg?sanitize=true "OptionalSequence('1', '2', '3')")

* Choice(index, ...children) - like `|` in a regex.  The index argument specifies which child is the "normal" choice and should go in the middle (starting from 0 for the first child).

    ![Choice(1, '1', '2', '3')](https://github.com/tabatkins/railroad-diagrams/raw/gh-pages/images/rr-choice.svg?sanitize=true "Choice(1, '1', '2', '3')")

* MultipleChoice(index, type, ...children) - like `||` or `&&` in a CSS grammar; it's similar to a Choice, but more than one branch can be taken.  The index argument specifies which child is the "normal" choice and should go in the middle, while the type argument must be either "any" (1+ branches can be taken) or "all" (all branches must be taken).

    ![MultipleChoice(1, 'all', '1', '2', '3')](https://github.com/tabatkins/railroad-diagrams/raw/gh-pages/images/rr-multiplechoice.svg?sanitize=true "MultipleChoice(1, 'all', '1', '2', '3')")

* HorizontalChoice(...children) - Identical to Choice, but the items are stacked horizontally rather than vertically. There's no "straight-line" choice, so it just takes a list of children. Best used when a simple Choice would be too tall; instead, you can break up the items into a HorizontalChoice of Choices of an appropriate height.

	![HorizontalChoice(Choice(2,'0','1','2','3','4'), Choice(2, '5', '6', '7', '8', '9'))](https://github.com/tabatkins/railroad-diagrams/raw/gh-pages/images/rr-horizontalchoice.svg?sanitize=true "HorizontalChoice(Choice(2,'0','1','2','3','4'), Choice(2, '5', '6', '7', '8', '9'))")

* Optional(child, skip?) - like `?` in a regex.  A shorthand for `Choice(1, Skip(), child)`.  If the optional `skip` parameter is `True`, it instead puts the Skip() in the straight-line path, for when the "normal" behavior is to omit the item.

    ![Optional('foo'), Optional('bar', 'skip')](https://github.com/tabatkins/railroad-diagrams/raw/gh-pages/images/rr-optional.svg?sanitize=true "Optional('foo'), Optional('bar', 'skip')")

* OneOrMore(child, repeat?) - like `+` in a regex.  The 'repeat' argument is optional, and specifies something that must go between the repetitions (usually a `Comment()`, but sometimes things like `","`, etc.)

    ![OneOrMore('foo', Comment('bar'))](https://github.com/tabatkins/railroad-diagrams/raw/gh-pages/images/rr-oneormore.svg?sanitize=true "OneOrMore('foo', Comment('bar'))")

* AlternatingSequence(option1, option2) - similar to a OneOrMore, where you must alternate between the two choices, but allows you to start and end with either element. (OneOrMore requires you to start and end with the "child" node.)

    ![AlternatingSequence('foo', 'bar')](https://github.com/tabatkins/railroad-diagrams/raw/gh-pages/images/rr-alternatingsequence.svg?sanitize=true "AlternatingSequence('foo', 'bar')")

* ZeroOrMore(child, repeat?, skip?) - like `*` in a regex.  A shorthand for `Optional(OneOrMore(child, repeat), skip)`.  Both `repeat` (same as in `OneOrMore()`) and `skip` (same as in `Optional()`) are optional.

    ![ZeroOrMore('foo', Comment('bar')), ZeroOrMore('foo', Comment('bar'), 'skip')](https://github.com/tabatkins/railroad-diagrams/raw/gh-pages/images/rr-zeroormore.svg?sanitize=true "ZeroOrMore('foo', Comment('bar')), ZeroOrMore('foo', Comment('bar'), 'skip')")

* Group(child, label?) - highlights its child with a dashed outline, and optionally labels it. Passing a string as the label constructs a Comment, or you can build one yourself (to give an href or title).

    ![Sequence("foo", Group(Choice(0, NonTerminal('option 1'), NonTerminal('or two')), "label"), "bar",)](https://github.com/tabatkins/railroad-diagrams/raw/gh-pages/images/rr-group.svg?sanitize=true "Sequence('foo', Group(Choice(0, NonTerminal('option 1'), NonTerminal('or two')), 'label'), 'bar',)")


Options
-------

There are a few options you can tweak, living as UPPERCASE_CONSTANTS at the top of the module; these can be adjusted via `railroad.OPTION_NAME_HERE = "whatever"`.
Note that if you change the text sizes in the CSS,
you'll have to adjust the text metrics here as well.

* VS - sets the minimum amount of vertical separation between two items, in CSS px.  Note that the stroke width isn't counted when computing the separation; this shouldn't be relevant unless you have a very small separation or very large stroke width. Defaults to `8`.
* AR - the radius of the arcs, in CSS px, used in the branching containers like Choice.  This has a relatively large effect on the size of non-trivial diagrams.  Both tight and loose values look good, depending on what you're going for. Defaults to `10`.
* DIAGRAM_CLASS - the class set on the root `<svg>` element of each diagram, for use in the CSS stylesheet. Defaults to `"railroad-diagram"`.
* STROKE_ODD_PIXEL_LENGTH - the default stylesheet uses odd pixel lengths for 'stroke'. Due to rasterization artifacts, they look best when the item has been translated half a pixel in both directions. If you change the styling to use a stroke with even pixel lengths, you'll want to set this variable to `False`.
* INTERNAL_ALIGNMENT - when some branches of a container are narrower than others, this determines how they're aligned in the extra space.  Defaults to `"center"`, but can be set to `"left"` or `"right"`.
* CHAR_WIDTH - the approximate width, in CSS px, of characters in normal text (`Terminal` and `NonTerminal`). Defaults to `8.5`.
* COMMENT_CHAR_WIDTH - the approximate width, in CSS px, of character in `Comment` text, which by default is smaller than the other textual items. Defaults to `7`.
* DEBUG - if `True`, writes some additional "debug information" into the attributes of elements in the output, to help debug sizing issues. Defaults to `False`.

Caveats
-------

SVG can't actually respond to the sizes of content; in particular, there's no way to make SVG adjust sizing/positioning based on the length of some text.  Instead, I guess at some font metrics, which mostly work as long as you're using a fairly standard monospace font.  This works pretty well, but long text inside of a construct might eventually overflow the construct.

License
-------

This document and all associated files in the github project are licensed under [CC0](http://creativecommons.org/publicdomain/zero/1.0/) ![](http://i.creativecommons.org/p/zero/1.0/80x15.png).
This means you can reuse, remix, or otherwise appropriate this project for your own use **without restriction**.
(The actual legal meaning can be found at the above link.)
Don't ask me for permission to use any part of this project, **just use it**.
I would appreciate attribution, but that is not required by the license.
