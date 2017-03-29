# coding=utf-8
import sys

if sys.version_info >= (3, ):
    unicode = str

# Display constants
VERTICAL_SEPARATION = 8
ARC_RADIUS = 10
DIAGRAM_CLASS = 'railroad-diagram'
TRANSLATE_HALF_PIXEL = True
INTERNAL_ALIGNMENT = 'center'
DEBUG=False

# Assume a monospace font with each char .5em wide, and the em is 16px
CHARACTER_ADVANCE = 8

def e(text):
    import re
    return re.sub(r"[*_\`\[\]<&]", lambda c: "&#{0};".format(ord(c.group(0))), unicode(text))

def determineGaps(outer, inner):
    diff = outer - inner
    if INTERNAL_ALIGNMENT == 'left':
        return 0, diff
    elif INTERNAL_ALIGNMENT == 'right':
        return diff, 0
    else:
        return diff/2, diff/2

def doubleenumerate(seq):
    length = len(list(seq))
    for i,item in enumerate(seq):
        yield i, i-length, item



class DiagramItem(object):
    def __init__(self, name, attrs=None, text=None):
        self.name = name
        # up = distance it projects above the entry line
        # height = distance between the entry/exit lines
        # down = distance it projects below the exit line
        self.height = 0
        self.attrs = attrs or {}
        self.children = [text] if text else []
        self.needsSpace = False

    def format(self, x, y, width):
        raise NotImplementedError  # Virtual

    def addTo(self, parent):
        parent.children.append(self)
        return self

    def writeSvg(self, write):
        write(u'<{0}'.format(self.name))
        for name, value in sorted(self.attrs.items()):
            write(u' {0}="{1}"'.format(name, e(value)))
        write(u'>')
        if self.name in ["g", "svg"]:
            write(u'\n')
        for child in self.children:
            if isinstance(child, DiagramItem):
                child.writeSvg(write)
            else:
                write(e(child))
        write(u'</{0}>'.format(self.name))

    def __eq__(self, other):
        return type(self) == type(other) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)


class Path(DiagramItem):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        DiagramItem.__init__(self, 'path', {'d': 'M%s %s' % (x, y)})

    def m(self, x, y):
        self.attrs['d'] += 'm{0} {1}'.format(x,y)
        return self

    def h(self, val):
        self.attrs['d'] += 'h{0}'.format(val)
        return self

    def right(self, val):
        return self.h(max(0, val))

    def left(self, val):
        return self.h(-max(0, val))

    def v(self, val):
        self.attrs['d'] += 'v{0}'.format(val)
        return self

    def down(self, val):
        return self.v(max(0, val))

    def up(self, val):
        return self.v(-max(0, val))

    def arc(self, sweep):
        x = ARC_RADIUS
        y = ARC_RADIUS
        if sweep[0] == 'e' or sweep[1] == 'w':
            x *= -1
        if sweep[0] == 's' or sweep[1] == 'n':
            y *= -1
        cw = 1 if sweep == 'ne' or sweep == 'es' or sweep == 'sw' or sweep == 'wn' else 0
        self.attrs['d'] += 'a{0} {0} 0 0 {1} {2} {3}'.format(ARC_RADIUS, cw, x, y)
        return self


    def format(self):
        self.attrs['d'] += 'h.5'
        return self

    def __repr__(self):
        return 'Path(%r, %r)' % (self.x, self.y)


def wrapString(value):
    return value if isinstance(value, DiagramItem) else Terminal(value)


DEFAULT_STYLE = '''\
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
'''


class Style(DiagramItem):
    def __init__(self, css):
        self.name = 'style'
        self.css = css
        self.height = 0
        self.width = 0
        self.needsSpace = False

    def __repr__(self):
        return 'Style(%r)' % css

    def format(self, x, y, width):
        return self

    def writeSvg(self, write):
        # Write included stylesheet as CDATA. See https://developer.mozilla.org/en-US/docs/Web/SVG/Element/style
        cdata = u'/* <![CDATA[ */\n{css}\n/* ]]> */\n'.format(css=self.css)
        write(u'<style>{cdata}</style>'.format(cdata=cdata))


