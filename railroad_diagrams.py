# Display constants
VERTICAL_SEPARATION = 8
ARC_RADIUS = 10
DIAGRAM_CLASS = 'railroad-diagram'
TRANSLATE_HALF_PIXEL = True

# Assume a monospace font with each char .5em wide, and the em is 16px
CHARACTER_ADVANCE = 8



class DiagramItem(object):
    def __init__(self, name, attrs=None, text=None):
        self.name = name
        self.attrs = attrs or {}
        self.children = [text] if text else []
        self.needs_space = False

    def format(self, x, y, width):
        raise NotImplementedError  # Virtual

    def add_to(self, parent):
        parent.children.append(self)
        return self

    def write_svg(self, write):
        write('<')
        write(self.name)
        for name, value in self.attrs.items():
            write(' ')
            write(name)
            write('="')
            write(str(value).replace('&', '&amp;').replace('"', '&quot;'))
            write('"')
        write('>\n')
        for child in self.children:
            if isinstance(child, DiagramItem):
                child.write_svg(write)
            else:
                write(child.replace('&', '&amp;').replace('<', '&lt;'))
        write('</')
        write(self.name)
        write('>\n')


class Path(DiagramItem):
    def __init__(self, x, y):
        DiagramItem.__init__(self, 'path', {'d': 'M%s %s' % (x, y)})

    def m(self, x, y):
        self.attrs['d'] += 'm%s %s' % (x, y)
        return self

    def h(self, val):
        self.attrs['d'] += 'h%s' % val
        return self

    right = h

    def left(self, val):
        return self.h(-val)

    def v(self, val):
        self.attrs['d'] += 'v%s' % val
        return self

    down = v

    def up(self, val):
        return self.v(-val)

    def arc(self, sweep):
        x = ARC_RADIUS
        y = ARC_RADIUS
        if sweep[0] == 'e' or sweep[1] == 'w':
            x *= -1
        if sweep[0] == 's' or sweep[1] == 'n':
            y *= -1
        cw = 1 if sweep == 'ne' or sweep == 'es' or sweep == 'sw' or sweep == 'wn' else 0
        self.attrs['d'] += 'a%s %s 0 0 %s %s %s' % (ARC_RADIUS, ARC_RADIUS, cw, x, y)
        return self


    def format(self):
        self.attrs['d'] += 'h.5'
        return self


def wrap_string(value):
    return value if isinstance(value, DiagramItem) else Terminal(value)


class Diagram(DiagramItem):
    def __init__(self, *items):
        DiagramItem.__init__(self, 'svg', {'class': DIAGRAM_CLASS})
        self.items = [Start()] + [wrap_string(item) for item in items] + [End()]
        self.width = 1 + sum(item.width + (20 if item.needs_space else 0)
                             for item in self.items)
        self.up = sum(item.up for item in self.items)
        self.down = sum(item.down for item in self.items)
        self.formatted = False

    def format(self, padding_top=20, padding_right=20, padding_bottom=20, padding_left=20):
        x = padding_left
        y = padding_top + self.up
        g = DiagramItem('g')
        if TRANSLATE_HALF_PIXEL:
            g.attrs['transform'] = 'translate(.5 .5)'
        for item in self.items:
            if item.needs_space:
                Path(x, y).h(10).add_to(g)
                x += 10
            item.format(x, y, item.width).add_to(g)
            x += item.width
            if item.needs_space:
                Path(x, y).h(10).add_to(g)
                x += 10
        self.attrs['width'] = self.width + padding_left + padding_right
        self.attrs['height'] = self.up + self.down + padding_top + padding_bottom
        g.add_to(self)
        self.formatted = True
        return self


    def write_svg(self, write):
        if not self.formatted:
            self.format()
        return DiagramItem.write_svg(self, write)


class Sequence(DiagramItem):
    def __init__(self, *items):
        DiagramItem.__init__(self, 'g')
        self.items = [wrap_string(item) for item in items]
        self.width = sum(item.width + (20 if item.needs_space else 0)
                         for item in self.items)
        self.up = sum(item.up for item in self.items)
        self.down = sum(item.down for item in self.items)

    def format(self, x, y, width):
        diff = width - self.width
        Path(x, y).h(diff / 2).add_to(self)
        x += diff/2
        for item in self.items:
            if item.needs_space:
                Path(x, y).h(10).add_to(self)
                x += 10
            item.format(x, y, item.width).add_to(self)
            x += item.width
            if item.needs_space:
                Path(x, y).h(10).add_to(self)
                x += 10
        Path(x, y).h(diff / 2).add_to(self)
        return self


