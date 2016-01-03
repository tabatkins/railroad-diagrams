Railroad-diagram Generator
==========================

![](images/rr-title.png "Diagram(Stack('Generate', 'some'), OneOrMore(NonTerminal('railroad diagrams'), Comment('and more')))")

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

To use the library, just include the js and css files, and then call the Diagram() function.
Its arguments are the components of the diagram (Diagram is a special form of Sequence).
An alternative to Diagram() is ComplexDiagram() which is used to describe a complex type diagram.
Components are either leaves or containers.

The leaves:
* Terminal(text, href) or a bare string - represents literal text. The 'href' attribute is optional, and creates a hyperlink with the given destination.
* NonTerminal(text, href) - represents an instruction or another production. The 'href' attribute is optional, and creates a hyperlink with the given destination.
* Comment(text, href) - a comment. The 'href' attribute is optional, and creates a hyperlink with the given destination.
* Skip() - an empty line

The containers:
* Sequence(children) - like simple concatenation in a regex

    ![Sequence('1', '2', '3')](images/rr-sequence.png "Sequence('1', '2', '3')")
* Stack(children) - identical to a Sequence, but the items are stacked vertically rather than horizontally

    ![Stack('1', '2', '3')](images/rr-stack.png "Stack('1', '2', '3')")
* OptionalSequence(children) - a Sequence where every item is *individually* optional, but at least one item must be chosen

    ![OptionalSequence('1', '2', '3')](images/rr-optseq.png "OptionalSequence('1', '2', '3')")
* Choice(index, children) - like `|` in a regex.  The index argument specifies which child is the "normal" choice and should go in the middle

    ![Choice(1, '1', '2', '3')](images/rr-choice.png "Choice(1, '1', '2', '3')")
* MultipleChoice(index, type, children) - like `||` or `&&` in a CSS grammar; it's similar to a Choice, but more than one branch can be taken.  The index argument specifies which child is the "normal" choice and should go in the middle, while the type argument must be either "any" (1+ branches can be taken) or "all" (all branches must be taken).

    ![MultipleChoice(1, 'all', '1', '2', '3')](images/rr-multchoice.png "MultipleChoice(1, 'all', '1', '2', '3')")
* Optional(child, skip) - like `?` in a regex.  A shorthand for `Choice(1, Skip(), child)`.  If the optional `skip` parameter has the value `"skip"`, it instead puts the Skip() in the straight-line path, for when the "normal" behavior is to omit the item.

    ![Optional('foo'), Optional('bar', 'skip'))](images/rr-optional.png "Optional('foo'), Optional('bar', 'skip'))")
* OneOrMore(child, repeat) - like `+` in a regex.  The 'repeat' argument is optional, and specifies something that must go between the repetitions.

    ![OneOrMore('foo', Comment('bar'))](images/rr-oneormore.png "OneOrMore('foo', Comment('bar'))")
* ZeroOrMore(child, repeat, skip) - like `*` in a regex.  A shorthand for `Optional(OneOrMore(child, repeat))`.  The optional `skip` parameter is identical to Optional().

    ![ZeroOrMore('foo', Comment('bar'))](images/rr-zeroormore.png "ZeroOrMore('foo', Comment('bar'))")

For convenience, each component can be called with or without `new`.
If called without `new`,
the container components become n-ary;
that is, you can say either `new Sequence([A, B])` or just `Sequence(A,B)`.

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

License
-------

This document and all associated files in the github project are licensed under [CC0](http://creativecommons.org/publicdomain/zero/1.0/) ![](http://i.creativecommons.org/p/zero/1.0/80x15.png).
This means you can reuse, remix, or otherwise appropriate this project for your own use **without restriction**.
(The actual legal meaning can be found at the above link.)
Don't ask me for permission to use any part of this project, **just use it**.
I would appreciate attribution, but that is not required by the license.