class Diagram(DiagramItem):
    def __init__(self, *items, **kwargs):
        # Accepts a type=[simple|complex] kwarg
        DiagramItem.__init__(self, 'svg', {'class': DIAGRAM_CLASS})
        self.type = kwargs.get("type", "simple")
        self.css = kwargs.get("css", DEFAULT_STYLE)
        self.items = [Start(self.type)] + [wrapString(item) for item in items] + [End(self.type)]
        if self.css:
            self.items.insert(0, Style(self.css))
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

    def __repr__(self):
        if self.css:
            items = ', '.join(map(repr, self.items[2:-1]))
        else:
            items = ', '.join(map(repr, self.items[1:-1]))
        pieces = [] if not items else [items]
        if self.css != DEFAULT_STYLE:
            pieces.append('css=%r' % self.css)
        if self.type != 'simple':
            pieces.append('type=%r' % self.type)
        return 'Diagram(%s)' % ', '.join(pieces)

    def format(self, paddingTop=20, paddingRight=None, paddingBottom=None, paddingLeft=None):
        if paddingRight is None:
            paddingRight = paddingTop
        if paddingBottom is None:
            paddingBottom = paddingTop
        if paddingLeft is None:
            paddingLeft = paddingRight
        x = paddingLeft
        y = paddingTop + self.up
        g = DiagramItem('g')
        if TRANSLATE_HALF_PIXEL:
            g.attrs['transform'] = 'translate(.5 .5)'
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
        self.attrs['width'] = self.width + paddingLeft + paddingRight
        self.attrs['height'] = self.up + self.height + self.down + paddingTop + paddingBottom
        self.attrs['viewBox'] = "0 0 {width} {height}".format(**self.attrs)
        g.addTo(self)
        self.formatted = True
        return self


    def writeSvg(self, write):
        if not self.formatted:
            self.format()
        return DiagramItem.writeSvg(self, write)

    def parseCSSGrammar(self, text):
        token_patterns = {
            'keyword': r"[\w-]+\(?",
            'type': r"<[\w-]+(\(\))?>",
            'char': r"[/,()]",
            'literal': r"'(.)'",
            'openbracket': r"\[",
            'closebracket': r"\]",
            'closebracketbang': r"\]!",
            'bar': r"\|",
            'doublebar': r"\|\|",
            'doubleand': r"&&",
            'multstar': r"\*",
            'multplus': r"\+",
            'multhash': r"#",
            'multnum1': r"{\s*(\d+)\s*}",
            'multnum2': r"{\s*(\d+)\s*,\s*(\d*)\s*}",
            'multhashnum1': r"#{\s*(\d+)\s*}",
            'multhashnum2': r"{\s*(\d+)\s*,\s*(\d*)\s*}"
        }


class Sequence(DiagramItem):
    def __init__(self, *items):
        DiagramItem.__init__(self, 'g')
        self.items = [wrapString(item) for item in items]
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
        if DEBUG:
            self.attrs['data-updown'] = "{0} {1} {2}".format(self.up, self.height, self.down)
            self.attrs['data-type'] = "sequence"

    def __repr__(self):
        items = ', '.join(map(repr, self.items))
        return 'Sequence(%s)' % items

    def format(self, x, y, width):
        leftGap, rightGap = determineGaps(width, self.width)
        Path(x, y).h(leftGap).addTo(self)
        Path(x+leftGap+self.width, y+self.height).h(rightGap).addTo(self)
        x += leftGap
        for i,item in enumerate(self.items):
            if item.needsSpace and i > 0:
                Path(x, y).h(10).addTo(self)
                x += 10
            item.format(x, y, item.width).addTo(self)
            x += item.width
            y += item.height
            if item.needsSpace and i < len(self.items)-1:
                Path(x, y).h(10).addTo(self)
                x += 10
        return self


