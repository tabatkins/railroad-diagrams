# coding=utf-8
from __future__ import unicode_literals

import re
import io
import pprint
import collections as coll
import itertools

import railroad_diagrams as rr

class TokenStream:
	def __init__(self, tokens, before=None, after=None):
		self.tokens = list(tokens)
		self.i = 0
		self.before = before
		self.after = after

	def __len__(self):
		return len(self.tokens)

	def __getitem__(self, index):
		if isinstance(index, int):
			return self.tokens[index]
		return TokenStream(self.tokens[index], before=self.before, after=self.after)

	def __setitem__(self, index, val):
		self.tokens[index] = val

	def __delitem__(self, index):
		del self.tokens[index]

	def ended(self):
		return self.i >= len(self)

	def prev(self, i=1):
		index = self.i - i
		if index < 0:
			return self.before
		return self[index]

	def curr(self):
		if self.i < 0:
			return self.before
		elif self.i >= len(self):
			return self.after
		else:
			return self[self.i]

	def next(self, i=1):
		index = self.i + i
		if index >= len(self):
			return self.after
		return self[index]

	def advance(self, i=1):
		self.i += i
		return self.curr()

	def __getattr__(self, name):
		if len(name) >= 5 and name[0:4] in ("prev", "curr", "next"):
			tokenDir = name[0:4]
			attrName = name[4:]
			def _missing(i=1):
				if tokenDir == "prev":
					tok = self.prev(i)
				elif tokenDir == "next":
					tok = self.next(i)
				else:
					tok = self.curr()
				if attrName in tok:
					return tok[attrName]
				else:
					raise AttributeError, attrName
			return _missing

	def __iter__(self):
		return self.tokens

	def __reversed__(self):
		return reversed(self.tokens)

	def __contains__(self, item):
		return item in self.tokens

	def __add__(self, other):
		if isinstance(other, TokenStream):
			return TokenStream(self.tokens + other.tokens, before=self.before, after=other.after)
		if isinstance(other, coll.Iterable):
			return TokenStream(self.tokens + other, before=self.before, after=self.after)
		raise TypeError("TokenStreams can only be added to iterable types, got '{0}'".format(type(other)))

	def __radd__(self, other):
		if isinstance(other, TokenStream):
			return TokenStream(other.tokens + self.tokens, before=other.before, after=self.after)
		if isinstance(other, coll.Iterable):
			return TokenStream(other + self.tokens, before=self.before, after=self.after)
		raise TypeError("TokenStreams can only be added to iterable types, got '{0}'".format(type(other)))

	def __iadd__(self, other):
		if isinstance(other, TokenStream):
			self.tokens += other.tokens
			self.after = other.after
			return self
		if isinstance(other, coll.Iterable):
			self.tokens += other
			return self
		raise TypeError("TokenStreams can only be added to iterable types, got '{0}'".format(type(other)))

	def __mul__(self, num):
		return TokenStream(self.tokens * num, before=self.before, after=self.after)

	def __rmul__(self, num):
		return TokenStream(self.tokens * num, before=self.before, after=self.after)

	def __imul__(self, num):
		self.tokens *= num
		return self

	def append(self, val):
		self.tokens.append(val)

	def extend(self, vals):
		self.tokens.extend(vals)

	def insert(self, i, val):
		self.tokens.insert(i, val)

	def remove(self, val):
		self.tokens.remove(val)

	def pop(self, i=None):
		if i is None:
			return self.tokens.pop()
		else:
			return self.tokens.pop(i)

	def index(self, val):
		return self.tokens.index(val)

	def count(self, val):
		return self.tokens.count(val)

	def sort(self, cmp=None, key=None, reverse=False):
		self.tokens.sort(cmp, key, reverse)

	def reverse(self):
		self.tokens.reverse()


def tokenize(tokenPatterns, text):
	tokenres = [{'name':name,'re':re.compile(regex) if isinstance(regex, basestring) else re.compile(regex[0], regex[1])} for name,regex in tokenPatterns.items()]
	pos = 0
	tokens = []
	while pos < len(text):
		token = max([{'name':token['name'], 'match':token['re'].match(text, pos)} for token in tokenres if token['re'].match(text,pos)], key=lambda x:x['match'].group(0))
		'''
		longestMatch = (0, None)
		for tname,tre in tokenres:
			match = tre.match(text, pos)
			if match and len(match.group(0)) > longestMatch[0]:
				longestMatch = (len(match.group(0)), (tname, match))'''
		if token is not None:
			tokens.append(token)
			pos += len(token['match'].group(0))
		else:
			raise Exception("Tokenize failure at pos {0} for text '{1}'.".format(pos, text))
	return tokens

