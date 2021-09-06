# -*- coding: utf-8 -*-
from __future__ import division, unicode_literals
import sys
import math as Math

if sys.version_info >= (3, ):
	unicode = str

# Display constants
DEBUG = False # if true, writes some debug information into attributes
VS = 8 # minimum vertical separation between things. For a 3px stroke, must be at least 4
AR = 10 # radius of arcs
DIAGRAM_CLASS = 'railroad-diagram' # class to put on the root <svg>
STROKE_ODD_PIXEL_LENGTH = True # is the stroke width an odd (1px, 3px, etc) pixel length?
INTERNAL_ALIGNMENT = 'center' # how to align items when they have extra space. left/right/center
CHAR_WIDTH = 8.5 # width of each monospace character. play until you find the right value for your font
COMMENT_CHAR_WIDTH = 7 # comments are in smaller text by default


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

def addDebug(el):
	if not DEBUG:
		return
	el.attrs['data-x'] = "{0} w:{1} h:{2}/{3}/{4}".format(type(el).__name__, el.width, el.up, el.height, el.down)



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

	def walk(self, cb):
		cb(self)

	def __eq__(self, other):
		return type(self) == type(other) and self.__dict__ == other.__dict__

	def __ne__(self, other):
		return not (self == other)


class DiagramMultiContainer(DiagramItem):
	def __init__(self, name, items, attrs=None, text=None):
		DiagramItem.__init__(self, name, attrs, text)
		self.items = [wrapString(item) for item in items]

	def walk(self, cb):
		cb(self)
		for item in self.items:
			item.walk(cb)