class Stack(DiagramItem):
    def __init__(self, *items):
        DiagramItem.__init__(self, 'g')
        self.items = [wrapString(item) for item in items]
        self.needsSpace = True
        self.width = max(item.width + (20 if item.needsSpace else 0) for item in self.items)
        # pretty sure that space calc is totes wrong
        if len(self.items) > 1:
            self.width += ARC_RADIUS*2
        self.up = self.items[0].up
        self.down = self.items[-1].down
        self.height = 0
        last = len(self.items) - 1
        for i,item in enumerate(self.items):
            self.height += item.height
            if i > 0:
                self.height += max(ARC_RADIUS*2, item.up + VERTICAL_SEPARATION)
            if i < last:
                self.height += max(ARC_RADIUS*2, item.down + VERTICAL_SEPARATION)
        if DEBUG:
            self.attrs['data-updown'] = "{0} {1} {2}".format(self.up, self.height, self.down)
            self.attrs['data-type'] = "stack"

    def __repr__(self):
        items = ', '.join(repr(item) for item in self.items)
        return 'Stack(%s)' % items

    def format(self, x, y, width):
        leftGap, rightGap = determineGaps(width, self.width)
        Path(x, y).h(leftGap).addTo(self)
        x += leftGap
        xInitial = x
        if len(self.items) > 1:
            Path(x, y).h(ARC_RADIUS).addTo(self)
            x += ARC_RADIUS
            innerWidth = self.width - ARC_RADIUS*2
        else:
            innerWidth = self.width
        for i,item in enumerate(self.items):
            item.format(x, y, innerWidth).addTo(self)
            x += innerWidth
            y += item.height
            if i != len(self.items)-1:
                (Path(x,y)
                    .arc('ne').down(max(0, item.down + VERTICAL_SEPARATION - ARC_RADIUS*2))
                    .arc('es').left(innerWidth)
                    .arc('nw').down(max(0, self.items[i+1].up + VERTICAL_SEPARATION - ARC_RADIUS*2))
                    .arc('ws').addTo(self))
                y += max(item.down + VERTICAL_SEPARATION, ARC_RADIUS*2) + max(self.items[i+1].up + VERTICAL_SEPARATION, ARC_RADIUS*2)
                x = xInitial + ARC_RADIUS
        if len(self.items) > 1:
            Path(x, y).h(ARC_RADIUS).addTo(self)
            x += ARC_RADIUS
        Path(x, y).h(rightGap).addTo(self)
        return self


