# -*- coding: utf-8 -*-
from __future__ import annotations

import math as Math
import sys

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import (
        Any,
        Callable,
        Dict,
        Generator,
        List,
        Optional as Opt,
        Sequence as Seq,
        Tuple,
        Type,
        TypeVar,
        Union,
    )

    T = TypeVar("T")
    Node = Union[str, DiagramItem]  # pylint: disable=used-before-assignment
    WriterF = Callable[[str], Any]
    WalkerF = Callable[[DiagramItem], Any]  # pylint: disable=used-before-assignment
    AttrsT = Dict[str, Any]

# Display constants
DEBUG = False  # if true, writes some debug information into attributes
VS = 8  # minimum vertical separation between things. For a 3px stroke, must be at least 4
AR = 10  # radius of arcs
DIAGRAM_CLASS = "railroad-diagram"  # class to put on the root <svg>
STROKE_ODD_PIXEL_LENGTH = (
    True  # is the stroke width an odd (1px, 3px, etc) pixel length?
)
INTERNAL_ALIGNMENT = (
    "center"  # how to align items when they have extra space. left/right/center
)
CHAR_WIDTH = 8.5  # width of each monospace character. play until you find the right value for your font
COMMENT_CHAR_WIDTH = 7  # comments are in smaller text by default
ESCAPE_HTML = True  # Should Diagram.writeText() produce HTML-escaped text, or raw?


def escapeAttr(val: Union[str, float]) -> str:
    if isinstance(val, str):
        return val.replace("&", "&amp;").replace("'", "&apos;").replace('"', "&quot;")
    return f"{val:g}"


def escapeHtml(val: str) -> str:
    return escapeAttr(val).replace("<", "&lt;")


def determineGaps(outer: float, inner: float) -> Tuple[float, float]:
    diff = outer - inner
    if INTERNAL_ALIGNMENT == "left":
        return 0, diff
    elif INTERNAL_ALIGNMENT == "right":
        return diff, 0
    else:
        return diff / 2, diff / 2


def doubleenumerate(seq: Seq[T]) -> Generator[Tuple[int, int, T], None, None]:
    length = len(list(seq))
    for i, item in enumerate(seq):
        yield i, i - length, item


def addDebug(el: DiagramItem) -> None:
    if not DEBUG:
        return
    el.attrs["data-x"] = "{0} w:{1} h:{2}/{3}/{4}".format(
        type(el).__name__, el.width, el.up, el.height, el.down
    )


class DiagramItem:
    def __init__(self, name: str, attrs: Opt[AttrsT] = None, text: Opt[Node] = None):
        self.name = name
        # up = distance it projects above the entry line
        self.up: float = 0
        # height = distance between the entry/exit lines
        self.height: float = 0
        # down = distance it projects below the exit line
        self.down: float = 0
        # width = distance between the entry/exit lines horizontally
        self.width: float = 0
        # Whether the item is okay with being snug against another item or not
        self.needsSpace = False

        # DiagramItems pull double duty as SVG elements.
        self.attrs: AttrsT = attrs or {}
        # Subclasses store their meaningful children as .item or .items;
        # .children instead stores their formatted SVG nodes.
        self.children: List[Union[Node, Path, Style]] = [text] if text else []

    def format(self, x: float, y: float, width: float) -> DiagramItem:
        raise NotImplementedError  # Virtual

    def textDiagram() -> TextDiagram:
        raise NotImplementedError("Virtual")

    def addTo(self, parent: DiagramItem) -> DiagramItem:
        parent.children.append(self)
        return self

    def writeSvg(self, write: WriterF) -> None:
        write("<{0}".format(self.name))
        for name, value in sorted(self.attrs.items()):
            write(' {0}="{1}"'.format(name, escapeAttr(value)))
        write(">")
        if self.name in ["g", "svg"]:
            write("\n")
        for child in self.children:
            if isinstance(child, (DiagramItem, Path, Style)):
                child.writeSvg(write)
            else:
                write(escapeHtml(child))
        write("</{0}>".format(self.name))

    def walk(self, cb: WalkerF) -> None:
        cb(self)

    def __repr__(self) -> str:
        return f"DiagramItem({self.name}, {self.attrs}, {self.children})"


class DiagramMultiContainer(DiagramItem):
    def __init__(
        self,
        name: str,
        items: Seq[Node],
        attrs: Opt[Dict[str, str]] = None,
        text: Opt[str] = None,
    ):
        DiagramItem.__init__(self, name, attrs, text)
        self.items: List[DiagramItem] = [wrapString(item) for item in items]

    def format(self, x: float, y: float, width: float) -> DiagramItem:
        raise NotImplementedError  # Virtual

    def walk(self, cb: WalkerF) -> None:
        cb(self)
        for item in self.items:
            item.walk(cb)

    def __repr__(self) -> str:
        return f"DiagramMultiContainer({self.name}, {self.items}. {self.attrs}, {self.children})"


class Path:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.attrs = {"d": f"M{x} {y}"}

    def m(self, x: float, y: float) -> Path:
        self.attrs["d"] += f"m{x} {y}"
        return self

    def l(self, x: float, y: float) -> Path:
        self.attrs["d"] += f"l{x} {y}"
        return self

    def h(self, val: float) -> Path:
        self.attrs["d"] += f"h{val}"
        return self

    def right(self, val: float) -> Path:
        return self.h(max(0, val))

    def left(self, val: float) -> Path:
        return self.h(-max(0, val))

    def v(self, val: float) -> Path:
        self.attrs["d"] += f"v{val}"
        return self

    def down(self, val: float) -> Path:
        return self.v(max(0, val))

    def up(self, val: float) -> Path:
        return self.v(-max(0, val))

    def arc_8(self, start: str, dir: str) -> Path:
        # 1/8 of a circle
        arc = AR
        s2 = 1 / Math.sqrt(2) * arc
        s2inv = arc - s2
        sweep = "1" if dir == "cw" else "0"
        path = f"a {arc} {arc} 0 0 {sweep} "
        sd = start + dir
        offset: List[float]
        if sd == "ncw":
            offset = [s2, s2inv]
        elif sd == "necw":
            offset = [s2inv, s2]
        elif sd == "ecw":
            offset = [-s2inv, s2]
        elif sd == "secw":
            offset = [-s2, s2inv]
        elif sd == "scw":
            offset = [-s2, -s2inv]
        elif sd == "swcw":
            offset = [-s2inv, -s2]
        elif sd == "wcw":
            offset = [s2inv, -s2]
        elif sd == "nwcw":
            offset = [s2, -s2inv]
        elif sd == "nccw":
            offset = [-s2, s2inv]
        elif sd == "nwccw":
            offset = [-s2inv, s2]
        elif sd == "wccw":
            offset = [s2inv, s2]
        elif sd == "swccw":
            offset = [s2, s2inv]
        elif sd == "sccw":
            offset = [s2, -s2inv]
        elif sd == "seccw":
            offset = [s2inv, -s2]
        elif sd == "eccw":
            offset = [-s2inv, -s2]
        elif sd == "neccw":
            offset = [-s2, -s2inv]

        path += " ".join(str(x) for x in offset)
        self.attrs["d"] += path
        return self

    def arc(self, sweep: str) -> Path:
        x = AR
        y = AR
        if sweep[0] == "e" or sweep[1] == "w":
            x *= -1
        if sweep[0] == "s" or sweep[1] == "n":
            y *= -1
        cw = 1 if sweep in ("ne", "es", "sw", "wn") else 0
        self.attrs["d"] += f"a{AR} {AR} 0 0 {cw} {x} {y}"
        return self

    def addTo(self, parent: DiagramItem) -> Path:
        parent.children.append(self)
        return self

    def writeSvg(self, write: WriterF) -> None:
        write("<path")
        for name, value in sorted(self.attrs.items()):
            write(f' {name}="{escapeAttr(value)}"')
        write(" />")

    def format(self) -> Path:
        self.attrs["d"] += "h.5"
        return self

    def textDiagram(self) -> TextDiagram:
        return TextDiagram(0, 0, [])

    def __repr__(self) -> str:
        return f"Path({repr(self.x)}, {repr(self.y)})"


def wrapString(value: Node) -> DiagramItem:
    return value if isinstance(value, DiagramItem) else Terminal(value)


DEFAULT_STYLE = """\
	svg.railroad-diagram {
		background-color:hsl(30,20%,95%);
	}
	svg.railroad-diagram path {
		stroke-width:3;
		stroke:black;
		fill:rgba(0,0,0,0);
	}
	svg.railroad-diagram text {
		font:bold 14px monospace;
		text-anchor:middle;
	}
	svg.railroad-diagram text.label{
		text-anchor:start;
	}
	svg.railroad-diagram text.comment{
		font:italic 12px monospace;
	}
	svg.railroad-diagram rect{
		stroke-width:3;
		stroke:black;
		fill:hsl(120,100%,90%);
	}
	svg.railroad-diagram rect.group-box {
		stroke: gray;
		stroke-dasharray: 10 5;
		fill: none;
	}
"""


class Style:
    def __init__(self, css: str):
        self.css = css

    def __repr__(self) -> str:
        return f"Style({repr(self.css)})"

    def addTo(self, parent: DiagramItem) -> Style:
        parent.children.append(self)
        return self

    def format(self) -> Style:
        return self

    def textDiagram(self) -> TextDiagram:
        return TextDiagram(0, 0, [])

    def writeSvg(self, write: WriterF) -> None:
        # Write included stylesheet as CDATA. See https:#developer.mozilla.org/en-US/docs/Web/SVG/Element/style
        cdata = "/* <![CDATA[ */\n{css}\n/* ]]> */\n".format(css=self.css)
        write("<style>{cdata}</style>".format(cdata=cdata))


