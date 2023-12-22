add('comment', Diagram(
	'/*',
	ZeroOrMore(
		NonTerminal('anything but * followed by /')),
	'*/'));

add('newline', Diagram(Choice(0, '\\n', '\\r\\n', '\\r', '\\f')));

add('whitespace', Diagram(Choice(
	0, 'space', '\\t', NonTerminal('newline'))));

add('hex digit', Diagram(NonTerminal('0-9 a-f or A-F')));

add('escape', Diagram(
	'\\', Choice(0,
		NonTerminal('not newline or hex digit'),
		Sequence(
			OneOrMore(NonTerminal('hex digit'), Comment('1-6 times')),
			Optional(NonTerminal('whitespace'), 'skip')))));

add('<whitespace-token>', Diagram(OneOrMore(NonTerminal('whitespace'))));

add('ws*', Diagram(ZeroOrMore(NonTerminal('<whitespace-token>'))));

add('<ident-token>', Diagram(
	Choice(0, Skip(), '-'),
	Choice(0, NonTerminal('a-z A-Z _ or non-ASCII'), NonTerminal('escape')),
	ZeroOrMore(Choice(0,
		NonTerminal('a-z A-Z 0-9 _ - or non-ASCII'), NonTerminal('escape')))));

add('<function-token>', Diagram(
	NonTerminal('<ident-token>'), '('));

add('<at-keyword-token>', Diagram(
	'@', NonTerminal('<ident-token>')));

add('<hash-token>', Diagram(
	'#', OneOrMore(Choice(0,
		NonTerminal('a-z A-Z 0-9 _ - or non-ASCII'),
		NonTerminal('escape')))));

add('<string-token>', Diagram(
	Choice(0,
		Sequence(
			'"',
			ZeroOrMore(
				Choice(0,
					NonTerminal('not " \\ or newline'),
					NonTerminal('escape'),
					Sequence('\\', NonTerminal('newline')))),
			'"'),
		Sequence(
			'\'',
			ZeroOrMore(
				Choice(0,
					NonTerminal("not ' \\ or newline"),
					NonTerminal('escape'),
					Sequence('\\', NonTerminal('newline')))),
			'\''))));

add('<url-token>', Diagram(
	NonTerminal('<ident-token "url">'),
	'(',
	NonTerminal('ws*'),
	Optional(Sequence(
		Choice(0, NonTerminal('url-unquoted'), NonTerminal('STRING')),
		NonTerminal('ws*'))),
	')'));

add('url-unquoted', Diagram(OneOrMore(
	Choice(0,
		NonTerminal('not " \' ( ) \\ whitespace or non-printable'),
		NonTerminal('escape')))));

add('<number-token>', Diagram(
	Choice(1, '+', Skip(), '-'),
	Choice(0,
		Sequence(
			OneOrMore(NonTerminal('digit')),
			'.',
			OneOrMore(NonTerminal('digit'))),
		OneOrMore(NonTerminal('digit')),
		Sequence(
			'.',
			OneOrMore(NonTerminal('digit')))),
	Choice(0,
		Skip(),
		Sequence(
			Choice(0, 'e', 'E'),
			Choice(1, '+', Skip(), '-'),
			OneOrMore(NonTerminal('digit'))))));

add('<dimension-token>', Diagram(
	NonTerminal('<number-token>'), NonTerminal('<ident-token>')));

add('<percentage-token>', Diagram(
	NonTerminal('<number-token>'), '%'));

add('<unicode-range-token>', Diagram(
	Choice(0,
		'U',
		'u'),
	'+',
	Choice(0,
		Sequence(OneOrMore(NonTerminal('hex digit'), Comment('1-6 times'))),
		Sequence(
			ZeroOrMore(NonTerminal('hex digit'), Comment('1-5 times')),
			OneOrMore('?', Comment('1 to (6 - digits) times'))),
		Sequence(
			OneOrMore(NonTerminal('hex digit'), Comment('1-6 times')),
			'-',
			OneOrMore(NonTerminal('hex digit'), Comment('1-6 times'))))));