class OptionalSequence(DiagramItem):
    def __new__(cls, *items):
        if len(items) <= 1:
            return Sequence(*items)
        else:
            return super(OptionalSequence, cls).__new__(cls)

    def __init__(self, *items):
        DiagramItem.__init__(self, 'g')
        self.items = [wrapString(item) for item in items]
        self.needsSpace = False
        self.width = 0
        self.up = 0
        self.height = sum(item.height for item in self.items)
        self.down = self.items[0].down
        heightSoFar = 0
        for i,item in enumerate(self.items):
            self.up = max(self.up, max(ARC_RADIUS * 2, item.up + VERTICAL_SEPARATION) - heightSoFar)
            heightSoFar += item.height
            if i > 0:
                self.down = max(self.height + self.down, heightSoFar + max(ARC_RADIUS*2, item.down + VERTICAL_SEPARATION)) - self.height
            itemWidth = item.width + (20 if item.needsSpace else 0)
            if i == 0:
                self.width += ARC_RADIUS + max(itemWidth, ARC_RADIUS)
            else:
                self.width += ARC_RADIUS*2 + max(itemWidth, ARC_RADIUS) + ARC_RADIUS
        if DEBUG:
            self.attrs['data-updown'] = "{0} {1} {2}".format(self.up, self.height, self.down)
            self.attrs['data-type'] = "optseq"

    def __repr__(self):
        items = ', '.join(repr(item) for item in self.items)
        return 'OptionalSequence(%s)' % items

    def format(self, x, y, width):
        leftGap, rightGap = determineGaps(width, self.width)
        Path(x, y).right(leftGap).addTo(self)
        Path(x + leftGap + self.width, y + self.height).right(rightGap).addTo(self)
        x += leftGap
        upperLineY = y - self.up
        last = len(self.items) - 1
        for i,item in enumerate(self.items):
            itemSpace = 10 if item.needsSpace else 0
            itemWidth = item.width + itemSpace
            if i == 0:
                # Upper skip
                (Path(x,y)
                    .arc('se')
                    .up(y - upperLineY - ARC_RADIUS*2)
                    .arc('wn')
                    .right(itemWidth - ARC_RADIUS)
                    .arc('ne')
                    .down(y + item.height - upperLineY - ARC_RADIUS*2)
                    .arc('ws')
                    .addTo(self))
                # Straight line
                (Path(x, y)
                    .right(itemSpace + ARC_RADIUS)
                    .addTo(self))
                item.format(x + itemSpace + ARC_RADIUS, y, item.width).addTo(self)
                x += itemWidth + ARC_RADIUS
                y += item.height
            elif i < last:
                # Upper skip
                (Path(x, upperLineY)
                    .right(ARC_RADIUS*2 + max(itemWidth, ARC_RADIUS) + ARC_RADIUS)
                    .arc('ne')
                    .down(y - upperLineY + item.height - ARC_RADIUS*2)
                    .arc('ws')
                    .addTo(self))
                # Straight line
                (Path(x,y)
                    .right(ARC_RADIUS*2)
                    .addTo(self))
                item.format(x + ARC_RADIUS*2, y, item.width).addTo(self)
                (Path(x + item.width + ARC_RADIUS*2, y + item.height)
                    .right(itemSpace + ARC_RADIUS)
                    .addTo(self))
                # Lower skip
                (Path(x,y)
                    .arc('ne')
                    .down(item.height + max(item.down + VERTICAL_SEPARATION, ARC_RADIUS*2) - ARC_RADIUS*2)
                    .arc('ws')
                    .right(itemWidth - ARC_RADIUS)
                    .arc('se')
                    .up(item.down + VERTICAL_SEPARATION - ARC_RADIUS*2)
                    .arc('wn')
                    .addTo(self))
                x += ARC_RADIUS*2 + max(itemWidth, ARC_RADIUS) + ARC_RADIUS
                y += item.height
            else:
                # Straight line
                (Path(x, y)
                    .right(ARC_RADIUS*2)
                    .addTo(self))
                item.format(x + ARC_RADIUS*2, y, item.width).addTo(self)
                (Path(x + ARC_RADIUS*2 + item.width, y + item.height)
                    .right(itemSpace + ARC_RADIUS)
                    .addTo(self))
                # Lower skip
                (Path(x,y)
                    .arc('ne')
                    .down(item.height + max(item.down + VERTICAL_SEPARATION, ARC_RADIUS*2) - ARC_RADIUS*2)
                    .arc('ws')
                    .right(itemWidth - ARC_RADIUS)
                    .arc('se')
                    .up(item.down + VERTICAL_SEPARATION - ARC_RADIUS*2)
                    .arc('wn')
                    .addTo(self))
        return self