class Choice(DiagramItem):
    def __init__(self, default, *items):
        DiagramItem.__init__(self, 'g')
        assert default < len(items)
        self.default = default
        self.items = [wrap_string(item) for item in items]
        self.width = ARC_RADIUS * 4 + max(
            item.width + (20 if item.needs_space else 0) for item in self.items)
        self.up = 0
        self.down = 0
        for i, item in enumerate(self.items):
            if i < default:
                self.up += max(ARC_RADIUS, item.up + item.down + VERTICAL_SEPARATION)
            elif i == default:
                self.up += max(ARC_RADIUS, item.up)
                self.down += max(ARC_RADIUS, item.down)
            else:
                assert i > default
                self.down += max(ARC_RADIUS, VERTICAL_SEPARATION + item.up + item.down)

    def format(self, x, y, width):
        last = len(self.items) - 1
        inner_width = self.width - ARC_RADIUS * 4

        # Hook up the two sides if self is narrower than its stated width.
        diff = width - self.width
        Path(x, y).h(diff / 2).add_to(self)
        Path(x + diff / 2 + self.width, y).h(diff / 2).add_to(self)
        x += diff / 2

        # Do the elements that curve above
        above = self.items[:self.default]
        if above:
            distance_from_y = max(
                ARC_RADIUS * 2,
                self.items[self.default].up + VERTICAL_SEPARATION
                    + self.items[self.default - 1].down)
        for i, item in list(enumerate(above))[::-1]:
            Path(x, y).arc('se').up(distance_from_y - ARC_RADIUS * 2).arc('wn').add_to(self)
            item.format(x + ARC_RADIUS * 2, y - distance_from_y, inner_width).add_to(self)
            Path(x + ARC_RADIUS * 2 + inner_width, y - distance_from_y).arc('ne') \
                .down(distance_from_y - ARC_RADIUS*2).arc('ws').add_to(self)
            distance_from_y += max(
                ARC_RADIUS, item.up + VERTICAL_SEPARATION + (
                    self.items[i - 1].down if i > 0 else 0))

        # Do the straight-line path.
        Path(x, y).right(ARC_RADIUS * 2).add_to(self)
        self.items[self.default].format(x + ARC_RADIUS * 2, y, inner_width).add_to(self)
        Path(x + ARC_RADIUS * 2 + inner_width, y).right(ARC_RADIUS * 2).add_to(self)

        # Do the elements that curve below
        below = self.items[self.default + 1:]
        distance_from_y = max(
            ARC_RADIUS * 2,
            self.items[self.default].down + VERTICAL_SEPARATION
                + self.items[self.default].up)
        for i, item in enumerate(below):
            Path(x, y).arc('ne').down(distance_from_y - ARC_RADIUS * 2).arc('ws').add_to(self)
            item.format(x + ARC_RADIUS * 2, y + distance_from_y, inner_width).add_to(self)
            Path(x + ARC_RADIUS * 2 + inner_width, y + distance_from_y).arc('se') \
                .up(distance_from_y - ARC_RADIUS * 2).arc('wn').add_to(self)
            distance_from_y += max(
                ARC_RADIUS,
                item.down + VERTICAL_SEPARATION + (
                    self.items[i + 1].up if i < len(self.items) else 0))
        return self


def Optional(item, skip=False):
    return Choice(0 if skip else 1, Skip(), item)


