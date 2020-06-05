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

(For Python, see [the Python README](https://github.com/tabatkins/railroad-diagrams/blob/gh-pages/README-py.md), or just `pip install railroad-diagrams`.)

Diagrams
--------

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

Alternately, you can call ComplexDiagram();
it's identical to Diagram(),
but has slightly different start/end shapes,
same as what JSON.org does to distinguish between "leaf" types like number (ordinary Diagram())
and "container" types like Array (ComplexDiagram()).

The Diagram class also has a few methods:

* `.walk(cb)` calls the cb function on the diagram, then on its child nodes, recursing down the tree. This is a "pre-order depth-first" traversal, if you're into that sort of thing - the first child's children are visited before the diagram's second child. (In other words, the same order you encounter their constructors in the code that created the diagram.) Use this if you want to, say, sanitize things in the diagram.
* `.format(...paddings)` "formats" the Diagram to make it ready for output. Pass it 0-4 paddings, interpreted just like the CSS `padding` property, to give it some "breathing room" around its box; these default to `20` if not specified. This is automatically called by the output functions if you don't do so yourself, so if the default paddings suffice, there's no need to worry about this.
* `.toString()` outputs the SVG of the diagram as a string, ready to be put into your HTML. This is *not* a standalone SVG file; it's intended to be embedded into HTML.
* `.toStandalone()` outputs the SVG of the diagram as a string, but this *is* a standalone SVG file.
* `.toSVG()` outputs the diagram as an actual `<svg>` DOM element, ready for appending into a document.
* `.addTo(parent?)` directly appends the diagram, as an `<svg>` element, to the specified parent element. If you omit the parent element, it instead appends to the script element it's being called from, so you can easily insert a diagram into your document by just dropping a tiny inline `<script>` that just calls `new Diagram(...).addTo()` where you want the diagram to show up.


Components
----------

Components are either leaves or containers.

The leaves:
* Terminal(text, {href, title, cls}) or a bare string - represents literal text.

    All the arguments in the options bag are optional:
    * 'href' makes the text a hyperlink with the given URL
    * 'title' adds an SVG `<title>` element to the element,
        giving it "hover text"
        and a description for screen-readers and other assistive tech
    * 'cls' is additional classes to apply to the element,
        beyond the default `'terminal'`

* NonTerminal(text, {href, title, cls}) - represents an instruction or another production.

    The optional arguments have the same meaning as for Terminal,
    except that the default class is `'non-terminal'`.

* Comment(text, {href, title, cls}) - a comment.

    The optional arguments have the same meaning as for Terminal,
    except that the default class is `'comment'`.

* Skip() - an empty line

* Start(type, label) and End(type) - the start/end shapes. These are supplied by default, but if you want to supply a label to the diagram, you can create a Start() explicitly (as the first child of the Diagram!). The "type" attribute takes either "simple" (the default) or "complex", a la Diagram() and ComplexDiagram(). All arguments are optional.

The containers:
* Sequence(...children) - like simple concatenation in a regex.

    ![Sequence('1', '2', '3')](https://github.com/tabatkins/railroad-diagrams/raw/gh-pages/images/rr-sequence.svg?sanitize=true "Sequence('1', '2', '3')")

* Stack(...children) - identical to a Sequence, but the items are stacked vertically rather than horizontally. Best used when a simple Sequence would be too wide; instead, you can break the items up into a Stack of Sequences of an appropriate width.

    ![Stack('1', '2', '3')](https://github.com/tabatkins/railroad-diagrams/raw/gh-pages/images/rr-stack.svg?sanitize=true "Stack('1', '2', '3')")

* OptionalSequence(...children) - a Sequence where every item is *individually* optional, but at least one item must be chosen

    ![OptionalSequence('1', '2', '3')](https://github.com/tabatkins/railroad-diagrams/raw/gh-pages/images/rr-optionalsequence.svg?sanitize=true "OptionalSequence('1', '2', '3')")

* Choice(index, ...children) - like `|` in a regex.  The index argument specifies which child is the "normal" choice and should go in the middle

    ![Choice(1, '1', '2', '3')](https://github.com/tabatkins/railroad-diagrams/raw/gh-pages/images/rr-choice.svg?sanitize=true "Choice(1, '1', '2', '3')")

* MultipleChoice(index, type, ...children) - like `||` or `&&` in a CSS grammar; it's similar to a Choice, but more than one branch can be taken.  The index argument specifies which child is the "normal" choice and should go in the middle, while the type argument must be either "any" (1+ branches can be taken) or "all" (all branches must be taken).

    ![MultipleChoice(1, 'all', '1', '2', '3')](https://github.com/tabatkins/railroad-diagrams/raw/gh-pages/images/rr-multiplechoice.svg?sanitize=true "MultipleChoice(1, 'all', '1', '2', '3')")

* HorizontalChoice(...children) - Identical to Choice, but the items are stacked horizontally rather than vertically. There's no "straight-line" choice, so it just takes a list of children. Best used when a simple Choice would be too tall; instead, you can break up the items into a HorizontalChoice of Choices of an appropriate height.

	![HorizontalChoice(Choice(2,'0','1','2','3','4'), Choice(2, '5', '6', '7', '8', '9'))](https://github.com/tabatkins/railroad-diagrams/raw/gh-pages/images/rr-horizontalchoice.svg?sanitize=true "HorizontalChoice(Choice(2,'0','1','2','3','4'), Choice(2, '5', '6', '7', '8', '9'))")

* Optional(child, skip) - like `?` in a regex.  A shorthand for `Choice(1, Skip(), child)`.  If the optional `skip` parameter has the value `"skip"`, it instead puts the Skip() in the straight-line path, for when the "normal" behavior is to omit the item.


    ![Optional('foo'), Optional('bar', 'skip')](https://github.com/tabatkins/railroad-diagrams/raw/gh-pages/images/rr-optional.svg?sanitize=true "Optional('foo'), Optional('bar', 'skip')")

* OneOrMore(child, repeat) - like `+` in a regex.  The 'repeat' argument is optional, and specifies something that must go between the repetitions (usually a `Comment()`, but sometimes things like `","`, etc.)

    ![OneOrMore('foo', Comment('bar'))](https://github.com/tabatkins/railroad-diagrams/raw/gh-pages/images/rr-oneormore.svg?sanitize=true "OneOrMore('foo', Comment('bar'))")

* AlternatingSequence(option1, option2) - similar to a OneOrMore, where you must alternate between the two choices, but allows you to start and end with either element. (OneOrMore requires you to start and end with the "child" node.)

    ![AlternatingSequence('foo', 'bar')](https://github.com/tabatkins/railroad-diagrams/raw/gh-pages/images/rr-alternatingsequence.svg?sanitize=true "AlternatingSequence('foo', 'bar')")

* ZeroOrMore(child, repeat, skip) - like `*` in a regex.  A shorthand for `Optional(OneOrMore(child, repeat), skip)`.  Both `repeat` (same as in `OneOrMore()`) and `skip` (same as in `Optional()`) are optional.

    ![ZeroOrMore('foo', Comment('bar')), ZeroOrMore('foo', Comment('bar'), 'skip')](https://github.com/tabatkins/railroad-diagrams/raw/gh-pages/images/rr-zeroormore.svg?sanitize=true "ZeroOrMore('foo', Comment('bar')), ZeroOrMore('foo', Comment('bar'), 'skip')")

* Group(child, label?) - highlights its child with a dashed outline, and optionally labels it. Passing a string as the label constructs a Comment, or you can build one yourself (to give an href or title).

    ![Sequence("foo", Group(Choice(0, NonTerminal('option 1'), NonTerminal('or two')), "label"), "bar",)](https://github.com/tabatkins/railroad-diagrams/raw/gh-pages/images/rr-group.svg?sanitize=true "Sequence('foo', Group(Choice(0, NonTerminal('option 1'), NonTerminal('or two')), 'label'), 'bar',)")

After constructing a Diagram, call `.format(...padding)` on it, specifying 0-4 padding values (just like CSS) for some additional "breathing space" around the diagram (the paddings default to 20px).

The result can either be `.toString()`'d for the markup, or `.toSVG()`'d for an `<svg>` element, which can then be immediately inserted to the document.  As a convenience, Diagram also has an `.addTo(element)` method, which immediately converts it to SVG and appends it to the referenced element with default paddings. `element` defaults to `document.body`.

Options
-------

There are a few options you can tweak,
in an `Options` object exported from the module.
Just tweak either until the diagram looks like what you want.
You can also change the CSS file - feel free to tweak to your heart's content.
Note, though, that if you change the text sizes in the CSS,
you'll have to go adjust the options specifying the text metrics as well.

* `Options.VS` - sets the minimum amount of vertical separation between two items, in CSS px.  Note that the stroke width isn't counted when computing the separation; this shouldn't be relevant unless you have a very small separation or very large stroke width. Defaults to `8`.
* `Options.AR` - the radius of the arcs, in CSS px, used in the branching containers like Choice.  This has a relatively large effect on the size of non-trivial diagrams.  Both tight and loose values look good, depending on what you're going for. Defaults to `10`.
* `Options.DIAGRAM_CLASS` - the class set on the root `<svg>` element of each diagram, for use in the CSS stylesheet. Defaults to `"railroad-diagram"`.
* `Options.STROKE_ODD_PIXEL_LENGTH` - the default stylesheet uses odd pixel lengths for 'stroke'. Due to rasterization artifacts, they look best when the item has been translated half a pixel in both directions. If you change the styling to use a stroke with even pixel lengths, you'll want to set this variable to `False`.
* `Options.INTERNAL_ALIGNMENT` - when some branches of a container are narrower than others, this determines how they're aligned in the extra space.  Defaults to `"center"`, but can be set to `"left"` or `"right"`.
* `Options.CHAR_WIDTH` - the approximate width, in CSS px, of characters in normal text (`Terminal` and `NonTerminal`). Defaults to `8.5`.
* `Options.COMMENT_CHAR_WIDTH` - the approximate width, in CSS px, of character in `Comment` text, which by default is smaller than the other textual items. Defaults to `7`.
* `Options.DEBUG` - if `true`, writes some additional "debug information" into the attributes of elements in the output, to help debug sizing issues. Defaults to `false`.

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