class Choice(DiagramItem):
    def __init__(self, default, *items):
        DiagramItem.__init__(self, 'g')
        assert default < len(items)
        self.default = default
        self.items = [wrapString(item) for item in items]
        self.width = ARC_RADIUS * 4 + max(item.width for item in self.items)
        self.up = self.items[0].up;
        self.down = self.items[-1].down;
        self.height = self.items[default].height
        for i, item in enumerate(self.items):
            if i in [default-1, default+1]:
                arcs = ARC_RADIUS*2
            else:
                arcs = ARC_RADIUS
            if i < default:
                self.up += max(arcs, item.height + item.down + VERTICAL_SEPARATION + self.items[i+1].up)
            elif i == default:
                continue
            else:
                self.down += max(arcs, item.up + VERTICAL_SEPARATION + self.items[i-1].down + self.items[i-1].height)
        self.down -= self.items[default].height # already counted in self.height
        if DEBUG:
            self.attrs['data-updown'] = "{0} {1} {2}".format(self.up, self.height, self.down)
            self.attrs['data-type'] = "choice"

    def __repr__(self):
        items = ', '.join(repr(item) for item in self.items)
        return 'Choice(%r, %s)' % (self.default, items)

    def format(self, x, y, width):
        leftGap, rightGap = determineGaps(width, self.width)

        # Hook up the two sides if self is narrower than its stated width.
        Path(x, y).h(leftGap).addTo(self)
        Path(x + leftGap + self.width, y + self.height).h(rightGap).addTo(self)
        x += leftGap

        innerWidth = self.width - ARC_RADIUS * 4
        default = self.items[self.default]

        # Do the elements that curve above
        above = self.items[:self.default][::-1]
        if above:
            distanceFromY = max(
                ARC_RADIUS * 2,
                default.up
                    + VERTICAL_SEPARATION
                    + above[0].down
                    + above[0].height)
        for i,ni,item in doubleenumerate(above):
            Path(x, y).arc('se').up(distanceFromY - ARC_RADIUS * 2).arc('wn').addTo(self)
            item.format(x + ARC_RADIUS * 2, y - distanceFromY, innerWidth).addTo(self)
            Path(x + ARC_RADIUS * 2 + innerWidth, y - distanceFromY + item.height).arc('ne') \
                .down(distanceFromY - item.height + default.height - ARC_RADIUS*2).arc('ws').addTo(self)
            if ni < -1:
                distanceFromY += max(
                    ARC_RADIUS,
                    item.up
                        + VERTICAL_SEPARATION
                        + above[i+1].down
                        + above[i+1].height)

        # Do the straight-line path.
        Path(x, y).right(ARC_RADIUS * 2).addTo(self)
        self.items[self.default].format(x + ARC_RADIUS * 2, y, innerWidth).addTo(self)
        Path(x + ARC_RADIUS * 2 + innerWidth, y+self.height).right(ARC_RADIUS * 2).addTo(self)

        # Do the elements that curve below
        below = self.items[self.default + 1:]
        if below:
            distanceFromY = max(
                ARC_RADIUS * 2,
                default.height
                    + default.down
                    + VERTICAL_SEPARATION
                    + below[0].up)
        for i, item in enumerate(below):
            Path(x, y).arc('ne').down(distanceFromY - ARC_RADIUS * 2).arc('ws').addTo(self)
            item.format(x + ARC_RADIUS * 2, y + distanceFromY, innerWidth).addTo(self)
            Path(x + ARC_RADIUS * 2 + innerWidth, y + distanceFromY + item.height).arc('se') \
                .up(distanceFromY - ARC_RADIUS * 2 + item.height - default.height).arc('wn').addTo(self)
            distanceFromY += max(
                ARC_RADIUS,
                item.height
                    + item.down
                    + VERTICAL_SEPARATION
                    + (below[i + 1].up if i+1 < len(below) else 0))
        return self