class Diagram(DiagramMultiContainer):
    def __init__(self, *items: Node, **kwargs: str):
        # Accepts a type=[simple|complex] kwarg
        DiagramMultiContainer.__init__(
            self,
            "svg",
            list(items),
            {
                "class": DIAGRAM_CLASS,
            },
        )
        self.type = kwargs.get("type", "simple")
        if items and not isinstance(items[0], Start):
            self.items.insert(0, Start(self.type))
        if items and not isinstance(items[-1], End):
            self.items.append(End(self.type))
        self.up = 0
        self.down = 0
        self.height = 0
        self.width = 0
        for item in self.items:
            if isinstance(item, Style):
                continue
            self.width += item.width + (20 if item.needsSpace else 0)
            self.up = max(self.up, item.up - self.height)
            self.height += item.height
            self.down = max(self.down - item.height, item.down)
        if self.items[0].needsSpace:
            self.width -= 10
        if self.items[-1].needsSpace:
            self.width -= 10
        self.formatted = False

    def __repr__(self) -> str:
        items = ", ".join(map(repr, self.items[1:-1]))
        pieces = [] if not items else [items]
        if self.type != "simple":
            pieces.append(f"type={repr(self.type)}")
        return f'Diagram({", ".join(pieces)})'

    def format(
        self,
        paddingTop: float = 20,
        paddingRight: Opt[float] = None,
        paddingBottom: Opt[float] = None,
        paddingLeft: Opt[float] = None,
    ) -> Diagram:
        if paddingRight is None:
            paddingRight = paddingTop
        if paddingBottom is None:
            paddingBottom = paddingTop
        if paddingLeft is None:
            paddingLeft = paddingRight
        assert paddingRight is not None
        assert paddingBottom is not None
        assert paddingLeft is not None
        x = paddingLeft
        y = paddingTop + self.up
        g = DiagramItem("g")
        if STROKE_ODD_PIXEL_LENGTH:
            g.attrs["transform"] = "translate(.5 .5)"
        for item in self.items:
            if item.needsSpace:
                Path(x, y).h(10).addTo(g)
                x += 10
            item.format(x, y, item.width).addTo(g)
            x += item.width
            y += item.height
            if item.needsSpace:
                Path(x, y).h(10).addTo(g)
                x += 10
        self.attrs["width"] = str(self.width + paddingLeft + paddingRight)
        self.attrs["height"] = str(
            self.up + self.height + self.down + paddingTop + paddingBottom
        )
        self.attrs["viewBox"] = f"0 0 {self.attrs['width']} {self.attrs['height']}"
        g.addTo(self)
        self.formatted = True
        return self

    def textDiagram(self) -> TextDiagram:
        (separator, ) = TextDiagram._getParts(["separator"])
        diagramTD = self.items[0].textDiagram()
        for item in self.items[1:]:
            itemTD = item.textDiagram()
            if item.needsSpace:
                itemTD = itemTD.expand(1, 1, 0, 0)
            diagramTD = diagramTD.appendRight(itemTD, separator)
        return diagramTD

    def writeSvg(self, write: WriterF) -> None:
        if not self.formatted:
            self.format()
        return DiagramItem.writeSvg(self, write)

    def writeText(self, write: WriterF) -> None:
        output = self.textDiagram()
        output = "\n".join(output.lines) + "\n"
        if ESCAPE_HTML:
            output = output.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
        write(output)

    def writeStandalone(self, write: WriterF, css: str | None = None) -> None:
        if not self.formatted:
            self.format()
        if css is None:
            css = DEFAULT_STYLE
        Style(css).addTo(self)
        self.attrs["xmlns"] = "http://www.w3.org/2000/svg"
        self.attrs['xmlns:xlink'] = "http://www.w3.org/1999/xlink"
        DiagramItem.writeSvg(self, write)
        self.children.pop()
        del self.attrs["xmlns"]
        del self.attrs["xmlns:xlink"]


class Sequence(DiagramMultiContainer):
    def __init__(self, *items: Node):
        DiagramMultiContainer.__init__(self, "g", items)
        self.needsSpace = True
        self.up = 0
        self.down = 0
        self.height = 0
        self.width = 0
        for item in self.items:
            self.width += item.width + (20 if item.needsSpace else 0)
            self.up = max(self.up, item.up - self.height)
            self.height += item.height
            self.down = max(self.down - item.height, item.down)
        if self.items[0].needsSpace:
            self.width -= 10
        if self.items[-1].needsSpace:
            self.width -= 10
        addDebug(self)

    def __repr__(self) -> str:
        items = ", ".join(repr(item) for item in self.items)
        return f"Sequence({items})"

    def format(self, x: float, y: float, width: float) -> Sequence:
        leftGap, rightGap = determineGaps(width, self.width)
        Path(x, y).h(leftGap).addTo(self)
        Path(x + leftGap + self.width, y + self.height).h(rightGap).addTo(self)
        x += leftGap
        for i, item in enumerate(self.items):
            if item.needsSpace and i > 0:
                Path(x, y).h(10).addTo(self)
                x += 10
            item.format(x, y, item.width).addTo(self)
            x += item.width
            y += item.height
            if item.needsSpace and i < len(self.items) - 1:
                Path(x, y).h(10).addTo(self)
                x += 10
        return self

    def textDiagram(self) -> TextDiagram:
        (separator, ) = TextDiagram._getParts(["separator"])
        diagramTD = TextDiagram(0, 0, [""])
        for item in self.items:
            itemTD = item.textDiagram()
            if item.needsSpace:
                itemTD = itemTD.expand(1, 1, 0, 0)
            diagramTD = diagramTD.appendRight(itemTD, separator)
        return diagramTD


class Stack(DiagramMultiContainer):
    def __init__(self, *items: Node):
        DiagramMultiContainer.__init__(self, "g", items)
        self.needsSpace = True
        self.width = max(
            item.width + (20 if item.needsSpace else 0) for item in self.items
        )
        # pretty sure that space calc is totes wrong
        if len(self.items) > 1:
            self.width += AR * 2
        self.up = self.items[0].up
        self.down = self.items[-1].down
        self.height = 0
        last = len(self.items) - 1
        for i, item in enumerate(self.items):
            self.height += item.height
            if i > 0:
                self.height += max(AR * 2, item.up + VS)
            if i < last:
                self.height += max(AR * 2, item.down + VS)
        addDebug(self)

    def __repr__(self) -> str:
        items = ", ".join(repr(item) for item in self.items)
        return f"Stack({items})"

    def format(self, x: float, y: float, width: float) -> Stack:
        leftGap, rightGap = determineGaps(width, self.width)
        Path(x, y).h(leftGap).addTo(self)
        x += leftGap
        xInitial = x
        if len(self.items) > 1:
            Path(x, y).h(AR).addTo(self)
            x += AR
            innerWidth = self.width - AR * 2
        else:
            innerWidth = self.width
        for i, item in enumerate(self.items):
            item.format(x, y, innerWidth).addTo(self)
            x += innerWidth
            y += item.height
            if i != len(self.items) - 1:
                (
                    Path(x, y)
                    .arc("ne")
                    .down(max(0, item.down + VS - AR * 2))
                    .arc("es")
                    .left(innerWidth)
                    .arc("nw")
                    .down(max(0, self.items[i + 1].up + VS - AR * 2))
                    .arc("ws")
                    .addTo(self)
                )
                y += max(item.down + VS, AR * 2) + max(
                    self.items[i + 1].up + VS, AR * 2
                )
                x = xInitial + AR
        if len(self.items) > 1:
            Path(x, y).h(AR).addTo(self)
            x += AR
        Path(x, y).h(rightGap).addTo(self)
        return self

    def textDiagram(self) -> TextDiagram:
        corner_bot_left, corner_bot_right, corner_top_left, corner_top_right, line, line_vertical = TextDiagram._getParts(["corner_bot_left", "corner_bot_right", "corner_top_left", "corner_top_right", "line", "line_vertical"])

        # Format all the child items, so we can know the maximum width.
        itemTDs = []
        for item in self.items:
            itemTDs.append(item.textDiagram())
        maxWidth = max([itemTD.width for itemTD in itemTDs])

        leftLines = []
        rightLines = []
        separatorTD = TextDiagram(0, 0, [line * maxWidth])
        diagramTD = None  # Top item will replace it.

        for itemNum, itemTD in enumerate(itemTDs):
            if itemNum == 0:
                # The top item enters directly from its left.
                leftLines += [line * 2]
                leftLines += [" " * 2] * (itemTD.height - itemTD.entry - 1)
            else:
                # All items below the top enter from a snake-line from the previous item's exit.
                # Here, we resume that line, already having descended from above on the right.
                diagramTD = diagramTD.appendBelow(separatorTD, [])
                leftLines += [corner_top_left + line]
                leftLines += [line_vertical + " "] * (itemTD.entry)
                leftLines += [corner_bot_left + line]
                leftLines += [" " * 2] * (itemTD.height - itemTD.entry - 1)
                rightLines += [" " * 2] * (itemTD.exit)
            if itemNum < len(itemTDs) - 1:
                # All items above the bottom exit via a snake-line to the next item's entry.
                # Here, we start that line on the right.
                rightLines += [line + corner_top_right]
                rightLines += [" " + line_vertical] * (itemTD.height - itemTD.exit - 1)
                rightLines += [line + corner_bot_right]
            else:
                # The bottom item exits directly to its right.
                rightLines += [line * 2]
            leftPad, rightPad = TextDiagram._gaps(maxWidth, itemTD.width)
            itemTD = itemTD.expand(leftPad, rightPad, 0, 0)
            if itemNum == 0:
                diagramTD = itemTD
            else:
                diagramTD = diagramTD.appendBelow(itemTD, [])

        leftTD = TextDiagram(0, 0, leftLines)
        diagramTD = leftTD.appendRight(diagramTD, "")
        rightTD = TextDiagram(0, len(rightLines) - 1, rightLines)
        diagramTD = diagramTD.appendRight(rightTD, "")
        return diagramTD