class Path(DiagramItem):
	def __init__(self, x, y):
		self.x = x
		self.y = y
		DiagramItem.__init__(self, 'path', {'d': 'M%s %s' % (x, y)})

	def m(self, x, y):
		self.attrs['d'] += 'm{0} {1}'.format(x,y)
		return self

	def l(self, x, y):
		self.attrs['d'] += 'l{0} {1}'.format(x,y)
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

	def arc_8(self, start, dir):
		# 1/8 of a circle
		arc = AR
		s2 = 1/Math.sqrt(2) * arc
		s2inv = (arc - s2)
		path = "a {0} {0} 0 0 {1} ".format(arc, "1" if dir == 'cw' else "0")
		sd = start+dir
		if sd == 'ncw':
			offset = [s2, s2inv]
		elif sd == 'necw':
			offset = [s2inv, s2]
		elif sd == 'ecw':
			offset = [-s2inv, s2]
		elif sd == 'secw':
			offset = [-s2, s2inv]
		elif sd == 'scw':
			offset = [-s2, -s2inv]
		elif sd == 'swcw':
			offset = [-s2inv, -s2]
		elif sd == 'wcw':
			offset = [s2inv, -s2]
		elif sd == 'nwcw':
			offset = [s2, -s2inv]
		elif sd == 'nccw':
			offset = [-s2, s2inv]
		elif sd == 'nwccw':
			offset = [-s2inv, s2]
		elif sd == 'wccw':
			offset = [s2inv, s2]
		elif sd == 'swccw':
			offset = [s2, s2inv]
		elif sd == 'sccw':
			offset = [s2, -s2inv]
		elif sd == 'seccw':
			offset = [s2inv, -s2]
		elif sd == 'eccw':
			offset = [-s2inv, -s2]
		elif sd == 'neccw':
			offset = [-s2, -s2inv]

		path += " ".join(str(x) for x in offset)
		self.attrs['d'] += path
		return self

	def arc(self, sweep):
		x = AR
		y = AR
		if sweep[0] == 'e' or sweep[1] == 'w':
			x *= -1
		if sweep[0] == 's' or sweep[1] == 'n':
			y *= -1
		cw = 1 if sweep == 'ne' or sweep == 'es' or sweep == 'sw' or sweep == 'wn' else 0
		self.attrs['d'] += 'a{0} {0} 0 0 {1} {2} {3}'.format(AR, cw, x, y)
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
	svg.railroad-diagram rect.group-box {
		stroke: gray;
		stroke-dasharray: 10 5;
		fill: none;
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
		return 'Style(%r)' % self.css

	def format(self, x, y, width):
		return self

	def writeSvg(self, write):
		# Write included stylesheet as CDATA. See https:#developer.mozilla.org/en-US/docs/Web/SVG/Element/style
		cdata = u'/* <![CDATA[ */\n{css}\n/* ]]> */\n'.format(css=self.css)
		write(u'<style>{cdata}</style>'.format(cdata=cdata))


class Diagram(DiagramMultiContainer):
	def __init__(self, *items, **kwargs):
		# Accepts a type=[simple|complex] kwarg
		DiagramMultiContainer.__init__(
			self,
			'svg',
			items,
			{'class': DIAGRAM_CLASS, 'xmlns': "http://www.w3.org/2000/svg",
				'xmlns:xlink': "http://www.w3.org/1999/xlink"}
		)
		self.type = kwargs.get("type", "simple")
		if items and not isinstance(items[0], Start):
			self.items.insert(0, Start(self.type))
		if items and not isinstance(items[-1], End):
			self.items.append(End(self.type))
		self.css = kwargs.get("css", DEFAULT_STYLE)
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
		if STROKE_ODD_PIXEL_LENGTH:
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


class Sequence(DiagramMultiContainer):
	def __init__(self, *items):
		DiagramMultiContainer.__init__(self, 'g', items)
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


class Stack(DiagramMultiContainer):
	def __init__(self, *items):
		DiagramMultiContainer.__init__(self, 'g', items)
		self.needsSpace = True
		self.width = max(item.width + (20 if item.needsSpace else 0) for item in self.items)
		# pretty sure that space calc is totes wrong
		if len(self.items) > 1:
			self.width += AR*2
		self.up = self.items[0].up
		self.down = self.items[-1].down
		self.height = 0
		last = len(self.items) - 1
		for i,item in enumerate(self.items):
			self.height += item.height
			if i > 0:
				self.height += max(AR*2, item.up + VS)
			if i < last:
				self.height += max(AR*2, item.down + VS)
		addDebug(self)

	def __repr__(self):
		items = ', '.join(repr(item) for item in self.items)
		return 'Stack(%s)' % items

	def format(self, x, y, width):
		leftGap, rightGap = determineGaps(width, self.width)
		Path(x, y).h(leftGap).addTo(self)
		x += leftGap
		xInitial = x
		if len(self.items) > 1:
			Path(x, y).h(AR).addTo(self)
			x += AR
			innerWidth = self.width - AR*2
		else:
			innerWidth = self.width
		for i,item in enumerate(self.items):
			item.format(x, y, innerWidth).addTo(self)
			x += innerWidth
			y += item.height
			if i != len(self.items)-1:
				(Path(x,y)
					.arc('ne').down(max(0, item.down + VS - AR*2))
					.arc('es').left(innerWidth)
					.arc('nw').down(max(0, self.items[i+1].up + VS - AR*2))
					.arc('ws').addTo(self))
				y += max(item.down + VS, AR*2) + max(self.items[i+1].up + VS, AR*2)
				x = xInitial + AR
		if len(self.items) > 1:
			Path(x, y).h(AR).addTo(self)
			x += AR
		Path(x, y).h(rightGap).addTo(self)
		return self


class OptionalSequence(DiagramMultiContainer):
	def __new__(cls, *items):
		if len(items) <= 1:
			return Sequence(*items)
		else:
			return super(OptionalSequence, cls).__new__(cls)

	def __init__(self, *items):
		DiagramMultiContainer.__init__(self, 'g', items)
		self.needsSpace = False
		self.width = 0
		self.up = 0
		self.height = sum(item.height for item in self.items)
		self.down = self.items[0].down
		heightSoFar = 0
		for i,item in enumerate(self.items):
			self.up = max(self.up, max(AR * 2, item.up + VS) - heightSoFar)
			heightSoFar += item.height
			if i > 0:
				self.down = max(self.height + self.down, heightSoFar + max(AR*2, item.down + VS)) - self.height
			itemWidth = item.width + (10 if item.needsSpace else 0)
			if i == 0:
				self.width += AR + max(itemWidth, AR)
			else:
				self.width += AR*2 + max(itemWidth, AR) + AR
		addDebug(self)

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
					.up(y - upperLineY - AR*2)
					.arc('wn')
					.right(itemWidth - AR)
					.arc('ne')
					.down(y + item.height - upperLineY - AR*2)
					.arc('ws')
					.addTo(self))
				# Straight line
				(Path(x, y)
					.right(itemSpace + AR)
					.addTo(self))
				item.format(x + itemSpace + AR, y, item.width).addTo(self)
				x += itemWidth + AR
				y += item.height
			elif i < last:
				# Upper skip
				(Path(x, upperLineY)
					.right(AR*2 + max(itemWidth, AR) + AR)
					.arc('ne')
					.down(y - upperLineY + item.height - AR*2)
					.arc('ws')
					.addTo(self))
				# Straight line
				(Path(x,y)
					.right(AR*2)
					.addTo(self))
				item.format(x + AR*2, y, item.width).addTo(self)
				(Path(x + item.width + AR*2, y + item.height)
					.right(itemSpace + AR)
					.addTo(self))
				# Lower skip
				(Path(x,y)
					.arc('ne')
					.down(item.height + max(item.down + VS, AR*2) - AR*2)
					.arc('ws')
					.right(itemWidth - AR)
					.arc('se')
					.up(item.down + VS - AR*2)
					.arc('wn')
					.addTo(self))
				x += AR*2 + max(itemWidth, AR) + AR
				y += item.height
			else:
				# Straight line
				(Path(x, y)
					.right(AR*2)
					.addTo(self))
				item.format(x + AR*2, y, item.width).addTo(self)
				(Path(x + AR*2 + item.width, y + item.height)
					.right(itemSpace + AR)
					.addTo(self))
				# Lower skip
				(Path(x,y)
					.arc('ne')
					.down(item.height + max(item.down + VS, AR*2) - AR*2)
					.arc('ws')
					.right(itemWidth - AR)
					.arc('se')
					.up(item.down + VS - AR*2)
					.arc('wn')
					.addTo(self))
		return self