NonTerminal = NonTerminal;

add('Stylesheet', Diagram(ZeroOrMore(Choice(3,
	NonTerminal('<CDO-token>'), NonTerminal('<CDC-token>'), NonTerminal('<whitespace-token>'),
	NonTerminal('Qualified rule'), NonTerminal('At-rule')))));

add('Rule list', Diagram(ZeroOrMore(Choice(1,
	NonTerminal('<whitespace-token>'), NonTerminal('Qualified rule'), NonTerminal('At-rule')))));

add('At-rule', Diagram(
	NonTerminal('<at-keyword-token>'), ZeroOrMore(NonTerminal('Component value')),
	Choice(0, NonTerminal('{} block'), ';')));

add('Qualified rule', Diagram(
	ZeroOrMore(NonTerminal('Component value')),
	NonTerminal('{} block')));

add('Declaration list', Diagram(
	NonTerminal('ws*'),
	Choice(0,
		Sequence(
			Optional(NonTerminal('Declaration')),
			Optional(Sequence(';', NonTerminal('Declaration list')))),
		Sequence(
			NonTerminal('At-rule'),
			NonTerminal('Declaration list')))));

add('Declaration', Diagram(
	NonTerminal('<ident-token>'), NonTerminal('ws*'), ':',
	ZeroOrMore(NonTerminal('Component value')), Optional(NonTerminal('!important'))));

add('!important', Diagram(
	'!', NonTerminal('ws*'), NonTerminal('<ident-token "important">'), NonTerminal('ws*')));

add('Component value', Diagram(Choice(0,
	NonTerminal('Preserved token'),
	NonTerminal('{} block'),
	NonTerminal('() block'),
	NonTerminal('[] block'),
	NonTerminal('Function block'))));


add('{} block', Diagram('{', ZeroOrMore(NonTerminal('Component value')), '}'));
add('() block', Diagram('(', ZeroOrMore(NonTerminal('Component value')), ')'));
add('[] block', Diagram('[', ZeroOrMore(NonTerminal('Component value')), ']'));

add('Function block', Diagram(
	NonTerminal('<function-token>'),
	ZeroOrMore(NonTerminal('Component value')),
	')'));

add('glob pattern', Diagram(
	AlternatingSequence(
		NonTerminal("ident"),
		"*")))

add('SQL', Diagram(
	Stack(
		Sequence(
			'SELECT',
			Optional('DISTINCT', 'skip'),
			Choice(0,
				'*',
				OneOrMore(
					Sequence(NonTerminal('expression'), Optional(Sequence('AS', NonTerminal('output_name')))),
					','
				)
			),
			'FROM',
			OneOrMore(NonTerminal('from_item'), ','),
			Optional(Sequence('WHERE', NonTerminal('condition')))
		),
		Sequence(
			Optional(Sequence('GROUP BY', NonTerminal('expression'))),
			Optional(Sequence('HAVING', NonTerminal('condition'))),
			Optional(Sequence(
				Choice(0, 'UNION', 'INTERSECT', 'EXCEPT'),
				Optional('ALL'),
				NonTerminal('select')
			))
		),
		Sequence(
			Optional(Sequence(
				'ORDER BY',
				OneOrMore(Sequence(NonTerminal('expression'), Choice(0, Skip(), 'ASC', 'DESC')), ','))
			),
			Optional(Sequence(
				'LIMIT',
				Choice(0, NonTerminal('count'), 'ALL')
			)),
			Optional(Sequence('OFFSET', NonTerminal('start'), Optional('ROWS')))
		))))

add('Group example',
	Diagram(
		"foo",
		ZeroOrMore(
			Group(
				Stack('foo', 'bar'),
				'label')
			),
		"bar"),
	)

add('Class example',
	Diagram(
		"foo",
		Terminal("blue", cls="blue"),
		NonTerminal("blue", cls="blue"),
		Comment("blue", cls="blue")
		)
	)