class OptionalSequence(DiagramMultiContainer):
    def __new__(cls, *items: Node) -> Any:
        if len(items) <= 1:
            return Sequence(*items)
        else:
            return super(OptionalSequence, cls).__new__(cls)

    def __init__(self, *items: Node):
        DiagramMultiContainer.__init__(self, "g", items)
        self.needsSpace = False
        self.width = 0
        self.up = 0
        self.height = sum(item.height for item in self.items)
        self.down = self.items[0].down
        heightSoFar: float = 0
        for i, item in enumerate(self.items):
            self.up = max(self.up, max(AR * 2, item.up + VS) - heightSoFar)
            heightSoFar += item.height
            if i > 0:
                self.down = (
                    max(
                        self.height + self.down,
                        heightSoFar + max(AR * 2, item.down + VS),
                    )
                    - self.height
                )
            itemWidth = item.width + (10 if item.needsSpace else 0)
            if i == 0:
                self.width += AR + max(itemWidth, AR)
            else:
                self.width += AR * 2 + max(itemWidth, AR) + AR
        addDebug(self)

    def __repr__(self) -> str:
        items = ", ".join(repr(item) for item in self.items)
        return f"OptionalSequence({items})"

    def format(self, x: float, y: float, width: float) -> OptionalSequence:
        leftGap, rightGap = determineGaps(width, self.width)
        Path(x, y).right(leftGap).addTo(self)
        Path(x + leftGap + self.width, y + self.height).right(rightGap).addTo(self)
        x += leftGap
        upperLineY = y - self.up
        last = len(self.items) - 1
        for i, item in enumerate(self.items):
            itemSpace = 10 if item.needsSpace else 0
            itemWidth = item.width + itemSpace
            if i == 0:
                # Upper skip
                (
                    Path(x, y)
                    .arc("se")
                    .up(y - upperLineY - AR * 2)
                    .arc("wn")
                    .right(itemWidth - AR)
                    .arc("ne")
                    .down(y + item.height - upperLineY - AR * 2)
                    .arc("ws")
                    .addTo(self)
                )
                # Straight line
                (Path(x, y).right(itemSpace + AR).addTo(self))
                item.format(x + itemSpace + AR, y, item.width).addTo(self)
                x += itemWidth + AR
                y += item.height
            elif i < last:
                # Upper skip
                (
                    Path(x, upperLineY)
                    .right(AR * 2 + max(itemWidth, AR) + AR)
                    .arc("ne")
                    .down(y - upperLineY + item.height - AR * 2)
                    .arc("ws")
                    .addTo(self)
                )
                # Straight line
                (Path(x, y).right(AR * 2).addTo(self))
                item.format(x + AR * 2, y, item.width).addTo(self)
                (
                    Path(x + item.width + AR * 2, y + item.height)
                    .right(itemSpace + AR)
                    .addTo(self)
                )
                # Lower skip
                (
                    Path(x, y)
                    .arc("ne")
                    .down(item.height + max(item.down + VS, AR * 2) - AR * 2)
                    .arc("ws")
                    .right(itemWidth - AR)
                    .arc("se")
                    .up(item.down + VS - AR * 2)
                    .arc("wn")
                    .addTo(self)
                )
                x += AR * 2 + max(itemWidth, AR) + AR
                y += item.height
            else:
                # Straight line
                (Path(x, y).right(AR * 2).addTo(self))
                item.format(x + AR * 2, y, item.width).addTo(self)
                (
                    Path(x + AR * 2 + item.width, y + item.height)
                    .right(itemSpace + AR)
                    .addTo(self)
                )
                # Lower skip
                (
                    Path(x, y)
                    .arc("ne")
                    .down(item.height + max(item.down + VS, AR * 2) - AR * 2)
                    .arc("ws")
                    .right(itemWidth - AR)
                    .arc("se")
                    .up(item.down + VS - AR * 2)
                    .arc("wn")
                    .addTo(self)
                )
        return self

    def textDiagram(self) -> TextDiagram:
        line, line_vertical, roundcorner_bot_left, roundcorner_bot_right, roundcorner_top_left, roundcorner_top_right = TextDiagram._getParts(["line", "line_vertical", "roundcorner_bot_left", "roundcorner_bot_right", "roundcorner_top_left", "roundcorner_top_right"])

        # Format all the child items, so we can know the maximum entry.
        itemTDs = []
        for item in self.items:
            itemTDs.append(item.textDiagram())
        # diagramEntry: distance from top to lowest entry, aka distance from top to diagram entry, aka final diagram entry and exit.
        diagramEntry = max([itemTD.entry for itemTD in itemTDs])
        # SOILHeight: distance from top to lowest entry before rightmost item, aka distance from skip-over-items line to rightmost entry, aka SOIL height.
        SOILHeight = max([itemTD.entry for itemTD in itemTDs[:-1]])
        # topToSOIL: distance from top to skip-over-items line.
        topToSOIL = diagramEntry - SOILHeight

        # The diagram starts with a line from its entry up to the skip-over-items line:
        lines = [" " * 2] * topToSOIL
        lines += [roundcorner_top_left + line]
        lines += [line_vertical + " "] * SOILHeight
        lines += [roundcorner_bot_right + line]
        diagramTD = TextDiagram(len(lines) - 1, len(lines) - 1, lines)
        for itemNum, itemTD in enumerate(itemTDs):
            if itemNum > 0:
                # All items except the leftmost start with a line from their entry down to their skip-under-item line,
                # with a joining-line across at the skip-over-items line:
                lines = []
                lines += [" " * 2] * topToSOIL
                lines += [line * 2]
                lines += [" " * 2] * (diagramTD.exit - topToSOIL - 1)
                lines += [line + roundcorner_top_right]
                lines += [" " + line_vertical] * (itemTD.height - itemTD.entry - 1)
                lines += [" " + roundcorner_bot_left]
                skipDownTD = TextDiagram(diagramTD.exit, diagramTD.exit, lines)
                diagramTD = diagramTD.appendRight(skipDownTD, "")
                # All items except the leftmost next have a line from skip-over-items line down to their entry,
                # with joining-lines at their entry and at their skip-under-item line:
                lines = []
                lines += [" " * 2] * topToSOIL
                # All such items except the rightmost also have a continuation of the skip-over-items line:
                lineToNextItem = line if itemNum < len(itemTDs) - 1 else " "
                lines += [line + roundcorner_top_right + lineToNextItem]
                lines += [" " + line_vertical + " "] * (diagramTD.exit - topToSOIL - 1)
                lines += [line + roundcorner_bot_left + line]
                lines += [" " * 3] * (itemTD.height - itemTD.entry - 1)
                lines += [line * 3]
                entryTD = TextDiagram(diagramTD.exit, diagramTD.exit, lines)
                diagramTD = diagramTD.appendRight(entryTD, "")
            partTD = TextDiagram(0, 0, [])
            if itemNum < len(itemTDs) - 1:
                # All items except the rightmost have a segment of the skip-over-items line at the top,
                # followed by enough blank lines to push their entry down to the previous item's exit:
                lines = []
                lines += [line * itemTD.width]
                lines += [" " * itemTD.width] * (SOILHeight - itemTD.entry)
                SOILSegment = TextDiagram(0, 0, lines)
                partTD = partTD.appendBelow(SOILSegment, [])
            partTD = partTD.appendBelow(itemTD, [], moveEntry=True, moveExit=True)
            if itemNum > 0:
                # All items except the leftmost have their skip-under-item line at the bottom.
                SUILSegment = TextDiagram(0, 0, [line * itemTD.width])
                partTD = partTD.appendBelow(SUILSegment, [])
            diagramTD = diagramTD.appendRight(partTD, "")
            if 0 < itemNum:
                # All items except the leftmost have a line from their skip-under-item line to their exit:
                lines = []
                lines += [" " * 2] * topToSOIL
                # All such items except the rightmost also have a joining-line across at the skip-over-items line:
                skipOverChar = line if itemNum < len(itemTDs) - 1 else " "
                lines += [skipOverChar * 2]
                lines += [" " * 2] * (diagramTD.exit - topToSOIL - 1)
                lines += [line + roundcorner_top_left]
                lines += [" " + line_vertical] * (partTD.height - partTD.exit - 2)
                lines += [line + roundcorner_bot_right]
                skipUpTD = TextDiagram(diagramTD.exit, diagramTD.exit, lines)
                diagramTD = diagramTD.appendRight(skipUpTD, "")
        return diagramTD