class MultipleChoice(DiagramItem):
    def __init__(self, default, type, *items):
        DiagramItem.__init__(self, 'g')
        assert 0 <= default < len(items)
        assert type in ["any", "all"]
        self.default = default
        self.type = type
        self.needsSpace = True
        self.items = [wrapString(item) for item in items]
        self.innerWidth = max(item.width for item in self.items)
        self.width = 30 + ARC_RADIUS + self.innerWidth + ARC_RADIUS + 20
        self.up = self.items[0].up;
        self.down = self.items[-1].down;
        self.height = self.items[default].height
        for i, item in enumerate(self.items):
            if i in [default-1, default+1]:
                minimum = 10 + ARC_RADIUS
            else:
                minimum = ARC_RADIUS
            if i < default:
                self.up += max(minimum, item.height + item.down + VERTICAL_SEPARATION + self.items[i+1].up)
            elif i == default:
                continue
            else:
                self.down += max(minimum, item.up + VERTICAL_SEPARATION + self.items[i-1].down + self.items[i-1].height)
        self.down -= self.items[default].height # already counted in self.height
        if DEBUG:
            self.attrs['data-updown'] = "{0} {1} {2}".format(self.up, self.height, self.down)
            self.attrs['data-type'] = "multiplechoice"

    def __repr__(self):
        items = ', '.join(map(repr, self.items))
        return 'MultipleChoice(%r, %r, %s)' % (self.default, self.type, items)

    def format(self, x, y, width):
        leftGap, rightGap = determineGaps(width, self.width)

        # Hook up the two sides if self is narrower than its stated width.
        Path(x, y).h(leftGap).addTo(self)
        Path(x + leftGap + self.width, y + self.height).h(rightGap).addTo(self)
        x += leftGap

        default = self.items[self.default]

        # Do the elements that curve above
        above = self.items[:self.default][::-1]
        if above:
            distanceFromY = max(
                10 + ARC_RADIUS,
                default.up
                    + VERTICAL_SEPARATION
                    + above[0].down
                    + above[0].height)
        for i,ni,item in doubleenumerate(above):
            (Path(x + 30, y)
                .up(distanceFromY - ARC_RADIUS)
                .arc('wn')
                .addTo(self))
            item.format(x + 30 + ARC_RADIUS, y - distanceFromY, self.innerWidth).addTo(self)
            (Path(x + 30 + ARC_RADIUS + self.innerWidth, y - distanceFromY + item.height)
                .arc('ne')
                .down(distanceFromY - item.height + default.height - ARC_RADIUS - 10)
                .addTo(self))
            if ni < -1:
                distanceFromY += max(
                    ARC_RADIUS,
                    item.up
                        + VERTICAL_SEPARATION
                        + above[i+1].down
                        + above[i+1].height)

        # Do the straight-line path.
        Path(x + 30, y).right(ARC_RADIUS).addTo(self)
        self.items[self.default].format(x + 30 + ARC_RADIUS, y, self.innerWidth).addTo(self)
        Path(x + 30 + ARC_RADIUS + self.innerWidth, y + self.height).right(ARC_RADIUS).addTo(self)

        # Do the elements that curve below
        below = self.items[self.default + 1:]
        if below:
            distanceFromY = max(
                10 + ARC_RADIUS,
                default.height
                    + default.down
                    + VERTICAL_SEPARATION
                    + below[0].up)
        for i, item in enumerate(below):
            (Path(x+30, y)
                .down(distanceFromY - ARC_RADIUS)
                .arc('ws')
                .addTo(self))
            item.format(x + 30 + ARC_RADIUS, y + distanceFromY, self.innerWidth).addTo(self)
            (Path(x + 30 + ARC_RADIUS + self.innerWidth, y + distanceFromY + item.height)
                .arc('se')
                .up(distanceFromY - ARC_RADIUS + item.height - default.height - 10)
                .addTo(self))
            distanceFromY += max(
                ARC_RADIUS,
                item.height
                    + item.down
                    + VERTICAL_SEPARATION
                    + (below[i + 1].up if i+1 < len(below) else 0))
        text = DiagramItem('g', attrs={"class": "diagram-text"}).addTo(self)
        DiagramItem('title', text="take one or more branches, once each, in any order" if self.type=="any" else "take all branches, once each, in any order").addTo(text)
        DiagramItem('path', attrs={
            "d": "M {x} {y} h -26 a 4 4 0 0 0 -4 4 v 12 a 4 4 0 0 0 4 4 h 26 z".format(x=x+30, y=y-10),
            "class": "diagram-text"
            }).addTo(text)
        DiagramItem('text', text="1+" if self.type=="any" else "all", attrs={
            "x": x + 15,
            "y": y + 4,
            "class": "diagram-text"
            }).addTo(text)
        DiagramItem('path', attrs={
            "d": "M {x} {y} h 16 a 4 4 0 0 1 4 4 v 12 a 4 4 0 0 1 -4 4 h -16 z".format(x=x+self.width-20, y=y-10),
            "class": "diagram-text"
            }).addTo(text)
        DiagramItem('text', text=u"↺", attrs={
            "x": x + self.width - 10,
            "y": y + 4,
            "class": "diagram-arrow"
            }).addTo(text)
        return self


def Optional(item, skip=False):
    return Choice(0 if skip else 1, Skip(), item)


