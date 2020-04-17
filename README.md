Railroad-diagram Generator
==========================

<a href="images/rr-title.svg"><img src="images/rr-title.svg" alt="Diagram(Stack('Generate', 'some'), OneOrMore(NonTerminal('railroad diagrams'), Comment('and more')))" title="Diagram(Stack('Generate', 'some'), OneOrMore(NonTerminal('railroad diagrams'), Comment('and more')))" width=10000></a>

This is a small library for generating railroad diagrams
(like what [JSON.org](http://json.org) uses)
using SVG, with both JS and Python ports.

Railroad diagrams are a way of visually representing a grammar
in a form that is more readable than using regular expressions or BNF.
They can easily represent any context-free grammar, and some more powerful grammars.
There are several railroad-diagram generators out there, but none of them had the visual appeal I wanted, so I wrote my own.

[Here's an online dingus for you to play with and get SVG code from!](https://tabatkins.github.io/railroad-diagrams/generator.html)

Details
-------

To use the library,
include `railroad.css` in your page,
and import the `railroad.js` module in your script,
then call the Diagram() function.
Its arguments are the components of the diagram
(Diagram is a special form of Sequence).

The constructors for each node are named exports in the module;
the default export is an object of same-named functions that just call the constructors,
so you can construct diagrams without having to spam `new` all over the place:

```js
// Use the constructors
import {Diagram, Choice} from "./railroad.js";
const d = new Diagram("foo", new Choice(0, "bar", "baz"));

// Or use the functions that call the constructors for you
import rr from "./railroad.js";
const d = rr.Diagram("foo", rr.Choice(0, "bar", "baz"));
```

(For Python, see [Python Port](#python-port).)

Alternately, you can call ComplexDiagram();
it's identical to Diagram(),
but has slightly different start/end shapes,
same as what JSON.org does to distinguish between "leaf" types like number (ordinary Diagram())
and "container" types like Array (ComplexDiagram()).

Components are either leaves or containers.

The leaves:
* Terminal(text, href) or a bare string - represents literal text. The 'href' attribute is optional, and creates a hyperlink with the given destination.
* NonTerminal(text, href) - represents an instruction or another production. The 'href' attribute is optional, and creates a hyperlink with the given destination.
* Comment(text, href) - a comment. The 'href' attribute is optional, and creates a hyperlink with the given destination.
* Skip() - an empty line
* Start(type, label) and End(type) - the start/end shapes. These are supplied by default, but if you want to supply a label to the diagram, you can create a Start() explicitly (as the first child of the Diagram!). The "type" attribute takes either "simple" (the default) or "complex", a la Diagram() and ComplexDiagram(). All arguments are optional.

The containers:
* Sequence(...children) - like simple concatenation in a regex.

    ![Sequence('1', '2', '3')](images/rr-sequence.svg "Sequence('1', '2', '3')")

* Stack(children) - identical to a Sequence, but the items are stacked vertically rather than horizontally. Best used when a simple Sequence would be too wide; instead, you can break the items up into a Stack of Sequences of an appropriate width.

    ![Stack('1', '2', '3')](images/rr-stack.svg "Stack('1', '2', '3')")

* OptionalSequence(...children) - a Sequence where every item is *individually* optional, but at least one item must be chosen

    ![OptionalSequence('1', '2', '3')](images/rr-optionalsequence.svg "OptionalSequence('1', '2', '3')")

* Choice(index, ...children) - like `|` in a regex.  The index argument specifies which child is the "normal" choice and should go in the middle

    ![Choice(1, '1', '2', '3')](images/rr-choice.svg "Choice(1, '1', '2', '3')")

* MultipleChoice(index, type, ...children) - like `||` or `&&` in a CSS grammar; it's similar to a Choice, but more than one branch can be taken.  The index argument specifies which child is the "normal" choice and should go in the middle, while the type argument must be either "any" (1+ branches can be taken) or "all" (all branches must be taken).

    ![MultipleChoice(1, 'all', '1', '2', '3')](images/rr-multiplechoice.svg "MultipleChoice(1, 'all', '1', '2', '3')")

* HorizontalChoice(...children) - Identical to Choice, but the items are stacked horizontally rather than vertically. There's no "straight-line" choice, so it just takes a list of children. Best used when a simple Choice would be too tall; instead, you can break up the items into a HorizontalChoice of Choices of an appropriate height.

	![HorizontalChoice(Choice(2,'0','1','2','3','4'), Choice(2, '5', '6', '7', '8', '9'))](images/rr-horizontalchoice.svg "HorizontalChoice(Choice(2,'0','1','2','3','4'), Choice(2, '5', '6', '7', '8', '9'))")

* Optional(child, skip) - like `?` in a regex.  A shorthand for `Choice(1, Skip(), child)`.  If the optional `skip` parameter has the value `"skip"`, it instead puts the Skip() in the straight-line path, for when the "normal" behavior is to omit the item.


    ![Optional('foo'), Optional('bar', 'skip')](images/rr-optional.svg "Optional('foo'), Optional('bar', 'skip')")

* OneOrMore(child, repeat) - like `+` in a regex.  The 'repeat' argument is optional, and specifies something that must go between the repetitions (usually a `Comment()`, but sometimes things like `","`, etc.)

    ![OneOrMore('foo', Comment('bar'))](images/rr-oneormore.svg "OneOrMore('foo', Comment('bar'))")

* AlternatingSequence(option1, option2) - similar to a OneOrMore, where you must alternate between the two choices, but allows you to start and end with either element. (OneOrMore requires you to start and end with the "child" node.)

    ![AlternatingSequence('foo', 'bar')](images/rr-alternatingsequence.svg "AlternatingSequence('foo', 'bar')")

* ZeroOrMore(child, repeat, skip) - like `*` in a regex.  A shorthand for `Optional(OneOrMore(child, repeat), skip)`.  Both `repeat` (same as in `OneOrMore()`) and `skip` (same as in `Optional()`) are optional.

    ![ZeroOrMore('foo', Comment('bar')), ZeroOrMore('foo', Comment('bar'), 'skip')](images/rr-zeroormore.svg "ZeroOrMore('foo', Comment('bar')), ZeroOrMore('foo', Comment('bar'), 'skip')")

* Group(child, label?) - highlights its child with a dashed outline, and optionally labels it. Passing a string as the label constructs a Comment, or you can build one yourself (to give an href or title).

    ![Sequence("foo", Group(Choice(0, NonTerminal('option 1'), NonTerminal('or two')), "label"), "bar",)](images/rr-group.svg "Sequence('foo', Group(Choice(0, NonTerminal('option 1'), NonTerminal('or two')), 'label'), 'bar',)")

After constructing a Diagram, call `.format(...padding)` on it, specifying 0-4 padding values (just like CSS) for some additional "breathing space" around the diagram (the paddings default to 20px).

The result can either be `.toString()`'d for the markup, or `.toSVG()`'d for an `<svg>` element, which can then be immediately inserted to the document.  As a convenience, Diagram also has an `.addTo(element)` method, which immediately converts it to SVG and appends it to the referenced element with default paddings. `element` defaults to `document.body`.

Options
-------

There are a few options you can tweak, with the defaults at the bottom of the file, and the live values hanging off of the `Diagram` object.  Just tweak either until the diagram looks like what you want.
You can also change the CSS file - feel free to tweak to your heart's content.
Note, though, that if you change the text sizes in the CSS,
you'll have to go adjust the metrics for the leaf nodes as well.

* VERTICAL_SEPARATION - sets the minimum amount of vertical separation between two items.  Note that the stroke width isn't counted when computing the separation; this shouldn't be relevant unless you have a very small separation or very large stroke width.
* ARC_RADIUS - the radius of the arcs used in the branching containers like Choice.  This has a relatively large effect on the size of non-trivial diagrams.  Both tight and loose values look good, depending on what you're going for.
* DIAGRAM_CLASS - the class set on the root `<svg>` element of each diagram, for use in the CSS stylesheet.
* STROKE_ODD_PIXEL_LENGTH - the default stylesheet uses odd pixel lengths for 'stroke'. Due to rasterization artifacts, they look best when the item has been translated half a pixel in both directions. If you change the styling to use a stroke with even pixel lengths, you'll want to set this variable to `false`.
* INTERNAL_ALIGNMENT - when some branches of a container are narrower than others, this determines how they're aligned in the extra space.  Defaults to "center", but can be set to "left" or "right".

Caveats
-------

SVG can't actually respond to the sizes of content; in particular, there's no way to make SVG adjust sizing/positioning based on the length of some text.  Instead, I guess at some font metrics, which mostly work as long as you're using a fairly standard monospace font.  This works pretty well, but long text inside of a construct might eventually overflow the construct.

Python Port
-----------

In addition to the canonical JS version, the library now exists as a Python library as well.

Using it is basically identical.  The config variables are globals in the file, and so may be adjusted either manually or via tweaking from inside your program.

The main difference from the JS port is how you extract the string from the Diagram.  You'll find a `writeSvg(writerFunc)` method on `Diagram`, which takes a callback of one argument and passes it the string form of the diagram.  For example, it can be used like `Diagram(...).writeSvg(sys.stdout.write)` to write to stdout.  **Note**: the callback will be called multiple times as it builds up the string, not just once with the whole thing.  If you need it all at once, consider something like a `StringIO` as an easy way to collect it into a single string.

As well, if you want a "complex" diagram, pass `type="complex"` to the `Diagram` constructor, rather than using a separate `ComplexDiagram()` constructor like in the JS port.

To **install** the python port, clone this project and `pip install` it.

```shell
~/> git clone https://github.com/tabatkins/railroad-diagrams.git
~/> cd railroad-diagrams/
~/railroad-diagrams/> python3 -m pip install .
```

...or just include the `railroad.py` file directly in your project.

License
-------

This document and all associated files in the github project are licensed under [CC0](http://creativecommons.org/publicdomain/zero/1.0/) ![](http://i.creativecommons.org/p/zero/1.0/80x15.png).
This means you can reuse, remix, or otherwise appropriate this project for your own use **without restriction**.
(The actual legal meaning can be found at the above link.)
Don't ask me for permission to use any part of this project, **just use it**.
I would appreciate attribution, but that is not required by the license.