add('rr-alternatingsequence',
	Diagram(
		AlternatingSequence(
			"foo",
			"bar"
			)
		)
	)

add('rr-choice',
	Diagram(
		Choice(
			1, "1", "2", "3"
			)
		)
	)

add('rr-group',
	Diagram(
		Terminal("foo"),
		Group(
			Choice(
				0, NonTerminal("option 1"), NonTerminal("or two"),
				)
			),
		Terminal("bar")
		)
	)

add('rr-horizontalchoice',
	Diagram(
		HorizontalChoice(
			Choice(2, "0", "1", "2", "3", "4"),
			Choice(2, "5", "6", "7", "8", "9"),
			Choice(2, "a", "b", "c", "d", "e"),
			)
		)
	)

add('rr-multchoice',
	Diagram(
		MultipleChoice(1, "all", "1", "2", "3")
		)
	)

add('rr-oneormore',
	Diagram(
			OneOrMore("foo", "bar")
		)
	)


add('rr-optional',
	Diagram(
			Optional("foo"),
			Optional("bar", True),
		)
	)


add('rr-optionalsequence',
	Diagram(
			OptionalSequence("1", "2", "3")
		)
	)


add('rr-sequence',
	Diagram(
			Sequence("1", "2", "3")
		)
	)


add('rr-stack',
	Diagram(
		Stack(
			"1",
			"2",
			"3"
			)
		)
	)

add('rr-title',
	Diagram(
			Stack(
				Terminal("Generate"),
				Terminal("some"),
			),
			OneOrMore(NonTerminal("railroad diagrams"), Comment("and more"))
		)
	)


add('rr-zeroormore-1',
	Diagram(
		ZeroOrMore("foo", Comment("bar"))
		)
	)


add('rr-zeroormore-2',
	Diagram(
		ZeroOrMore("foo", Comment("bar")),
		ZeroOrMore("foo", Comment("bar"), True)
		)
	)

add('complicated-horizontalchoice-1',
	Diagram(
		HorizontalChoice(
			Choice(0, "1", "2", "3", "4", "5"),
			Choice(4, "1", "2", "3", "4", "5"),
			Choice(2, "1", "2", "3", "4", "5"),
			Choice(3, "1", "2", "3", "4", "5"),
			Choice(1, "1", "2", "3", "4", "5")
			),
		HorizontalChoice("1", "2", "3", "4", "5")
		)
	)

add('complicated-horizontalchoice-2',
	Diagram(
		HorizontalChoice(
			Choice(0, "1", "2", "3", "4"),
			"4",
			Choice(3, "1", "2", "3", "4"),
			)
		)
	)

add('complicated-horizontalchoice-3',
	Diagram(
		HorizontalChoice(
			Choice(0, "1", "2", "3", "4"),
			Stack("1", "2", "3"),
			Choice(3, "1", "2", "3", "4"),
			)
		)
	)

add('complicated-horizontalchoice-4',
	Diagram(
		HorizontalChoice(
			Choice(0, "1", "2", "3", "4"),
			Choice(3, "1", "2", "3", "4"),
			Stack("1", "2", "3"),
			)
		)
	)

add('complicated-horizontalchoice-5',
	Diagram(
		HorizontalChoice(
			Stack("1", "2", "3"),
			Choice(0, "1", "2", "3", "4"),
			Choice(3, "1", "2", "3", "4"),
			)
		)
	)

add('single-stack',
	Diagram(
		Stack("1"),
		)
	)

add('complicated-optionalsequence-1',
	Diagram(
			OptionalSequence("1", Choice(2, "2", "3", "4", "5"), Stack("6", "7", "8", "9", "10"), "11")
		)
	)

add('labeled-start',
	Diagram(
			Start(label="Labeled Start"),
			Sequence("1", "2", "3")
		)
	)

add('complex',
	Diagram(
			Sequence("1", "2", "3"),
			type="complex"
		)
	)

add('simple',
	Diagram(
			Sequence("1", "2", "3"),
			type="simple"
		)
	)