class OneOrMore(DiagramItem):
    def __init__(self, item, repeat=None):
        DiagramItem.__init__(self, 'g')
        repeat = repeat or Skip()
        self.item = wrapString(item)
        self.rep = wrapString(repeat)
        self.width = max(self.item.width, self.rep.width) + ARC_RADIUS * 2
        self.height = self.item.height
        self.up = self.item.up
        self.down = max(
            ARC_RADIUS * 2,
            self.item.down + VERTICAL_SEPARATION + self.rep.up + self.rep.height + self.rep.down)
        self.needsSpace = True
        if DEBUG:
            self.attrs['data-updown'] = "{0} {1} {2}".format(self.up, self.height, self.down)
            self.attrs['data-type'] = "oneormore"

    def format(self, x, y, width):
        leftGap, rightGap = determineGaps(width, self.width)

        # Hook up the two sides if self is narrower than its stated width.
        Path(x, y).h(leftGap).addTo(self)
        Path(x + leftGap + self.width, y +self.height).h(rightGap).addTo(self)
        x += leftGap

        # Draw item
        Path(x, y).right(ARC_RADIUS).addTo(self)
        self.item.format(x + ARC_RADIUS, y, self.width - ARC_RADIUS * 2).addTo(self)
        Path(x + self.width - ARC_RADIUS, y + self.height).right(ARC_RADIUS).addTo(self)

        # Draw repeat arc
        distanceFromY = max(ARC_RADIUS*2, self.item.height + self.item.down + VERTICAL_SEPARATION + self.rep.up)
        Path(x + ARC_RADIUS, y).arc('nw').down(distanceFromY - ARC_RADIUS * 2) \
            .arc('ws').addTo(self)
        self.rep.format(x + ARC_RADIUS, y + distanceFromY, self.width - ARC_RADIUS*2).addTo(self)
        Path(x + self.width - ARC_RADIUS, y + distanceFromY + self.rep.height).arc('se') \
            .up(distanceFromY - ARC_RADIUS * 2 + self.rep.height - self.item.height).arc('en').addTo(self)

        return self

    def __repr__(self):
        return 'OneOrMore(%r, repeat=%r)' % (self.item, self.rep)


def ZeroOrMore(item, repeat=None):
    result = Optional(OneOrMore(item, repeat))
    return result


class Start(DiagramItem):
    def __init__(self, type="simple"):
        DiagramItem.__init__(self, 'path')
        self.width = 20
        self.up = 10
        self.down = 10
        self.type = type
        if DEBUG:
            self.attrs['data-updown'] = "{0} {1} {2}".format(self.up, self.height, self.down)
            self.attrs['data-type'] = "start"

    def format(self, x, y, _width):
        if self.type == "simple":
            self.attrs['d'] = 'M {0} {1} v 20 m 10 -20 v 20 m -10 -10 h 20.5'.format(x, y - 10)
        elif self.type == "complex":
            self.attrs['d'] = 'M {0} {1} v 20 m 0 -10 h 20.5'
        return self

    def __repr__(self):
        return 'Start(type=%r)' % self.type


class End(DiagramItem):
    def __init__(self, type="simple"):
        DiagramItem.__init__(self, 'path')
        self.width = 20
        self.up = 10
        self.down = 10
        self.type = type
        if DEBUG:
            self.attrs['data-updown'] = "{0} {1} {2}".format(self.up, self.height, self.down)
            self.attrs['data-type'] = "end"

    def format(self, x, y, _width):
        if self.type == "simple":
            self.attrs['d'] = 'M {0} {1} h 20 m -10 -10 v 20 m 10 -20 v 20'.format(x, y)
        elif self.type == "complex":
            self.attrs['d'] = 'M {0} {1} h 20 m 0 -10 v 20'
        return self

    def __repr__(self):
        return 'End(type=%r)' % self.type