def parse(tokens):
	tokens = TokenStream(tokens)

	# First resolve brackets
	def collectGroup(tokens):
		tokens.advance() # jump past the open bracket
		group = []
		while not tokens.ended():
			if tokens.currname() == "closebracket":
				return {"name": "sequence", "children": group}
			elif tokens.currname() == "closebracketbang":
				return {"name": "optionalsequence", "children": group}
			else:
				group.append(tokens.curr())
				tokens.advance()
		raise Exception("Ran out of tokens while trying to find the end of a group.")
	tokenTree = []
	while not tokens.ended():
		if tokens.currname() == "openbracket":
			tokenTree.append(collectGroup(tokens))
		else:
			tokenTree.append(tokens.curr())
		tokens.advance()

	# Now split into Choice/MultipleChoice
	def groupAll(tokens):
		if any(t['name'] == 'doubleand' for t in tokens):
			children = []
			group = []
			for t in tokens:
				if t['name'] == "doubleand":
					children.append({"name":"sequence": "children":group})
				elif t['name'] in ["sequence", "optionalsequence"]:
					t['children'] = groupOne(t['children'])
					group.append(t)
				else:
					group.append(t)
			children.append({"name":"sequence": "children":group})
			return [{"name": "doubleand", "children": children}]
		else:
			return [tokens]
	def groupSome(tokens):
		if any(t['name'] == 'doublebar' for t in tokens):
			children = []
			group = []
			for t in tokens:
				if t['name'] == "bar":
					children.append({"name":"sequence": "children":group})
				elif t['name'] in ["sequence", "optionalsequence"]:
					t['children'] = groupOne(t['children'])
					group.append(t)
				else:
					group.append(t)
			children.append({"name":"sequence": "children":group})
			return [{"name": "doublebar", "children": children}]
		else:
			return [tokens]

	def groupOne(tokens):
		if any(t['name'] == 'bar' for t in tokens):
			children = []
			group = []
			for t in tokens:
				if t['name'] == "bar":
					children.append({"name":"sequence": "children":group})
				elif t['name'] in ["sequence", "optionalsequence"]:
					t['children'] = groupOne(t['children'])
					group.append(t)
				else:
					group.append(t)
			children.append({"name":"sequence": "children":group})
			return [{"name": "bar", "children": children}]
		else:
			return [tokens]

	# Finally, convert tokens into diagrams
	def convertTokens(tokens):
		d = []
		for token in tokens:
			name = token['name']
			if name in ["keyword", "char"]:
				d.append(rr.Terminal(token['match'].group(0)))
			elif name == "literal":
				d.append(rr.Terminal(token['match'].group(1)))
			elif name == "type":
				d.append(rr.NonTerminal(token['match'].group(0)))
			elif name == "sequence":
				token['children'] = convertTokens(token['children'])
				d.append(rr.Sequence(*token['children']))
			elif name == "optionalsequence":
				token['children'] = convertTokens(token['children'])
				d.append(rr.OptionalSequence(*token['children']))
			elif name == "multopt":
				d[-1] = rr.Optional(d[-1])
			elif name == "multstar":
				d[-1] = rr.ZeroOrMore(d[-1])
			elif name == "multplus":
				d[-1] = rr.OneOrMore(d[-1])
			elif name == "multhash":
				d[-1] = rr.OneOrMore(d[-1], Terminal(','))
			elif name in ["multopt", "multstar", "multplus", "multhash"]:
				token['child'] = d[-1]
				d[-1] = token
			else:
				d.append(token)
		return d
	return Diagram(*convertTokens(tokenTree))





tokenPatterns = {
    'keyword': r"[\w-]+\(?",
    'type': r"<[\w'‘’-]+(\(\))?>",
    'char': r"[/,()]",
    'literal': r"'(.)'",
    'openbracket': r"\[",
    'closebracket': r"\]",
    'closebracketbang': r"\]!",
    'bar': r"\|",
    'doublebar': r"\|\|",
    'doubleand': r"&&",
    'multopt': r"\?",
    'multstar': r"\*",
    'multplus': r"\+",
    'multhash': r"#",
    'multnum1': r"{\s*(\d+)\s*}",
    'multnum2': r"{\s*(\d+)\s*,\s*(\d*)\s*}",
    'multhashnum1': r"#{\s*(\d+)\s*}",
    'multhashnum2': r"{\s*(\d+)\s*,\s*(\d*)\s*}",
    'ws': r"\s+"
}

tokens = [t for t in tokenize(tokenPatterns, "none | [ <‘flex-grow’> <‘flex-shrink’>? || <‘flex-basis’> ]") if t['name'] != 'ws']
tokens = parse(tokens)
# pprint.PrettyPrinter(indent=2).pprint(tokens)
with io.open('testpy.html', 'w', encoding='utf-8') as fh:
	fh.write("<!doctype html><link rel=stylesheet href=railroad-diagrams.css>")
	rr.Diagram(*tokens).writeSvg(fh.write)