class AlternatingSequence(DiagramMultiContainer):
	def __new__(cls, *items):
		if len(items) == 2:
			return super(AlternatingSequence, cls).__new__(cls)
		else:
			raise Exception("AlternatingSequence takes exactly two arguments, but got {0} arguments.".format(len(items)))

	def __init__(self, *items):
		DiagramMultiContainer.__init__(self, 'g', items)
		self.needsSpace = False

		arc = AR
		vert = VS
		first = self.items[0]
		second = self.items[1]

		arcX = 1 / Math.sqrt(2) * arc * 2
		arcY = (1 - 1 / Math.sqrt(2)) * arc * 2
		crossY = max(arc, vert)
		crossX = (crossY - arcY) + arcX

		firstOut = max(arc + arc, crossY/2 + arc + arc, crossY/2 + vert + first.down)
		self.up = firstOut + first.height + first.up

		secondIn = max(arc + arc, crossY/2 + arc + arc, crossY/2 + vert + second.up)
		self.down = secondIn + second.height + second.down

		self.height = 0

		firstWidth = (20 if first.needsSpace else 0) + first.width
		secondWidth = (20 if second.needsSpace else 0) + second.width
		self.width = 2*arc + max(firstWidth, crossX, secondWidth) + 2*arc
		addDebug(self)

	def __repr__(self):
		items = ', '.join(repr(item) for item in self.items)
		return 'AlternatingSequence(%s)' % items

	def format(self, x, y, width):
		arc = AR
		gaps = determineGaps(width, self.width)
		Path(x,y).right(gaps[0]).addTo(self)
		x += gaps[0]
		Path(x+self.width, y).right(gaps[1]).addTo(self)
		# bounding box
		# Path(x+gaps[0], y).up(self.up).right(self.width).down(self.up+self.down).left(self.width).up(self.down).addTo(self)
		first = self.items[0]
		second = self.items[1]

		# top
		firstIn = self.up - first.up
		firstOut = self.up - first.up - first.height
		Path(x,y).arc('se').up(firstIn-2*arc).arc('wn').addTo(self)
		first.format(x + 2*arc, y - firstIn, self.width - 4*arc).addTo(self)
		Path(x + self.width - 2*arc, y - firstOut).arc('ne').down(firstOut - 2*arc).arc('ws').addTo(self)

		# bottom
		secondIn = self.down - second.down - second.height
		secondOut = self.down - second.down
		Path(x,y).arc('ne').down(secondIn - 2*arc).arc('ws').addTo(self)
		second.format(x + 2*arc, y + secondIn, self.width - 4*arc).addTo(self)
		Path(x + self.width - 2*arc, y + secondOut).arc('se').up(secondOut - 2*arc).arc('wn').addTo(self)

		# crossover
		arcX = 1 / Math.sqrt(2) * arc * 2
		arcY = (1 - 1 / Math.sqrt(2)) * arc * 2
		crossY = max(arc, VS)
		crossX = (crossY - arcY) + arcX
		crossBar = (self.width - 4*arc - crossX)/2
		(Path(x+arc, y - crossY/2 - arc).arc('ws').right(crossBar)
			.arc_8('n', 'cw').l(crossX - arcX, crossY - arcY).arc_8('sw', 'ccw')
			.right(crossBar).arc('ne').addTo(self))
		(Path(x+arc, y + crossY/2 + arc).arc('wn').right(crossBar)
			.arc_8('s', 'ccw').l(crossX - arcX, -(crossY - arcY)).arc_8('nw', 'cw')
			.right(crossBar).arc('se').addTo(self))

		return self