class Terminal(DiagramItem):
    def __init__(self, text, href=None):
        DiagramItem.__init__(self, 'g', {'class': 'terminal'})
        self.text = text
        self.href = href
        self.width = len(text) * CHARACTER_ADVANCE + 20
        self.up = 11
        self.down = 11
        self.needsSpace = True
        if DEBUG:
            self.attrs['data-updown'] = "{0} {1} {2}".format(self.up, self.height, self.down)
            self.attrs['data-type'] = "terminal"

    def __repr__(self):
        return 'Terminal(%r, href=%r)' % (self.text, self.href)

    def format(self, x, y, width):
        leftGap, rightGap = determineGaps(width, self.width)

        # Hook up the two sides if self is narrower than its stated width.
        Path(x, y).h(leftGap).addTo(self)
        Path(x + leftGap + self.width, y).h(rightGap).addTo(self)

        DiagramItem('rect', {'x': x + leftGap, 'y': y - 11, 'width': self.width,
                             'height': self.up + self.down, 'rx': 10, 'ry': 10}).addTo(self)
        text = DiagramItem('text', {'x': x + width / 2, 'y': y + 4}, self.text)
        if self.href is not None:
            a = DiagramItem('a', {'xlink:href':self.href}, text).addTo(self)
            text.addTo(a)
        else:
            text.addTo(self)
        return self


class NonTerminal(DiagramItem):
    def __init__(self, text, href=None):
        DiagramItem.__init__(self, 'g', {'class': 'non-terminal'})
        self.text = text
        self.href = href
        self.width = len(text) * CHARACTER_ADVANCE + 20
        self.up = 11
        self.down = 11
        self.needsSpace = True
        if DEBUG:
            self.attrs['data-updown'] = "{0} {1} {2}".format(self.up, self.height, self.down)
            self.attrs['data-type'] = "non-terminal"

    def __repr__(self):
        return 'NonTerminal(%r, href=%r)' % (self.text, self.href)

    def format(self, x, y, width):
        leftGap, rightGap = determineGaps(width, self.width)

        # Hook up the two sides if self is narrower than its stated width.
        Path(x, y).h(leftGap).addTo(self)
        Path(x + leftGap + self.width, y).h(rightGap).addTo(self)

        DiagramItem('rect', {'x': x + leftGap, 'y': y - 11, 'width': self.width,
                             'height': self.up + self.down}).addTo(self)
        text = DiagramItem('text', {'x': x + width / 2, 'y': y + 4}, self.text)
        if self.href is not None:
            a = DiagramItem('a', {'xlink:href':self.href}, text).addTo(self)
            text.addTo(a)
        else:
            text.addTo(self)
        return self


class Comment(DiagramItem):
    def __init__(self, text, href=None):
        DiagramItem.__init__(self, 'g')
        self.text = text
        self.href = href
        self.width = len(text) * 7 + 10
        self.up = 11
        self.down = 11
        self.needsSpace = True
        if DEBUG:
            self.attrs['data-updown'] = "{0} {1} {2}".format(self.up, self.height, self.down)
            self.attrs['data-type'] = "comment"

    def format(self, x, y, width):
        leftGap, rightGap = determineGaps(width, self.width)

        # Hook up the two sides if self is narrower than its stated width.
        Path(x, y).h(leftGap).addTo(self)
        Path(x + leftGap + self.width, y).h(rightGap).addTo(self)

        text = DiagramItem('text', {'x': x + width / 2, 'y': y + 5, 'class': 'comment'}, self.text)
        if self.href is not None:
            a = DiagramItem('a', {'xlink:href':self.href}, text).addTo(self)
            text.addTo(a)
        else:
            text.addTo(self)
        return self


class Skip(DiagramItem):
    def __init__(self):
        DiagramItem.__init__(self, 'g')
        self.width = 0
        self.up = 0
        self.down = 0
        if DEBUG:
            self.attrs['data-updown'] = "{0} {1} {2}".format(self.up, self.height, self.down)
            self.attrs['data-type'] = "skip"

    def format(self, x, y, width):
        Path(x, y).right(width).addTo(self)
        return self

    def __repr__(self):
        return 'Skip()'


if __name__ == '__main__':
    def add(name, diagram):
        sys.stdout.write('<h1>{0}</h1>\n'.format(e(name)))
        diagram.writeSvg(sys.stdout.write)
        sys.stdout.write('\n')

    import sys
    sys.stdout.write("<!doctype html><title>Test</title><body>")
    exec(open('css-example.py-js').read())
    sys.stdout.write('</body></html>')