class AlternatingSequence(DiagramMultiContainer):
    def __new__(cls, *items: Node) -> AlternatingSequence:
        if len(items) == 2:
            return super(AlternatingSequence, cls).__new__(cls)
        else:
            raise Exception(
                "AlternatingSequence takes exactly two arguments, but got {0} arguments.".format(
                    len(items)
                )
            )

    def __init__(self, *items: Node):
        DiagramMultiContainer.__init__(self, "g", items)
        self.needsSpace = False

        arc = AR
        vert = VS
        first = self.items[0]
        second = self.items[1]

        arcX = 1 / Math.sqrt(2) * arc * 2
        arcY = (1 - 1 / Math.sqrt(2)) * arc * 2
        crossY = max(arc, vert)
        crossX = (crossY - arcY) + arcX

        firstOut = max(
            arc + arc, crossY / 2 + arc + arc, crossY / 2 + vert + first.down
        )
        self.up = firstOut + first.height + first.up

        secondIn = max(arc + arc, crossY / 2 + arc + arc, crossY / 2 + vert + second.up)
        self.down = secondIn + second.height + second.down

        self.height = 0

        firstWidth = (20 if first.needsSpace else 0) + first.width
        secondWidth = (20 if second.needsSpace else 0) + second.width
        self.width = 2 * arc + max(firstWidth, crossX, secondWidth) + 2 * arc
        addDebug(self)

    def __repr__(self) -> str:
        items = ", ".join(repr(item) for item in self.items)
        return f"AlternatingSequence({items})"

    def format(self, x: float, y: float, width: float) -> AlternatingSequence:
        arc = AR
        gaps = determineGaps(width, self.width)
        Path(x, y).right(gaps[0]).addTo(self)
        x += gaps[0]
        Path(x + self.width, y).right(gaps[1]).addTo(self)
        # bounding box
        # Path(x+gaps[0], y).up(self.up).right(self.width).down(self.up+self.down).left(self.width).up(self.down).addTo(self)
        first = self.items[0]
        second = self.items[1]

        # top
        firstIn = self.up - first.up
        firstOut = self.up - first.up - first.height
        Path(x, y).arc("se").up(firstIn - 2 * arc).arc("wn").addTo(self)
        first.format(x + 2 * arc, y - firstIn, self.width - 4 * arc).addTo(self)
        Path(x + self.width - 2 * arc, y - firstOut).arc("ne").down(
            firstOut - 2 * arc
        ).arc("ws").addTo(self)

        # bottom
        secondIn = self.down - second.down - second.height
        secondOut = self.down - second.down
        Path(x, y).arc("ne").down(secondIn - 2 * arc).arc("ws").addTo(self)
        second.format(x + 2 * arc, y + secondIn, self.width - 4 * arc).addTo(self)
        Path(x + self.width - 2 * arc, y + secondOut).arc("se").up(
            secondOut - 2 * arc
        ).arc("wn").addTo(self)

        # crossover
        arcX = 1 / Math.sqrt(2) * arc * 2
        arcY = (1 - 1 / Math.sqrt(2)) * arc * 2
        crossY = max(arc, VS)
        crossX = (crossY - arcY) + arcX
        crossBar = (self.width - 4 * arc - crossX) / 2
        (
            Path(x + arc, y - crossY / 2 - arc)
            .arc("ws")
            .right(crossBar)
            .arc_8("n", "cw")
            .l(crossX - arcX, crossY - arcY)
            .arc_8("sw", "ccw")
            .right(crossBar)
            .arc("ne")
            .addTo(self)
        )
        (
            Path(x + arc, y + crossY / 2 + arc)
            .arc("wn")
            .right(crossBar)
            .arc_8("s", "ccw")
            .l(crossX - arcX, -(crossY - arcY))
            .arc_8("nw", "cw")
            .right(crossBar)
            .arc("se")
            .addTo(self)
        )

        return self

    def textDiagram(self) -> TextDiagram:
        cross_diag, corner_bot_left, corner_bot_right, corner_top_left, corner_top_right, line, line_vertical, tee_left, tee_right = TextDiagram._getParts(["cross_diag", "roundcorner_bot_left", "roundcorner_bot_right", "roundcorner_top_left", "roundcorner_top_right", "line", "line_vertical", "tee_left", "tee_right"])

        firstTD = self.items[0].textDiagram()
        secondTD = self.items[1].textDiagram()
        maxWidth = TextDiagram._maxWidth(firstTD, secondTD)
        leftWidth, rightWidth = TextDiagram._gaps(maxWidth, 0)
        leftLines = []
        rightLines = []
        separator = []
        leftSize, rightSize = TextDiagram._gaps(firstTD.width, 0)
        diagramTD = firstTD.expand(leftWidth - leftSize, rightWidth - rightSize, 0, 0)
        leftLines += [" " * 2] * (diagramTD.entry)
        leftLines += [corner_top_left + line]
        leftLines += [line_vertical + " "] * (diagramTD.height - diagramTD.entry - 1)
        leftLines += [corner_bot_left + line]
        rightLines += [" " * 2] * (diagramTD.entry)
        rightLines += [line + corner_top_right]
        rightLines += [" " + line_vertical] * (diagramTD.height - diagramTD.entry - 1)
        rightLines += [line + corner_bot_right]

        separator += [(line * (leftWidth - 1)) + corner_top_right + " " + corner_top_left + (line * (rightWidth - 2))]
        separator += [(" " * (leftWidth - 1)) + " " + cross_diag + " " + (" " * (rightWidth - 2))]
        separator += [(line * (leftWidth - 1)) + corner_bot_right + " " + corner_bot_left + (line * (rightWidth - 2))]
        leftLines += [" " * 2]
        rightLines += [" " * 2]

        leftSize, rightSize = TextDiagram._gaps(secondTD.width, 0)
        secondTD = secondTD.expand(leftWidth - leftSize, rightWidth - rightSize, 0, 0)
        diagramTD = diagramTD.appendBelow(secondTD, separator, moveEntry=True, moveExit=True)
        leftLines += [corner_top_left + line]
        leftLines += [line_vertical + " "] * secondTD.entry
        leftLines += [corner_bot_left + line]
        rightLines += [line + corner_top_right]
        rightLines += [" " + line_vertical] * secondTD.entry
        rightLines += [line + corner_bot_right]

        diagramTD = diagramTD.alter(entry=firstTD.height + (len(separator) // 2), exit=firstTD.height + (len(separator) // 2))
        leftTD = TextDiagram(firstTD.height + (len(separator) // 2), firstTD.height + (len(separator) // 2), leftLines)
        rightTD = TextDiagram(firstTD.height + (len(separator) // 2), firstTD.height + (len(separator) // 2), rightLines)
        diagramTD = leftTD.appendRight(diagramTD, "").appendRight(rightTD, "")
        diagramTD = TextDiagram(1, 1, [corner_top_left, tee_left, corner_bot_left]).appendRight(diagramTD, "").appendRight(TextDiagram(1, 1, [corner_top_right, tee_right, corner_bot_right]), "")
        return diagramTD


class Choice(DiagramMultiContainer):
    def __init__(self, default: int, *items: Node):
        DiagramMultiContainer.__init__(self, "g", items)
        assert default < len(items)
        self.default = default
        self.width = AR * 4 + max(item.width for item in self.items)

        # The size of the vertical separation between an item
        # and the following item.
        # The calcs are non-trivial and need to be done both here
        # and in .format(), so no reason to do it twice.
        self.separators: list[int] = [VS] * (len(items) - 1)

        # If the entry or exit lines would be too close together
        # to accommodate the arcs,
        # bump up the vertical separation to compensate.
        self.up = 0
        for i in range(default - 1, -1, -1):
            if i == default-1:
                arcs = AR * 2
            else:
                arcs = AR

            item = self.items[i]
            lowerItem = self.items[i+1]

            entryDelta = lowerItem.up + VS + item.down + item.height
            exitDelta = lowerItem.height + lowerItem.up + VS + item.down

            separator = VS
            if exitDelta < arcs or entryDelta < arcs:
                separator += max(arcs - entryDelta, arcs - exitDelta)
            self.separators[i] = separator
            self.up += lowerItem.up + separator + item.down + item.height
        self.up += self.items[0].up

        self.height = self.items[default].height

        for i in range(default+1, len(self.items)):
            if i == default+1:
                arcs = AR * 2
            else:
                arcs = AR

            item = self.items[i]
            upperItem = self.items[i-1]

            entryDelta = upperItem.height + upperItem.down + VS + item.up
            exitDelta = upperItem.down + VS + item.up + item.height

            separator = VS
            if entryDelta < arcs or exitDelta < arcs:
                separator += max(arcs - entryDelta, arcs - exitDelta)
            self.separators[i-1] = separator
            self.down += upperItem.down + separator + item.up + item.height
        self.down += self.items[-1].down
        addDebug(self)

    def __repr__(self) -> str:
        items = ", ".join(repr(item) for item in self.items)
        return f"Choice({self.default}, {items})"

    def format(self, x: float, y: float, width: float) -> Choice:
        leftGap, rightGap = determineGaps(width, self.width)

        # Hook up the two sides if self is narrower than its stated width.
        Path(x, y).h(leftGap).addTo(self)
        Path(x + leftGap + self.width, y + self.height).h(rightGap).addTo(self)
        x += leftGap

        innerWidth = self.width - AR * 4
        default = self.items[self.default]

        # Do the elements that curve above
        distanceFromY = 0
        for i in range(self.default - 1, -1, -1):
            item = self.items[i]
            lowerItem = self.items[i+1]
            distanceFromY += lowerItem.up + self.separators[i] + item.down + item.height
            Path(x, y).arc("se").up(distanceFromY - AR * 2).arc("wn").addTo(self)
            item.format(x + AR * 2, y - distanceFromY, innerWidth).addTo(self)
            Path(x + AR * 2 + innerWidth, y - distanceFromY + item.height).arc(
                "ne"
            ).down(distanceFromY - item.height + default.height - AR * 2).arc(
                "ws"
            ).addTo(
                self
            )

        # Do the straight-line path.
        Path(x, y).right(AR * 2).addTo(self)
        self.items[self.default].format(x + AR * 2, y, innerWidth).addTo(self)
        Path(x + AR * 2 + innerWidth, y + self.height).right(AR * 2).addTo(self)

        # Do the elements that curve below
        distanceFromY = 0
        for i in range(self.default+1, len(self.items)):
            item = self.items[i]
            upperItem = self.items[i-1]
            distanceFromY += upperItem.height + upperItem.down + self.separators[i-1] + item.up
            Path(x, y).arc("ne").down(distanceFromY - AR * 2).arc("ws").addTo(self)
            item.format(x + AR * 2, y + distanceFromY, innerWidth).addTo(self)
            Path(x + AR * 2 + innerWidth, y + distanceFromY + item.height).arc("se").up(
                distanceFromY - AR * 2 + item.height - default.height
            ).arc("wn").addTo(self)

        return self

    def textDiagram(self) -> TextDiagram:
        cross, line, line_vertical, roundcorner_bot_left, roundcorner_bot_right, roundcorner_top_left, roundcorner_top_right = TextDiagram._getParts(["cross", "line", "line_vertical", "roundcorner_bot_left", "roundcorner_bot_right", "roundcorner_top_left", "roundcorner_top_right"])
        # Format all the child items, so we can know the maximum width.
        itemTDs = []
        for item in self.items:
            itemTDs.append(item.textDiagram().expand(1, 1, 0, 0))
        max_item_width = max([i.width for i in itemTDs])
        diagramTD = TextDiagram(0, 0, [])
        # Format the choice collection.
        for itemNum, itemTD in enumerate(itemTDs):
            leftPad, rightPad = TextDiagram._gaps(max_item_width, itemTD.width)
            itemTD = itemTD.expand(leftPad, rightPad, 0, 0)
            hasSeparator = True
            leftLines = [line_vertical] * itemTD.height
            rightLines = [line_vertical] * itemTD.height
            moveEntry = False
            moveExit = False
            if itemNum <= self.default:
                # Item above the line: round off the entry/exit lines upwards.
                leftLines[itemTD.entry] = roundcorner_top_left
                rightLines[itemTD.exit] = roundcorner_top_right
                if itemNum == 0:
                    # First item and above the line: also remove ascenders above the item's entry and exit, suppress the separator above it.
                    hasSeparator = False
                    for i in range(0, itemTD.entry):
                        leftLines[i] = " "
                    for i in range(0, itemTD.exit):
                        rightLines[i] = " "
            if itemNum >= self.default:
                # Item below the line: round off the entry/exit lines downwards.
                leftLines[itemTD.entry] = roundcorner_bot_left
                rightLines[itemTD.exit] = roundcorner_bot_right
                if itemNum == 0:
                    # First item and below the line: also suppress the separator above it.
                    hasSeparator = False
                if itemNum == (len(self.items) - 1):
                    # Last item and below the line: also remove descenders below the item's entry and exit
                    for i in range(itemTD.entry + 1, itemTD.height):
                        leftLines[i] = " "
                    for i in range(itemTD.exit + 1, itemTD.height):
                        rightLines[i] = " "
            if itemNum == self.default:
                # Item on the line: entry/exit are horizontal, and sets the outer entry/exit.
                leftLines[itemTD.entry] = cross
                rightLines[itemTD.exit] = cross
                moveEntry = True
                moveExit = True
                if itemNum == 0 and itemNum == (len(self.items) - 1):
                    # Only item and on the line: set entry/exit for straight through.
                    leftLines[itemTD.entry] = line
                    rightLines[itemTD.exit] = line
                elif itemNum == 0:
                    # First item and on the line: set entry/exit for no ascenders.
                    leftLines[itemTD.entry] = roundcorner_top_right
                    rightLines[itemTD.exit] = roundcorner_top_left
                elif itemNum == (len(self.items) - 1):
                    # Last item and on the line: set entry/exit for no descenders.
                    leftLines[itemTD.entry] = roundcorner_bot_right
                    rightLines[itemTD.exit] = roundcorner_bot_left
            leftJointTD = TextDiagram(itemTD.entry, itemTD.entry, leftLines)
            rightJointTD = TextDiagram(itemTD.exit, itemTD.exit, rightLines)
            itemTD = leftJointTD.appendRight(itemTD, "").appendRight(rightJointTD, "")
            separator = [line_vertical + (" " * (TextDiagram._maxWidth(diagramTD, itemTD) - 2)) + line_vertical] if hasSeparator else []
            diagramTD = diagramTD.appendBelow(itemTD, separator, moveEntry=moveEntry, moveExit=moveExit)
        return diagramTD


class MultipleChoice(DiagramMultiContainer):
    def __init__(self, default: int, type: str, *items: Node):
        DiagramMultiContainer.__init__(self, "g", items)
        assert 0 <= default < len(items)
        assert type in ["any", "all"]
        self.default = default
        self.type = type
        self.needsSpace = True
        self.innerWidth = max(item.width for item in self.items)
        self.width = 30 + AR + self.innerWidth + AR + 20
        self.up = self.items[0].up
        self.down = self.items[-1].down
        self.height = self.items[default].height
        for i, item in enumerate(self.items):
            if i in [default - 1, default + 1]:
                minimum = 10 + AR
            else:
                minimum = AR
            if i < default:
                self.up += max(
                    minimum, item.height + item.down + VS + self.items[i + 1].up
                )
            elif i == default:
                continue
            else:
                self.down += max(
                    minimum,
                    item.up + VS + self.items[i - 1].down + self.items[i - 1].height,
                )
        self.down -= self.items[default].height  # already counted in self.height
        addDebug(self)

    def __repr__(self) -> str:
        items = ", ".join(repr(item) for item in self.items)
        return f"MultipleChoice({repr(self.default)}, {repr(self.type)}, {items})"

    def format(self, x: float, y: float, width: float) -> MultipleChoice:
        leftGap, rightGap = determineGaps(width, self.width)

        # Hook up the two sides if self is narrower than its stated width.
        Path(x, y).h(leftGap).addTo(self)
        Path(x + leftGap + self.width, y + self.height).h(rightGap).addTo(self)
        x += leftGap

        default = self.items[self.default]

        # Do the elements that curve above
        above = self.items[: self.default][::-1]
        if above:
            distanceFromY = max(
                10 + AR, default.up + VS + above[0].down + above[0].height
            )
        for i, ni, item in doubleenumerate(above):
            (Path(x + 30, y).up(distanceFromY - AR).arc("wn").addTo(self))
            item.format(x + 30 + AR, y - distanceFromY, self.innerWidth).addTo(self)
            (
                Path(x + 30 + AR + self.innerWidth, y - distanceFromY + item.height)
                .arc("ne")
                .down(distanceFromY - item.height + default.height - AR - 10)
                .addTo(self)
            )
            if ni < -1:
                distanceFromY += max(
                    AR, item.up + VS + above[i + 1].down + above[i + 1].height
                )

        # Do the straight-line path.
        Path(x + 30, y).right(AR).addTo(self)
        self.items[self.default].format(x + 30 + AR, y, self.innerWidth).addTo(self)
        Path(x + 30 + AR + self.innerWidth, y + self.height).right(AR).addTo(self)

        # Do the elements that curve below
        below = self.items[self.default + 1 :]
        if below:
            distanceFromY = max(
                10 + AR, default.height + default.down + VS + below[0].up
            )
        for i, item in enumerate(below):
            (Path(x + 30, y).down(distanceFromY - AR).arc("ws").addTo(self))
            item.format(x + 30 + AR, y + distanceFromY, self.innerWidth).addTo(self)
            (
                Path(x + 30 + AR + self.innerWidth, y + distanceFromY + item.height)
                .arc("se")
                .up(distanceFromY - AR + item.height - default.height - 10)
                .addTo(self)
            )
            distanceFromY += max(
                AR,
                item.height
                + item.down
                + VS
                + (below[i + 1].up if i + 1 < len(below) else 0),
            )
        text = DiagramItem("g", attrs={"class": "diagram-text"}).addTo(self)
        DiagramItem(
            "title",
            text="take one or more branches, once each, in any order"
            if self.type == "any"
            else "take all branches, once each, in any order",
        ).addTo(text)
        DiagramItem(
            "path",
            attrs={
                "d": "M {x} {y} h -26 a 4 4 0 0 0 -4 4 v 12 a 4 4 0 0 0 4 4 h 26 z".format(
                    x=x + 30, y=y - 10
                ),
                "class": "diagram-text",
            },
        ).addTo(text)
        DiagramItem(
            "text",
            text="1+" if self.type == "any" else "all",
            attrs={"x": x + 15, "y": y + 4, "class": "diagram-text"},
        ).addTo(text)
        DiagramItem(
            "path",
            attrs={
                "d": "M {x} {y} h 16 a 4 4 0 0 1 4 4 v 12 a 4 4 0 0 1 -4 4 h -16 z".format(
                    x=x + self.width - 20, y=y - 10
                ),
                "class": "diagram-text",
            },
        ).addTo(text)
        DiagramItem(
            "text",
            text="↺",
            attrs={"x": x + self.width - 10, "y": y + 4, "class": "diagram-arrow"},
        ).addTo(text)
        return self

    def textDiagram(self) -> TextDiagram:
        (multi_repeat,) = TextDiagram._getParts(["multi_repeat"])
        anyAll = TextDiagram.rect("1+" if self.type == "any" else "all")
        diagramTD = Choice.textDiagram(self)
        repeatTD = TextDiagram.rect(multi_repeat)
        diagramTD = anyAll.appendRight(diagramTD, "")
        diagramTD = diagramTD.appendRight(repeatTD, "")
        return diagramTD


class HorizontalChoice(DiagramMultiContainer):
    def __new__(cls, *items: Node) -> Any:
        if len(items) <= 1:
            return Sequence(*items)
        else:
            return super(HorizontalChoice, cls).__new__(cls)

    def __init__(self, *items: Node):
        DiagramMultiContainer.__init__(self, "g", items)
        allButLast = self.items[:-1]
        middles = self.items[1:-1]
        first = self.items[0]
        last = self.items[-1]
        self.needsSpace = False

        self.width = (
            AR  # starting track
            + AR * 2 * (len(self.items) - 1)  # inbetween tracks
            + sum(x.width + (20 if x.needsSpace else 0) for x in self.items)  # items
            + (AR if last.height > 0 else 0)  # needs space to curve up
            + AR
        )  # ending track

        # Always exits at entrance height
        self.height = 0

        # All but the last have a track running above them
        self._upperTrack = max(AR * 2, VS, max(x.up for x in allButLast) + VS)
        self.up = max(self._upperTrack, last.up)

        # All but the first have a track running below them
        # Last either straight-lines or curves up, so has different calculation
        self._lowerTrack = max(
            VS,
            max(x.height + max(x.down + VS, AR * 2) for x in middles) if middles else 0,
            last.height + last.down + VS,
        )
        if first.height < self._lowerTrack:
            # Make sure there's at least 2*AR room between first exit and lower track
            self._lowerTrack = max(self._lowerTrack, first.height + AR * 2)
        self.down = max(self._lowerTrack, first.height + first.down)

        addDebug(self)

    def format(self, x: float, y: float, width: float) -> HorizontalChoice:
        # Hook up the two sides if self is narrower than its stated width.
        leftGap, rightGap = determineGaps(width, self.width)
        Path(x, y).h(leftGap).addTo(self)
        Path(x + leftGap + self.width, y + self.height).h(rightGap).addTo(self)
        x += leftGap

        first = self.items[0]
        last = self.items[-1]

        # upper track
        upperSpan = (
            sum(x.width + (20 if x.needsSpace else 0) for x in self.items[:-1])
            + (len(self.items) - 2) * AR * 2
            - AR
        )
        (
            Path(x, y)
            .arc("se")
            .up(self._upperTrack - AR * 2)
            .arc("wn")
            .h(upperSpan)
            .addTo(self)
        )

        # lower track
        lowerSpan = (
            sum(x.width + (20 if x.needsSpace else 0) for x in self.items[1:])
            + (len(self.items) - 2) * AR * 2
            + (AR if last.height > 0 else 0)
            - AR
        )
        lowerStart = x + AR + first.width + (20 if first.needsSpace else 0) + AR * 2
        (
            Path(lowerStart, y + self._lowerTrack)
            .h(lowerSpan)
            .arc("se")
            .up(self._lowerTrack - AR * 2)
            .arc("wn")
            .addTo(self)
        )

        # Items
        for [i, item] in enumerate(self.items):
            # input track
            if i == 0:
                (Path(x, y).h(AR).addTo(self))
                x += AR
            else:
                (
                    Path(x, y - self._upperTrack)
                    .arc("ne")
                    .v(self._upperTrack - AR * 2)
                    .arc("ws")
                    .addTo(self)
                )
                x += AR * 2

            # item
            itemWidth = item.width + (20 if item.needsSpace else 0)
            item.format(x, y, itemWidth).addTo(self)
            x += itemWidth

            # output track
            if i == len(self.items) - 1:
                if item.height == 0:
                    (Path(x, y).h(AR).addTo(self))
                else:
                    (Path(x, y + item.height).arc("se").addTo(self))
            elif i == 0 and item.height > self._lowerTrack:
                # Needs to arc up to meet the lower track, not down.
                if item.height - self._lowerTrack >= AR * 2:
                    (
                        Path(x, y + item.height)
                        .arc("se")
                        .v(self._lowerTrack - item.height + AR * 2)
                        .arc("wn")
                        .addTo(self)
                    )
                else:
                    # Not enough space to fit two arcs
                    # so just bail and draw a straight line for now.
                    (
                        Path(x, y + item.height)
                        .l(AR * 2, self._lowerTrack - item.height)
                        .addTo(self)
                    )
            else:
                (
                    Path(x, y + item.height)
                    .arc("ne")
                    .v(self._lowerTrack - item.height - AR * 2)
                    .arc("ws")
                    .addTo(self)
                )
        return self

    def __repr__(self) -> str:
        items = ", ".join(repr(item) for item in self.items)
        return f"HorizontalChoice({items})"

    def textDiagram(self) -> TextDiagram:
        line, line_vertical, roundcorner_bot_left, roundcorner_bot_right, roundcorner_top_left, roundcorner_top_right = TextDiagram._getParts(["line", "line_vertical", "roundcorner_bot_left", "roundcorner_bot_right", "roundcorner_top_left", "roundcorner_top_right"])

        # Format all the child items, so we can know the maximum entry, exit, and height.
        itemTDs = []
        for item in self.items:
            itemTDs.append(item.textDiagram())
        # diagramEntry: distance from top to lowest entry, aka distance from top to diagram entry, aka final diagram entry and exit.
        diagramEntry = max([itemTD.entry for itemTD in itemTDs])
        # SOILToBaseline: distance from top to lowest entry before rightmost item, aka distance from skip-over-items line to rightmost entry, aka SOIL height.
        SOILToBaseline = max([itemTD.entry for itemTD in itemTDs[:-1]])
        # topToSOIL: distance from top to skip-over-items line.
        topToSOIL = diagramEntry - SOILToBaseline
        # baselineToSUIL: distance from lowest entry or exit after leftmost item to bottom, aka distance from entry to skip-under-items line, aka SUIL height.
        baselineToSUIL = max([itemTD.height - min(itemTD.entry, itemTD.exit) for itemTD in itemTDs[1:]]) - 1

        # The diagram starts with a line from its entry up to skip-over-items line:
        lines = [" " * 2] * topToSOIL
        lines += [roundcorner_top_left + line]
        lines += [line_vertical + " "] * SOILToBaseline
        lines += [roundcorner_bot_right + line]
        diagramTD = TextDiagram(len(lines) - 1, len(lines) - 1, lines)
        for itemNum, itemTD in enumerate(itemTDs):
            if itemNum > 0:
                # All items except the leftmost start with a line from the skip-over-items line down to their entry,
                # with a joining-line across at the skip-under-items line:
                lines = []
                lines += [" " * 2] * topToSOIL
                # All such items except the rightmost also have a continuation of the skip-over-items line:
                lineToNextItem = " " if itemNum == len(itemTDs) - 1 else line
                lines += [roundcorner_top_right + lineToNextItem]
                lines += [line_vertical + " "] * SOILToBaseline
                lines += [roundcorner_bot_left + line]
                lines += [" " * 2] * baselineToSUIL
                lines += [line * 2]
                entryTD = TextDiagram(diagramTD.exit, diagramTD.exit, lines)
                diagramTD = diagramTD.appendRight(entryTD, "")
            partTD = TextDiagram(0, 0, [])
            if itemNum < len(itemTDs) - 1:
                # All items except the rightmost start with a segment of the skip-over-items line at the top.
                # followed by enough blank lines to push their entry down to the previous item's exit:
                lines = []
                lines += [line * itemTD.width]
                lines += [" " * itemTD.width] * (SOILToBaseline - itemTD.entry)
                SOILSegment = TextDiagram(0, 0, lines)
                partTD = partTD.appendBelow(SOILSegment, [])
            partTD = partTD.appendBelow(itemTD, [], moveEntry=True, moveExit=True)
            if itemNum > 0:
                # All items except the leftmost end with enough blank lines to pad down to the skip-under-items
                # line, followed by a segment of the skip-under-items line:
                lines = []
                lines += [" " * itemTD.width] * (baselineToSUIL - (itemTD.height - itemTD.entry) + 1)
                lines += [line * itemTD.width]
                SUILSegment = TextDiagram(0, 0, lines)
                partTD = partTD.appendBelow(SUILSegment, [])
            diagramTD = diagramTD.appendRight(partTD, "")
            if itemNum < len(itemTDs) - 1:
                # All items except the rightmost have a line from their exit down to the skip-under-items line,
                # with a joining-line across at the skip-over-items line:
                lines = []
                lines += [" " * 2] * topToSOIL
                lines += [line * 2]
                lines += [" " * 2] * (diagramTD.exit - topToSOIL - 1)
                lines += [line + roundcorner_top_right]
                lines += [" " + line_vertical] * (baselineToSUIL - (diagramTD.exit - diagramTD.entry))
                # All such items except the leftmost also have are continuing of the skip-under-items line from the previous item:
                lineFromPrevItem = line if itemNum > 0 else " "
                lines += [lineFromPrevItem + roundcorner_bot_left]
                entry = diagramEntry + 1 + (diagramTD.exit - diagramTD.entry)
                exitTD = TextDiagram(entry, diagramEntry + 1, lines)
                diagramTD = diagramTD.appendRight(exitTD, "")
            else:
                # The rightmost item has a line from the skip-under-items line and from its exit up to the diagram exit:
                lines = []
                lineFromExit = " " if diagramTD.exit != diagramTD.entry else line
                lines += [lineFromExit + roundcorner_top_left]
                lines += [" " + line_vertical] * (diagramTD.exit - diagramTD.entry - 1)
                if diagramTD.exit != diagramTD.entry:
                    lines += [line + roundcorner_bot_right]
                lines += [" " + line_vertical] * (baselineToSUIL - (diagramTD.exit - diagramTD.entry))
                lines += [line + roundcorner_bot_right]
                exitTD = TextDiagram(diagramTD.exit - diagramTD.entry, 0, lines)
                diagramTD = diagramTD.appendRight(exitTD, "")
        return diagramTD


def Optional(item: Node, skip: bool = False) -> Choice:
    return Choice(0 if skip else 1, Skip(), item)


class OneOrMore(DiagramItem):
    def __init__(self, item: Node, repeat: Opt[Node] = None):
        DiagramItem.__init__(self, "g")
        self.item = wrapString(item)
        repeat = repeat or Skip()
        self.rep = wrapString(repeat)
        self.width = max(self.item.width, self.rep.width) + AR * 2
        self.height = self.item.height
        self.up = self.item.up
        self.down = max(
            AR * 2, self.item.down + VS + self.rep.up + self.rep.height + self.rep.down
        )
        self.needsSpace = True
        addDebug(self)

    def format(self, x: float, y: float, width: float) -> OneOrMore:
        leftGap, rightGap = determineGaps(width, self.width)

        # Hook up the two sides if self is narrower than its stated width.
        Path(x, y).h(leftGap).addTo(self)
        Path(x + leftGap + self.width, y + self.height).h(rightGap).addTo(self)
        x += leftGap

        # Draw item
        Path(x, y).right(AR).addTo(self)
        self.item.format(x + AR, y, self.width - AR * 2).addTo(self)
        Path(x + self.width - AR, y + self.height).right(AR).addTo(self)

        # Draw repeat arc
        distanceFromY = max(
            AR * 2, self.item.height + self.item.down + VS + self.rep.up
        )
        Path(x + AR, y).arc("nw").down(distanceFromY - AR * 2).arc("ws").addTo(self)
        self.rep.format(x + AR, y + distanceFromY, self.width - AR * 2).addTo(self)
        Path(x + self.width - AR, y + distanceFromY + self.rep.height).arc("se").up(
            distanceFromY - AR * 2 + self.rep.height - self.item.height
        ).arc("en").addTo(self)

        return self

    def textDiagram(self) -> TextDiagram:
        line, repeat_top_left, repeat_left, repeat_bot_left, repeat_top_right, repeat_right, repeat_bot_right = TextDiagram._getParts(["line", "repeat_top_left", "repeat_left", "repeat_bot_left", "repeat_top_right", "repeat_right", "repeat_bot_right"])
        # Format the item and then format the repeat append it to tbe bottom, after a spacer.
        itemTD = self.item.textDiagram()
        repeatTD = self.rep.textDiagram()
        fIRWidth = TextDiagram._maxWidth(itemTD, repeatTD)
        repeatTD = repeatTD.expand(0, fIRWidth - repeatTD.width, 0, 0)
        itemTD = itemTD.expand(0, fIRWidth - itemTD.width, 0, 0)
        itemAndRepeatTD = itemTD.appendBelow(repeatTD, [])
        # Build the left side of the repeat line and append the combined item and repeat to its right.
        leftLines = []
        leftLines += [repeat_top_left + line]
        leftLines += [repeat_left + " "] * ((itemTD.height - itemTD.entry) + repeatTD.entry - 1)
        leftLines += [repeat_bot_left + line]
        leftTD = TextDiagram(0, 0, leftLines)
        leftTD = leftTD.appendRight(itemAndRepeatTD, "")
        # Build the right side of the repeat line and append it to the combined left side, item, and repeat's right.
        rightLines = []
        rightLines += [line + repeat_top_right]
        rightLines += [" " + repeat_right] * ((itemTD.height - itemTD.exit) + repeatTD.exit - 1)
        rightLines += [line + repeat_bot_right]
        rightTD = TextDiagram(0, 0, rightLines)
        diagramTD = leftTD.appendRight(rightTD, "")
        return diagramTD

    def walk(self, cb: WalkerF) -> None:
        cb(self)
        self.item.walk(cb)
        self.rep.walk(cb)

    def __repr__(self) -> str:
        return f"OneOrMore({repr(self.item)}, repeat={repr(self.rep)})"


def ZeroOrMore(item: Node, repeat: Opt[Node] = None, skip: bool = False) -> Choice:
    result = Optional(OneOrMore(item, repeat), skip)
    return result


class Group(DiagramItem):
    def __init__(self, item: Node, label: Opt[Node] = None):
        DiagramItem.__init__(self, "g")
        self.item = wrapString(item)
        self.label: Opt[DiagramItem]
        if isinstance(label, DiagramItem):
            self.label = label
        elif label:
            self.label = Comment(label)
        else:
            self.label = None

        self.width = max(
            self.item.width + (20 if self.item.needsSpace else 0),
            self.label.width if self.label else 0,
            AR * 2,
        )
        self.height = self.item.height
        self.boxUp = max(self.item.up + VS, AR)
        self.up = self.boxUp
        if self.label:
            self.up += self.label.up + self.label.height + self.label.down
        self.down = max(self.item.down + VS, AR)
        self.needsSpace = True
        addDebug(self)

    def format(self, x: float, y: float, width: float) -> Group:
        leftGap, rightGap = determineGaps(width, self.width)
        Path(x, y).h(leftGap).addTo(self)
        Path(x + leftGap + self.width, y + self.height).h(rightGap).addTo(self)
        x += leftGap

        DiagramItem(
            "rect",
            {
                "x": x,
                "y": y - self.boxUp,
                "width": self.width,
                "height": self.boxUp + self.height + self.down,
                "rx": AR,
                "ry": AR,
                "class": "group-box",
            },
        ).addTo(self)

        self.item.format(x, y, self.width).addTo(self)
        if self.label:
            self.label.format(
                x,
                y - (self.boxUp + self.label.down + self.label.height),
                self.label.width,
            ).addTo(self)

        return self

    def textDiagram(self) -> TextDiagram:
        diagramTD = TextDiagram.roundrect(self.item.textDiagram(), dashed=True)
        if self.label:
            labelTD = self.label.textDiagram()
            diagramTD = labelTD.appendBelow(diagramTD, [], moveEntry=True, moveExit=True).expand(0, 0, 1, 0)
        return diagramTD

    def walk(self, cb: WalkerF) -> None:
        cb(self)
        self.item.walk(cb)
        if self.label:
            self.label.walk(cb)

    def __repr__(self) -> str:
        return f"Group({repr(self.item)}, label={repr(self.label)})"


class Start(DiagramItem):
    def __init__(self, type: str = "simple", label: Opt[str] = None):
        DiagramItem.__init__(self, "g")
        if label:
            self.width = max(20, len(label) * CHAR_WIDTH + 10)
        else:
            self.width = 20
        self.up = 10
        self.down = 10
        self.type = type
        self.label = label
        addDebug(self)

    def format(self, x: float, y: float, width: float) -> Start:
        path = Path(x, y - 10)
        if self.type == "complex":
            path.down(20).m(0, -10).right(self.width).addTo(self)
        else:
            path.down(20).m(10, -20).down(20).m(-10, -10).right(self.width).addTo(self)
        if self.label:
            DiagramItem(
                "text",
                attrs={"x": x, "y": y - 15, "style": "text-anchor:start"},
                text=self.label,
            ).addTo(self)
        return self

    def textDiagram(self) -> TextDiagram:
        cross, line, tee_right = TextDiagram._getParts(["cross", "line", "tee_right"])
        if self.type == "simple":
            start = tee_right + cross + line
        else:
            start = tee_right + line
        labelTD = TextDiagram(0, 0, [])
        if self.label:
            labelTD = TextDiagram(0, 0, [self.label])
            start = TextDiagram._padR(start, labelTD.width, line)
        startTD = TextDiagram(0, 0, [start])
        return labelTD.appendBelow(startTD, [], moveEntry=True, moveExit=True)

    def __repr__(self) -> str:
        return f"Start(type={repr(self.type)}, label={repr(self.label)})"


class End(DiagramItem):
    def __init__(self, type: str = "simple"):
        DiagramItem.__init__(self, "path")
        self.width = 20
        self.up = 10
        self.down = 10
        self.type = type
        addDebug(self)

    def format(self, x: float, y: float, width: float) -> End:
        if self.type == "simple":
            self.attrs["d"] = "M {0} {1} h 20 m -10 -10 v 20 m 10 -20 v 20".format(x, y)
        elif self.type == "complex":
            self.attrs["d"] = "M {0} {1} h 20 m 0 -10 v 20".format(x, y)
        return self

    def textDiagram(self) -> TextDiagram:
        cross, line, tee_left = TextDiagram._getParts(["cross", "line", "tee_left"])
        if self.type == "simple":
            end = line + cross + tee_left
        else:
            end = line + tee_left
        return TextDiagram(0, 0, [end])

    def __repr__(self) -> str:
        return f"End(type={repr(self.type)})"


class Terminal(DiagramItem):
    def __init__(
        self, text: str, href: Opt[str] = None, title: Opt[str] = None, cls: str = ""
    ):
        DiagramItem.__init__(self, "g", {"class": " ".join(["terminal", cls])})
        self.text = text
        self.href = href
        self.title = title
        self.cls = cls
        self.width = len(text) * CHAR_WIDTH + 20
        self.up = 11
        self.down = 11
        self.needsSpace = True
        addDebug(self)

    def __repr__(self) -> str:
        return f"Terminal({repr(self.text)}, href={repr(self.href)}, title={repr(self.title)}, cls={repr(self.cls)})"

    def format(self, x: float, y: float, width: float) -> Terminal:
        leftGap, rightGap = determineGaps(width, self.width)

        # Hook up the two sides if self is narrower than its stated width.
        Path(x, y).h(leftGap).addTo(self)
        Path(x + leftGap + self.width, y).h(rightGap).addTo(self)

        DiagramItem(
            "rect",
            {
                "x": x + leftGap,
                "y": y - 11,
                "width": self.width,
                "height": self.up + self.down,
                "rx": 10,
                "ry": 10,
            },
        ).addTo(self)
        text = DiagramItem(
            "text", {"x": x + leftGap + self.width / 2, "y": y + 4}, self.text
        )
        if self.href is not None:
            a = DiagramItem("a", {"xlink:href": self.href}, text).addTo(self)
            text.addTo(a)
        else:
            text.addTo(self)
        if self.title is not None:
            DiagramItem("title", {}, self.title).addTo(self)
        return self

    def textDiagram(self) -> TextDiagram:
        # Note: href, title, and cls are ignored for text diagrams.
        return TextDiagram.roundrect(self.text)


class NonTerminal(DiagramItem):
    def __init__(
        self, text: str, href: Opt[str] = None, title: Opt[str] = None, cls: str = ""
    ):
        DiagramItem.__init__(self, "g", {"class": " ".join(["non-terminal", cls])})
        self.text = text
        self.href = href
        self.title = title
        self.cls = cls
        self.width = len(text) * CHAR_WIDTH + 20
        self.up = 11
        self.down = 11
        self.needsSpace = True
        addDebug(self)

    def __repr__(self) -> str:
        return f"NonTerminal({repr(self.text)}, href={repr(self.href)}, title={repr(self.title)}, cls={repr(self.cls)})"

    def format(self, x: float, y: float, width: float) -> NonTerminal:
        leftGap, rightGap = determineGaps(width, self.width)

        # Hook up the two sides if self is narrower than its stated width.
        Path(x, y).h(leftGap).addTo(self)
        Path(x + leftGap + self.width, y).h(rightGap).addTo(self)

        DiagramItem(
            "rect",
            {
                "x": x + leftGap,
                "y": y - 11,
                "width": self.width,
                "height": self.up + self.down,
            },
        ).addTo(self)
        text = DiagramItem(
            "text", {"x": x + leftGap + self.width / 2, "y": y + 4}, self.text
        )
        if self.href is not None:
            a = DiagramItem("a", {"xlink:href": self.href}, text).addTo(self)
            text.addTo(a)
        else:
            text.addTo(self)
        if self.title is not None:
            DiagramItem("title", {}, self.title).addTo(self)
        return self

    def textDiagram(self) -> TextDiagram:
        # Note: href, title, and cls are ignored for text diagrams.
        return TextDiagram.rect(self.text)


class Comment(DiagramItem):
    def __init__(
        self, text: str, href: Opt[str] = None, title: Opt[str] = None, cls: str = ""
    ):
        DiagramItem.__init__(self, "g", {"class": " ".join(["non-terminal", cls])})
        self.text = text
        self.href = href
        self.title = title
        self.cls = cls
        self.width = len(text) * COMMENT_CHAR_WIDTH + 10
        self.up = 8
        self.down = 8
        self.needsSpace = True
        addDebug(self)

    def __repr__(self) -> str:
        return f"Comment({repr(self.text)}, href={repr(self.href)}, title={repr(self.title)}, cls={repr(self.cls)})"

    def format(self, x: float, y: float, width: float) -> Comment:
        leftGap, rightGap = determineGaps(width, self.width)

        # Hook up the two sides if self is narrower than its stated width.
        Path(x, y).h(leftGap).addTo(self)
        Path(x + leftGap + self.width, y).h(rightGap).addTo(self)

        text = DiagramItem(
            "text",
            {"x": x + leftGap + self.width / 2, "y": y + 5, "class": "comment"},
            self.text,
        )
        if self.href is not None:
            a = DiagramItem("a", {"xlink:href": self.href}, text).addTo(self)
            text.addTo(a)
        else:
            text.addTo(self)
        if self.title is not None:
            DiagramItem("title", {}, self.title).addTo(self)
        return self

    def textDiagram(self) -> TextDiagram:
        # Note: href, title, and cls are ignored for text diagrams.
        return TextDiagram(0, 0, [self.text])


class Skip(DiagramItem):
    def __init__(self) -> None:
        DiagramItem.__init__(self, "g")
        self.width = 0
        self.up = 0
        self.down = 0
        addDebug(self)

    def format(self, x: float, y: float, width: float) -> Skip:
        Path(x, y).right(width).addTo(self)
        return self

    def textDiagram(self) -> TextDiagram:
        (line,) = TextDiagram._getParts(["line"])
        return TextDiagram(0, 0, [line])

    def __repr__(self) -> str:
        return "Skip()"


class TextDiagram:
    # Characters to use in drawing diagrams.  See setFormatting(), PARTS_ASCII, and PARTS_UNICODE.
    parts: Dict[str, str]

    def __init__(self, entry: int, exit: int, lines: List[str]) -> TextDiagram:
        # entry: The entry line for this diagram-part.
        self.entry: int = entry
        # exit: The exit line for this diagram-part.
        self.exit: int = exit
        # height: The height of this diagram-part, in lines.
        self.height: int = len(lines)
        # lines[]: The visual data of this diagram-part.  Each line must be the same length.
        self.lines: List[str] = lines.copy()
        # width: The width of this diagram-part, in character cells.
        self.width: int = len(lines[0]) if len(lines) > 0 else 0
        nl = "\n"  # f-strings can't contain \n until Python 3.12
        assert entry <= len(lines), f"Entry is not within diagram vertically:{nl}{self._dump(False)}"
        assert exit <= len(lines), f"Exit is not within diagram vertically:{nl}{self._dump(False)}"
        for i in range(0, len(lines)):
            assert len(lines[0]) == len(lines[i]), f"Diagram data is not rectangular:{nl}{self._dump(False)}"

    def alter(self, entry: int = None, exit: int = None, lines: List[str] = None) -> TextDiagram:
        """
        Create and return a new TextDiagram based on this instance, with the specified changes.

        Note: This is used sparingly, and may be a bad idea.
        """
        newEntry = entry or self.entry
        newExit = exit or self.exit
        newLines = lines or self.lines
        return self.__class__(newEntry, newExit, newLines.copy())

    def appendBelow(self, item: TextDiagram, linesBetween: List[str], moveEntry=False, moveExit=False) -> TextDiagram:
        """
        Create and return a new TextDiagram by appending the specified lines below this instance's data,
        and then appending the specified TextDiagram below those lines, possibly setting the resulting
        TextDiagram's entry and or exit indices to those of the appended item.
        """
        newWidth = max(self.width, item.width)
        newLines = []
        newLines += self.center(newWidth, " ").lines
        for line in linesBetween:
            newLines += [TextDiagram._padR(line, newWidth, " ")]
        newLines += item.center(newWidth, " ").lines
        newEntry = self.height + len(linesBetween) + item.entry if moveEntry else self.entry
        newExit = self.height + len(linesBetween) + item.exit if moveExit else self.exit
        newSelf = self.__class__(newEntry, newExit, newLines)
        return newSelf

    def appendRight(self, item: TextDiagram, charsBetween: str) -> TextDiagram:
        """
        Create and return a new TextDiagram by appending the specified TextDiagram to the right of this instance's data,
        aligning the left-hand exit and the right-hand entry points.  The charsBetween are inserted between the left-exit
        and right-entry, and equivalent spaces on all other lines.
        """
        joinLine = max(self.exit, item.entry)
        newHeight = max(self.height - self.exit, item.height - item.entry) + joinLine
        leftTopAdd = joinLine - self.exit
        leftBotAdd = newHeight - self.height - leftTopAdd
        rightTopAdd = joinLine - item.entry
        rightBotAdd = newHeight - item.height - rightTopAdd
        left = self.expand(0, 0, leftTopAdd, leftBotAdd)
        right = item.expand(0, 0, rightTopAdd, rightBotAdd)
        newLines = []
        for i in range(0, newHeight):
            sep = " " * len(charsBetween) if i != joinLine else charsBetween
            newLines += [(left.lines[i] + sep + right.lines[i])]
        newEntry = self.entry + leftTopAdd
        newExit = item.exit + rightTopAdd
        return self.__class__(newEntry, newExit, newLines)

    def center(self, width: int, pad: str) -> TextDiagram:
        """
        Create and return a new TextDiagram by centering the data of this instance within a new, equal or larger widtth.
        """
        assert width >= self.width, "Cannot center into smaller width"
        if width == self.width:
            return self.copy()
        else:
            total_padding = width - self.width
            leftWidth = total_padding // 2
            left = [(pad * leftWidth)] * self.height
            right = [(pad * (total_padding - leftWidth))] * self.height
            return self.__class__(self.entry, self.exit, TextDiagram._encloseLines(self.lines, left, right))

    def copy(self) -> TextDiagram:
        """
        Create and return a new TextDiagram by copying this instance's data.
        """
        return self.__class__(self.entry, self.exit, self.lines.copy())

    def expand(self, left: int, right: int, top: int, bottom: int) -> TextDiagram:
        """
        Create and return a new TextDiagram by expanding this instance's data by the specified amount in the specified directions.
        """
        assert left >= 0
        assert right >= 0
        assert top >= 0
        assert bottom >= 0
        if left + right + top + bottom == 0:
            return self.copy()
        else:
            line = self.parts["line"]
            newLines = []
            newLines += [(" " * (self.width + left + right))] * top
            for i in range(0, self.height):
                leftExpansion = line if i == self.entry else " "
                rightExpansion = line if i == self.exit else " "
                newLines += [(leftExpansion * left) + self.lines[i] + (rightExpansion * right)]
            newLines += [(" " * (self.width + left + right))] * bottom
            return self.__class__(self.entry + top, self.exit + top, newLines)

    @classmethod
    def rect(cls, item: Union[str, TextDiagram], dashed=False) -> TextDiagram:
        """
        Create and return a new TextDiagram for a rectangular box.
        """
        return cls._rectish("rect", item, dashed=dashed)

    @classmethod
    def roundrect(cls, item: Union[str, TextDiagram], dashed=False) -> TextDiagram:
        """
        Create and return a new TextDiagram for a rectangular box with rounded corners.
        """
        return cls._rectish("roundrect", item, dashed=dashed)

    @classmethod
    def setFormatting(cls, characters: Dict[str, str] = None, defaults: Dict[str, str] = None) -> None:
        """
        Set the characters to use for drawing text diagrams.
        """
        if characters is not None:
            cls.parts = {}
            if defaults is not None:
                cls.parts.update(defaults)
            cls.parts.update(characters)
        for name in cls.parts:
            assert len(cls.parts[name]) == 1, f"Text part {name} is more than 1 character: {cls.parts[name]}"

    def _dump(self, show=True) -> None:
        """
        Dump out the data of this instance for debugging, either displaying or returning it.
        DO NOT use this for actual work, only for debugging or in assertion output.
        """
        nl = "\n"  # f-strings can't contain \n until Python 3.12
        result = f"height={self.height}; len(lines)={len(self.lines)}"
        if self.entry > len(self.lines):
            result += f"; entry outside diagram: entry={self.entry}"
        if self.exit > len(self.lines):
            result += f"; exit outside diagram: exit={self.exit}"
        for y in range(0, max(len(self.lines), self.entry + 1, self.exit + 1)):
            result = result + f"{nl}[{y:03}]"
            if y < len(self.lines):
                result = result + f" '{self.lines[y]}' len={len(self.lines[y])}"
            if y == self.entry and y == self.exit:
                result += " <- entry, exit"
            elif y == self.entry:
                result += " <- entry"
            elif y == self.exit:
                result += " <- exit"
        if show:
            print(result)
        else:
            return result

    @classmethod
    def _encloseLines(cls, lines: List[str], lefts: List[str], rights: List[str]) -> List[str]:
        """
        Join the lefts, lines, and rights arrays together, line-by-line, and return the result.
        """
        assert len(lines) == len(lefts), "All arguments must be the same length"
        assert len(lines) == len(rights), "All arguments must be the same length"
        newLines = []
        for i in range(0, len(lines)):
            newLines.append(lefts[i] + lines[i] + rights[i])
        return newLines

    @staticmethod
    def _gaps(outerWidth: int, innerWidth: int) -> Tuple[int, int]:
        """
        Return the left and right pad spacing based on the alignment configuration setting.
        """
        diff = outerWidth - innerWidth
        if INTERNAL_ALIGNMENT == "left":
            return 0, diff
        elif INTERNAL_ALIGNMENT == "right":
            return diff, 0
        else:
            left = diff // 2
            right = diff - left
            return left, right

    @classmethod
    def _getParts(cls, partNames: List[str]) -> List[str]:
        """
        Return a list of text diagram drawing characters for the specified character names.
        """
        return [cls.parts[name] for name in partNames]

    @staticmethod
    def _maxWidth(*args: List[Union[int, str, List[str], TextDiagram]]) -> int:
        """
        Return the maximum width of all of the arguments.
        """
        maxWidth = 0
        for arg in args:
            if isinstance(arg, TextDiagram):
                width = arg.width
            elif isinstance(arg, list):
                width = max([len(e) for e in arg])
            elif isinstance(arg, int):
                width = len(str(arg))
            else:
                width = len(arg)
            maxWidth = width if width > maxWidth else maxWidth
        return maxWidth

    @staticmethod
    def _padL(string: str, width: int, pad: str) -> str:
        """
        Pad the specified string on the left to the specified width with the specified pad string and return the result.
        """
        assert (width - len(string)) % len(pad) == 0, f"Gap {width - len(string)} must be a multiple of pad string '{pad}'"
        return (pad * ((width - len(string) // len(pad)))) + string

    @staticmethod
    def _padR(string: str, width: int, pad: str) -> str:
        """
        Pad the specified string on the right to the specified width with the specified pad string and return the result.
        """
        assert (width - len(string)) % len(pad) == 0, f"Gap {width - len(string)} must be a multiple of pad string '{pad}'"
        return string + (pad * ((width - len(string) // len(pad))))

    @classmethod
    def _rectish(cls, rect_type: str, data: TextDiagram, dashed=False) -> TextDiagram:
        """
        Create and return a new TextDiagram for a rectangular box surrounding the specified TextDiagram, using the
        specified set of drawing characters (i.e., "rect" or "roundrect"), and possibly using dashed lines.
        """
        lineType = "_dashed" if dashed else ""
        topLeft, ctrLeft, botLeft, topRight, ctrRight, botRight, topHoriz, botHoriz, line, cross = cls._getParts([f"{rect_type}_top_left", f"{rect_type}_left{lineType}", f"{rect_type}_bot_left", f"{rect_type}_top_right", f"{rect_type}_right{lineType}", f"{rect_type}_bot_right", f"{rect_type}_top{lineType}", f"{rect_type}_bot{lineType}", "line", "cross"])
        itemWasFormatted = isinstance(data, TextDiagram)
        if itemWasFormatted:
            itemTD = data
        else:
            itemTD = TextDiagram(0, 0, [data])
        # Create the rectangle and enclose the item in it.
        lines = []
        lines += [(topHoriz * (itemTD.width + 2))]
        if itemWasFormatted:
            lines += itemTD.expand(1, 1, 0, 0).lines
        else:
            for i in range(0, len(itemTD.lines)):
                lines += [(" " + itemTD.lines[i] + " ")]
        lines += [(botHoriz * (itemTD.width + 2))]
        entry = itemTD.entry + 1
        exit = itemTD.exit + 1
        leftMaxWidth = cls._maxWidth(topLeft, ctrLeft, botLeft)
        lefts = [cls._padR(ctrLeft, leftMaxWidth, " ")] * len(lines)
        lefts[0] = cls._padR(topLeft, leftMaxWidth, topHoriz)
        lefts[-1] = cls._padR(botLeft, leftMaxWidth, botHoriz)
        if itemWasFormatted:
            lefts[entry] = cross
        rightMaxWidth = cls._maxWidth(topRight, ctrRight, botRight)
        rights = [cls._padL(ctrRight, rightMaxWidth, " ")] * len(lines)
        rights[0] = cls._padL(topRight, rightMaxWidth, topHoriz)
        rights[-1] = cls._padL(botRight, rightMaxWidth, botHoriz)
        if itemWasFormatted:
            rights[exit] = cross
        # Build the entry and exit perimeter.
        lines = TextDiagram._encloseLines(lines, lefts, rights)
        lefts = [" "] * len(lines)
        lefts[entry] = line
        rights = [" "] * len(lines)
        rights[exit] = line
        lines = TextDiagram._encloseLines(lines, lefts, rights)
        return cls(entry, exit, lines)

    def __repr__(self) -> str:
        return f"TextDiagram({self.entry}, {self.exit}, {self.lines})"

    # Note:  All the drawing sequences below MUST be single characters.  setFormatting() checks this.

    # Unicode 25xx box drawing characters, plus a few others.
    PARTS_UNICODE = {
        "cross_diag"             : "\u2573",
        "corner_bot_left"        : "\u2514",
        "corner_bot_right"       : "\u2518",
        "corner_top_left"        : "\u250c",
        "corner_top_right"       : "\u2510",
        "cross"                  : "\u253c",
        "left"                   : "\u2502",
        "line"                   : "\u2500",
        "line_vertical"          : "\u2502",
        "multi_repeat"           : "\u21ba",
        "rect_bot"               : "\u2500",
        "rect_bot_dashed"        : "\u2504",
        "rect_bot_left"          : "\u2514",
        "rect_bot_right"         : "\u2518",
        "rect_left"              : "\u2502",
        "rect_left_dashed"       : "\u2506",
        "rect_right"             : "\u2502",
        "rect_right_dashed"      : "\u2506",
        "rect_top"               : "\u2500",
        "rect_top_dashed"        : "\u2504",
        "rect_top_left"          : "\u250c",
        "rect_top_right"         : "\u2510",
        "repeat_bot_left"        : "\u2570",
        "repeat_bot_right"       : "\u256f",
        "repeat_left"            : "\u2502",
        "repeat_right"           : "\u2502",
        "repeat_top_left"        : "\u256d",
        "repeat_top_right"       : "\u256e",
        "right"                  : "\u2502",
        "roundcorner_bot_left"   : "\u2570",
        "roundcorner_bot_right"  : "\u256f",
        "roundcorner_top_left"   : "\u256d",
        "roundcorner_top_right"  : "\u256e",
        "roundrect_bot"          : "\u2500",
        "roundrect_bot_dashed"   : "\u2504",
        "roundrect_bot_left"     : "\u2570",
        "roundrect_bot_right"    : "\u256f",
        "roundrect_left"         : "\u2502",
        "roundrect_left_dashed"  : "\u2506",
        "roundrect_right"        : "\u2502",
        "roundrect_right_dashed" : "\u2506",
        "roundrect_top"          : "\u2500",
        "roundrect_top_dashed"   : "\u2504",
        "roundrect_top_left"     : "\u256d",
        "roundrect_top_right"    : "\u256e",
        "separator"              : "\u2500",
        "tee_left"               : "\u2524",
        "tee_right"              : "\u251c",
    }

    # Plain old ASCII characters.
    PARTS_ASCII = {
        "cross_diag"             : "X",
        "corner_bot_left"        : "\\",
        "corner_bot_right"       : "/",
        "corner_top_left"        : "/",
        "corner_top_right"       : "\\",
        "cross"                  : "+",
        "left"                   : "|",
        "line"                   : "-",
        "line_vertical"          : "|",
        "multi_repeat"           : "&",
        "rect_bot"               : "-",
        "rect_bot_dashed"        : "-",
        "rect_bot_left"          : "+",
        "rect_bot_right"         : "+",
        "rect_left"              : "|",
        "rect_left_dashed"       : "|",
        "rect_right"             : "|",
        "rect_right_dashed"      : "|",
        "rect_top_dashed"        : "-",
        "rect_top"               : "-",
        "rect_top_left"          : "+",
        "rect_top_right"         : "+",
        "repeat_bot_left"        : "\\",
        "repeat_bot_right"       : "/",
        "repeat_left"            : "|",
        "repeat_right"           : "|",
        "repeat_top_left"        : "/",
        "repeat_top_right"       : "\\",
        "right"                  : "|",
        "roundcorner_bot_left"   : "\\",
        "roundcorner_bot_right"  : "/",
        "roundcorner_top_left"   : "/",
        "roundcorner_top_right"  : "\\",
        "roundrect_bot"          : "-",
        "roundrect_bot_dashed"   : "-",
        "roundrect_bot_left"     : "\\",
        "roundrect_bot_right"    : "/",
        "roundrect_left"         : "|",
        "roundrect_left_dashed"  : "|",
        "roundrect_right"        : "|",
        "roundrect_right_dashed" : "|",
        "roundrect_top"          : "-",
        "roundrect_top_dashed"   : "-",
        "roundrect_top_left"     : "/",
        "roundrect_top_right"    : "\\",
        "separator"              : "-",
        "tee_left"               : "|",
        "tee_right"              : "|",
    }


# Default to Unicode box characters, they're much prettier than raw ASCII.
TextDiagram.setFormatting(TextDiagram.PARTS_UNICODE)

if __name__ == "__main__":

    if len(sys.argv) < 2 or sys.argv[1] == "":
        mode = "svg"
    elif sys.argv[1].lower() in ["svg", "ascii", "unicode", "standalone"]:
        mode = sys.argv[1].lower()
    else:
        raise ValueError(f"Unknown option: {sys.argv[1]}")
    testList = sys.argv[2:]

    def add(name: str, diagram: DiagramItem) -> None:
        if name in testList or len(testList) == 0:
            sys.stdout.write(f"\n<h1>{escapeHtml(name)}</h1>\n")
            if mode == "svg":
                diagram.writeSvg(sys.stdout.write)
            elif mode == "standalone":
                diagram.writeStandalone(sys.stdout.write)
            elif mode in ["ascii", "unicode"]:
                sys.stdout.write("\n<pre>\n")
                diagram.writeText(sys.stdout.write)
                sys.stdout.write("\n</pre>\n")
            sys.stdout.write("\n")

    sys.stdout.write("<!doctype html><title>Test</title><body>")
    if mode == "ascii":
        TextDiagram.setFormatting(TextDiagram.PARTS_ASCII)
    elif mode == "unicode":
        TextDiagram.setFormatting(TextDiagram.PARTS_UNICODE)
    elif mode in ("svg", "standalone"):
        sys.stdout.write(
            f"""
    		<style>
            {DEFAULT_STYLE}
    		.blue text {{ fill: blue; }}
    		</style>
    		"""
        )
    with open("test.py", "r", encoding="utf-8") as fh:
        exec(fh.read())  # pylint: disable=exec-used
    sys.stdout.write("</body></html>")