class Choice(DiagramMultiContainer):
	def __init__(self, default, *items):
		DiagramMultiContainer.__init__(self, 'g', items)
		assert default < len(items)
		self.default = default
		self.width = AR * 4 + max(item.width for item in self.items)
		self.up = self.items[0].up
		self.down = self.items[-1].down
		self.height = self.items[default].height
		for i, item in enumerate(self.items):
			if i in [default-1, default+1]:
				arcs = AR*2
			else:
				arcs = AR
			if i < default:
				self.up += max(arcs, item.height + item.down + VS + self.items[i+1].up)
			elif i == default:
				continue
			else:
				self.down += max(arcs, item.up + VS + self.items[i-1].down + self.items[i-1].height)
		self.down -= self.items[default].height # already counted in self.height
		addDebug(self)

	def __repr__(self):
		items = ', '.join(repr(item) for item in self.items)
		return 'Choice(%r, %s)' % (self.default, items)

	def format(self, x, y, width):
		leftGap, rightGap = determineGaps(width, self.width)

		# Hook up the two sides if self is narrower than its stated width.
		Path(x, y).h(leftGap).addTo(self)
		Path(x + leftGap + self.width, y + self.height).h(rightGap).addTo(self)
		x += leftGap

		innerWidth = self.width - AR * 4
		default = self.items[self.default]

		# Do the elements that curve above
		above = self.items[:self.default][::-1]
		if above:
			distanceFromY = max(
				AR * 2,
				default.up
					+ VS
					+ above[0].down
					+ above[0].height)
		for i,ni,item in doubleenumerate(above):
			Path(x, y).arc('se').up(distanceFromY - AR * 2).arc('wn').addTo(self)
			item.format(x + AR * 2, y - distanceFromY, innerWidth).addTo(self)
			Path(x + AR * 2 + innerWidth, y - distanceFromY + item.height).arc('ne') \
				.down(distanceFromY - item.height + default.height - AR*2).arc('ws').addTo(self)
			if ni < -1:
				distanceFromY += max(
					AR,
					item.up
						+ VS
						+ above[i+1].down
						+ above[i+1].height)

		# Do the straight-line path.
		Path(x, y).right(AR * 2).addTo(self)
		self.items[self.default].format(x + AR * 2, y, innerWidth).addTo(self)
		Path(x + AR * 2 + innerWidth, y+self.height).right(AR * 2).addTo(self)

		# Do the elements that curve below
		below = self.items[self.default + 1:]
		if below:
			distanceFromY = max(
				AR * 2,
				default.height
					+ default.down
					+ VS
					+ below[0].up)
		for i, item in enumerate(below):
			Path(x, y).arc('ne').down(distanceFromY - AR * 2).arc('ws').addTo(self)
			item.format(x + AR * 2, y + distanceFromY, innerWidth).addTo(self)
			Path(x + AR * 2 + innerWidth, y + distanceFromY + item.height).arc('se') \
				.up(distanceFromY - AR * 2 + item.height - default.height).arc('wn').addTo(self)
			distanceFromY += max(
				AR,
				item.height
					+ item.down
					+ VS
					+ (below[i + 1].up if i+1 < len(below) else 0))
		return self