class OneOrMore(DiagramItem):
    def __init__(self, item, repeat=None):
        DiagramItem.__init__(self, 'g')
        repeat = repeat or Skip()
        self.item = wrap_string(item)
        self.rep = wrap_string(repeat)
        self.width = max(self.item.width, self.rep.width) + ARC_RADIUS * 2
        self.up = self.item.up
        self.down = max(
            ARC_RADIUS * 2,
            self.item.down + VERTICAL_SEPARATION + self.rep.up + self.rep.down)
        self.needs_space = True

    def format(self, x, y, width):
        # Hook up the two sides if self is narrower than its stated width.
        diff = width - self.width
        Path(x, y).h(diff / 2).add_to(self)
        Path(x + diff / 2 + self.width, y).h(diff / 2).add_to(self)
        x += diff / 2

        # Draw item
        Path(x, y).right(ARC_RADIUS).add_to(self)
        self.item.format(x + ARC_RADIUS, y, self.width - ARC_RADIUS * 2).add_to(self)
        Path(x + self.width - ARC_RADIUS, y).right(ARC_RADIUS).add_to(self)

        # Draw repeat arc
        distance_from_y = max(ARC_RADIUS*2, self.item.down + VERTICAL_SEPARATION + self.rep.up)
        Path(x + ARC_RADIUS, y).arc('nw').down(distance_from_y - ARC_RADIUS * 2) \
            .arc('ws').add_to(self)
        self.rep.format(x + ARC_RADIUS, y + distance_from_y, self.width - ARC_RADIUS*2).add_to(self)
        Path(x + self.width - ARC_RADIUS, y + distance_from_y).arc('se') \
            .up(distance_from_y - ARC_RADIUS * 2).arc('en').add_to(self)

        return self


def ZeroOrMore(item, repeat=None):
    result = Optional(OneOrMore(item, repeat))
    result.needsSpace = True  # XXX is this correct?
    return result


class Start(DiagramItem):
    def __init__(self):
        DiagramItem.__init__(self, 'path')
        self.width = 20
        self.up = 10
        self.down = 10

    def format(self, x, y, _width):
        self.attrs['d'] = 'M %s %s v 20 m 10 -20 v 20 m -10 -10 h 20.5' % (x, y - 10)
        return self


class End(DiagramItem):
    def __init__(self):
        DiagramItem.__init__(self, 'path')
        self.width = 20
        self.up = 10
        self.down = 10

    def format(self, x, y, _width):
        self.attrs['d'] = 'M %s %s h 20 m -10 -10 v 20 m 10 -20 v 20' % (x, y)
        return self


class Terminal(DiagramItem):
    def __init__(self, text):
        DiagramItem.__init__(self, 'g')
        self.text = text
        self.width = len(text) * CHARACTER_ADVANCE + 20
        self.up = 11
        self.down = 11
        self.needs_space = True

    def format(self, x, y, width):
        diff = width - self.width
        Path(x, y).right(width).add_to(self)
        DiagramItem('rect', {'x': x + diff / 2, 'y': y - 11, 'width': self.width,
                             'height': self.up + self.down, 'rx': 10, 'ry': 10}).add_to(self)
        DiagramItem('text', {'x': x + width / 2, 'y': y + 4}, self.text).add_to(self)
        return self


class NonTerminal(DiagramItem):
    def __init__(self, text):
        DiagramItem.__init__(self, 'g')
        self.text = text
        self.width = len(text) * CHARACTER_ADVANCE + 20
        self.up = 11
        self.down = 11
        self.needs_space = True

    def format(self, x, y, width):
        diff = width - self.width
        Path(x, y).right(width).add_to(self)
        DiagramItem('rect', {'x': x + diff / 2, 'y': y - 11, 'width': self.width,
                             'height': self.up + self.down}).add_to(self)
        DiagramItem('text', {'x': x + width / 2, 'y': y + 4}, self.text).add_to(self)
        return self


class Comment(DiagramItem):
    def __init__(self, text):
        DiagramItem.__init__(self, 'g')
        self.text = text
        self.width = len(text) * 7 + 10
        self.up = 11
        self.down = 11
        self.needs_space = True

    def format(self, x, y, width):
        diff = width - self.width
        Path(x, y).right(diff / 2).add_to(self)
        Path(x + diff / 2 + self.width, y).right(diff / 2).add_to(self)
        DiagramItem('text', {'x': x + width / 2, 'y': y + 5, 'class': 'comment'}, self.text).add_to(self)
        return self


class Skip(DiagramItem):
    def __init__(self):
        DiagramItem.__init__(self, 'g')
        self.width = 0
        self.up = 0
        self.down = 0

    def format(self, x, y, width):
        Path(x, y).right(width).add_to(self)
        return self


if __name__ == '__main__':
    def add(name, diagram):
        sys.stdout.write('%s\n' % name)
        diagram.write_svg(sys.stdout.write)
        sys.stdout.write('\n')

    import sys
    exec(open('css-example.py-js').read())