class MultipleChoice(DiagramMultiContainer):
	def __init__(self, default, type, *items):
		DiagramMultiContainer.__init__(self, 'g', items)
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
			if i in [default-1, default+1]:
				minimum = 10 + AR
			else:
				minimum = AR
			if i < default:
				self.up += max(minimum, item.height + item.down + VS + self.items[i+1].up)
			elif i == default:
				continue
			else:
				self.down += max(minimum, item.up + VS + self.items[i-1].down + self.items[i-1].height)
		self.down -= self.items[default].height # already counted in self.height
		addDebug(self)

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
				10 + AR,
				default.up
					+ VS
					+ above[0].down
					+ above[0].height)
		for i,ni,item in doubleenumerate(above):
			(Path(x + 30, y)
				.up(distanceFromY - AR)
				.arc('wn')
				.addTo(self))
			item.format(x + 30 + AR, y - distanceFromY, self.innerWidth).addTo(self)
			(Path(x + 30 + AR + self.innerWidth, y - distanceFromY + item.height)
				.arc('ne')
				.down(distanceFromY - item.height + default.height - AR - 10)
				.addTo(self))
			if ni < -1:
				distanceFromY += max(
					AR,
					item.up
						+ VS
						+ above[i+1].down
						+ above[i+1].height)

		# Do the straight-line path.
		Path(x + 30, y).right(AR).addTo(self)
		self.items[self.default].format(x + 30 + AR, y, self.innerWidth).addTo(self)
		Path(x + 30 + AR + self.innerWidth, y + self.height).right(AR).addTo(self)

		# Do the elements that curve below
		below = self.items[self.default + 1:]
		if below:
			distanceFromY = max(
				10 + AR,
				default.height
					+ default.down
					+ VS
					+ below[0].up)
		for i, item in enumerate(below):
			(Path(x+30, y)
				.down(distanceFromY - AR)
				.arc('ws')
				.addTo(self))
			item.format(x + 30 + AR, y + distanceFromY, self.innerWidth).addTo(self)
			(Path(x + 30 + AR + self.innerWidth, y + distanceFromY + item.height)
				.arc('se')
				.up(distanceFromY - AR + item.height - default.height - 10)
				.addTo(self))
			distanceFromY += max(
				AR,
				item.height
					+ item.down
					+ VS
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


class HorizontalChoice(DiagramMultiContainer):
	def __new__(cls, *items):
		if len(items) <= 1:
			return Sequence(*items)
		else:
			return super(HorizontalChoice, cls).__new__(cls)

	def __init__(self, *items):
		DiagramMultiContainer.__init__(self, 'g', items)
		allButLast = self.items[:-1]
		middles = self.items[1:-1]
		first = self.items[0]
		last = self.items[-1]
		self.needsSpace = False

		self.width = (AR # starting track
			+ AR*2 * (len(self.items)-1) # inbetween tracks
			+ sum(x.width + (20 if x.needsSpace else 0) for x in self.items) #items
			+ (AR if last.height > 0 else 0) # needs space to curve up
			+ AR) #ending track

		# Always exits at entrance height
		self.height = 0

		# All but the last have a track running above them
		self._upperTrack = max(
			AR*2,
			VS,
			max(x.up for x in allButLast) + VS
		)
		self.up = max(self._upperTrack, last.up)

		# All but the first have a track running below them
		# Last either straight-lines or curves up, so has different calculation
		self._lowerTrack = max(
			VS,
			max(x.height+max(x.down+VS, AR*2) for x in middles) if middles else 0,
			last.height + last.down + VS
		)
		if first.height < self._lowerTrack:
			# Make sure there's at least 2*AR room between first exit and lower track
			self._lowerTrack = max(self._lowerTrack, first.height + AR*2)
		self.down = max(self._lowerTrack, first.height + first.down)

		addDebug(self)

	def format(self, x, y, width):
		# Hook up the two sides if self is narrower than its stated width.
		leftGap, rightGap = determineGaps(width, self.width)
		Path(x, y).h(leftGap).addTo(self)
		Path(x + leftGap + self.width, y + self.height).h(rightGap).addTo(self)
		x += leftGap

		first = self.items[0]
		last = self.items[-1]

		# upper track
		upperSpan = (sum(x.width+(20 if x.needsSpace else 0) for x in self.items[:-1])
			+ (len(self.items) - 2) * AR*2
			- AR)
		(Path(x,y)
			.arc('se')
			.up(self._upperTrack - AR*2)
			.arc('wn')
			.h(upperSpan)
			.addTo(self))

		# lower track
		lowerSpan = (sum(x.width+(20 if x.needsSpace else 0) for x in self.items[1:])
			+ (len(self.items) - 2) * AR*2
			+ (AR if last.height > 0 else 0)
			- AR)
		lowerStart = x + AR + first.width+(20 if first.needsSpace else 0) + AR*2
		(Path(lowerStart, y+self._lowerTrack)
			.h(lowerSpan)
			.arc('se')
			.up(self._lowerTrack - AR*2)
			.arc('wn')
			.addTo(self))

		# Items
		for [i, item] in enumerate(self.items):
			# input track
			if i == 0:
				(Path(x,y)
					.h(AR)
					.addTo(self))
				x += AR
			else:
				(Path(x, y - self._upperTrack)
					.arc('ne')
					.v(self._upperTrack - AR*2)
					.arc('ws')
					.addTo(self))
				x += AR*2

			# item
			itemWidth = item.width + (20 if item.needsSpace else 0)
			item.format(x, y, itemWidth).addTo(self)
			x += itemWidth

			# output track
			if i == len(self.items)-1:
				if item.height == 0:
					(Path(x,y)
						.h(AR)
						.addTo(self))
				else:
					(Path(x,y+item.height)
						.arc('se')
						.addTo(self))
			elif i == 0 and item.height > self._lowerTrack:
				# Needs to arc up to meet the lower track, not down.
				if item.height - self._lowerTrack >= AR*2:
					(Path(x, y+item.height)
						.arc('se')
						.v(self._lowerTrack - item.height + AR*2)
						.arc('wn')
						.addTo(self))
				else:
					# Not enough space to fit two arcs
					# so just bail and draw a straight line for now.
					(Path(x, y+item.height)
						.l(AR*2, self._lowerTrack - item.height)
						.addTo(self))
			else:
				(Path(x, y+item.height)
					.arc('ne')
					.v(self._lowerTrack - item.height - AR*2)
					.arc('ws')
					.addTo(self))
		return self


def Optional(item, skip=False):
	return Choice(0 if skip else 1, Skip(), item)


class OneOrMore(DiagramItem):
	def __init__(self, item, repeat=None):
		DiagramItem.__init__(self, 'g')
		self.item = wrapString(item)
		repeat = repeat or Skip()
		self.rep = wrapString(repeat)
		self.width = max(self.item.width, self.rep.width) + AR * 2
		self.height = self.item.height
		self.up = self.item.up
		self.down = max(
			AR * 2,
			self.item.down + VS + self.rep.up + self.rep.height + self.rep.down)
		self.needsSpace = True
		addDebug(self)

	def format(self, x, y, width):
		leftGap, rightGap = determineGaps(width, self.width)

		# Hook up the two sides if self is narrower than its stated width.
		Path(x, y).h(leftGap).addTo(self)
		Path(x + leftGap + self.width, y +self.height).h(rightGap).addTo(self)
		x += leftGap

		# Draw item
		Path(x, y).right(AR).addTo(self)
		self.item.format(x + AR, y, self.width - AR * 2).addTo(self)
		Path(x + self.width - AR, y + self.height).right(AR).addTo(self)

		# Draw repeat arc
		distanceFromY = max(AR*2, self.item.height + self.item.down + VS + self.rep.up)
		Path(x + AR, y).arc('nw').down(distanceFromY - AR * 2) \
			.arc('ws').addTo(self)
		self.rep.format(x + AR, y + distanceFromY, self.width - AR*2).addTo(self)
		Path(x + self.width - AR, y + distanceFromY + self.rep.height).arc('se') \
			.up(distanceFromY - AR * 2 + self.rep.height - self.item.height).arc('en').addTo(self)

		return self

	def walk(self, cb):
		cb(self)
		self.item.walk(cb)
		self.rep.walk(cb)

	def __repr__(self):
		return 'OneOrMore(%r, repeat=%r)' % (self.item, self.rep)


def ZeroOrMore(item, repeat=None, skip=False):
	result = Optional(OneOrMore(item, repeat), skip)
	return result




class Group(DiagramItem):
	def __init__(self, item, label):
		DiagramItem.__init__(self, 'g')
		self.item = wrapString(item)
		if isinstance(label, DiagramItem):
			self.label = label
		elif label:
			self.label = Comment(label)
		else:
			self.label = None

		self.width = max(
			self.item.width + (20 if self.item.needsSpace else 0),
			self.label.width if self.label else 0,
			AR*2)
		self.height = self.item.height
		self.boxUp = max(self.item.up + VS, AR)
		self.up = self.boxUp
		if self.label:
			self.up += self.label.up + self.label.height + self.label.down
		self.down = max(self.item.down + VS, AR)
		self.needsSpace = True
		addDebug(self)

	def format(self, x, y, width):
		leftGap, rightGap = determineGaps(width, self.width)
		Path(x,y).h(leftGap).addTo(self)
		Path(x+leftGap+self.width,y+self.height).h(rightGap).addTo(self)
		x += leftGap

		DiagramItem('rect', {
			"x":x,
			"y":y-self.boxUp,
			"width":self.width,
			"height":self.boxUp + self.height + self.down,
			"rx": AR,
			"ry": AR,
			'class':'group-box',
		}).addTo(self)

		self.item.format(x,y,self.width).addTo(self)
		if self.label:
			self.label.format(
				x,
				y-(self.boxUp+self.label.down+self.label.height),
				self.label.width).addTo(self)

		return self

	def walk(self, cb):
		cb(self)
		self.item.walk(cb)
		self.label.walk(cb)


class Start(DiagramItem):
	def __init__(self, type="simple", label=None):
		DiagramItem.__init__(self, 'g')
		if label:
			self.width = max(20, len(label) * CHAR_WIDTH + 10)
		else:
			self.width = 20
		self.up = 10
		self.down = 10
		self.type = type
		self.label = label
		addDebug(self)

	def format(self, x, y, _width):
		path = Path(x, y-10)
		if self.type == "complex":
			path.down(20).m(0, -10).right(self.width).addTo(self)
		else:
			path.down(20).m(10, -20).down(20).m(-10, -10).right(self.width).addTo(self)
		if self.label:
			DiagramItem('text', attrs={"x":x, "y":y-15, "style":"text-anchor:start"}, text=self.label).addTo(self)
		return self

	def __repr__(self):
		return 'Start(type=%r, label=%r)' % (self.type, self.label)


class End(DiagramItem):
	def __init__(self, type="simple"):
		DiagramItem.__init__(self, 'path')
		self.width = 20
		self.up = 10
		self.down = 10
		self.type = type
		addDebug(self)

	def format(self, x, y, _width):
		if self.type == "simple":
			self.attrs['d'] = 'M {0} {1} h 20 m -10 -10 v 20 m 10 -20 v 20'.format(x, y)
		elif self.type == "complex":
			self.attrs['d'] = 'M {0} {1} h 20 m 0 -10 v 20'.format(x, y)
		return self

	def __repr__(self):
		return 'End(type=%r)' % self.type


class Terminal(DiagramItem):
	def __init__(self, text, href=None, title=None, cls=""):
		DiagramItem.__init__(self, 'g', {'class': ' '.join(['terminal', cls])})
		self.text = text
		self.href = href
		self.title = title
		self.cls = cls
		self.width = len(text) * CHAR_WIDTH + 20
		self.up = 11
		self.down = 11
		self.needsSpace = True
		addDebug(self)

	def __repr__(self):
		return 'Terminal(%r, href=%r, title=%r)' % (self.text, self.href, self.title)

	def format(self, x, y, width):
		leftGap, rightGap = determineGaps(width, self.width)

		# Hook up the two sides if self is narrower than its stated width.
		Path(x, y).h(leftGap).addTo(self)
		Path(x + leftGap + self.width, y).h(rightGap).addTo(self)

		DiagramItem('rect', {'x': x + leftGap, 'y': y - 11, 'width': self.width,
							 'height': self.up + self.down, 'rx': 10, 'ry': 10}).addTo(self)
		text = DiagramItem('text', {'x': x + leftGap + self.width / 2, 'y': y + 4}, self.text)
		if self.href is not None:
			a = DiagramItem('a', {'xlink:href':self.href}, text).addTo(self)
			text.addTo(a)
		else:
			text.addTo(self)
		if self.title is not None:
			DiagramItem('title', {}, self.title).addTo(self)
		return self


class NonTerminal(DiagramItem):
	def __init__(self, text, href=None, title=None, cls=""):
		DiagramItem.__init__(self, 'g', {'class': ' '.join(['non-terminal', cls])})
		self.text = text
		self.href = href
		self.title = title
		self.cls = cls
		self.width = len(text) * CHAR_WIDTH + 20
		self.up = 11
		self.down = 11
		self.needsSpace = True
		addDebug(self)

	def __repr__(self):
		return 'NonTerminal(%r, href=%r, title=%r)' % (self.text, self.href, self.title)

	def format(self, x, y, width):
		leftGap, rightGap = determineGaps(width, self.width)

		# Hook up the two sides if self is narrower than its stated width.
		Path(x, y).h(leftGap).addTo(self)
		Path(x + leftGap + self.width, y).h(rightGap).addTo(self)

		DiagramItem('rect', {'x': x + leftGap, 'y': y - 11, 'width': self.width,
							 'height': self.up + self.down}).addTo(self)
		text = DiagramItem('text', {'x': x + leftGap + self.width / 2, 'y': y + 4}, self.text)
		if self.href is not None:
			a = DiagramItem('a', {'xlink:href':self.href}, text).addTo(self)
			text.addTo(a)
		else:
			text.addTo(self)
		if self.title is not None:
			DiagramItem('title', {}, self.title).addTo(self)
		return self


class Comment(DiagramItem):
	def __init__(self, text, href=None, title=None, cls=""):
		DiagramItem.__init__(self, 'g', {'class': ' '.join(['non-terminal', cls])})
		self.text = text
		self.href = href
		self.title = title
		self.cls = cls
		self.width = len(text) * COMMENT_CHAR_WIDTH + 10
		self.up = 8
		self.down = 8
		self.needsSpace = True
		addDebug(self)

	def __repr__(self):
		return 'Comment(%r, href=%r, title=%r)' % (self.text, self.href, self.title)

	def format(self, x, y, width):
		leftGap, rightGap = determineGaps(width, self.width)

		# Hook up the two sides if self is narrower than its stated width.
		Path(x, y).h(leftGap).addTo(self)
		Path(x + leftGap + self.width, y).h(rightGap).addTo(self)

		text = DiagramItem('text', {'x': x + leftGap + self.width / 2, 'y': y + 5, 'class': 'comment'}, self.text)
		if self.href is not None:
			a = DiagramItem('a', {'xlink:href':self.href}, text).addTo(self)
			text.addTo(a)
		else:
			text.addTo(self)
		if self.title is not None:
			DiagramItem('title', {}, self.title).addTo(self)
		return self


class Skip(DiagramItem):
	def __init__(self):
		DiagramItem.__init__(self, 'g')
		self.width = 0
		self.up = 0
		self.down = 0
		addDebug(self)

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
	exec(open('test.py').read())
	sys.stdout.write('''
		<style>
		.blue text { fill: blue; }
		</style>
		''')
	sys.stdout.write('</body></html>')
