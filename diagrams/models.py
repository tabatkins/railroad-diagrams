# diagrams for 2 models


add('Syk species - Syk(tSH2,l~Y,a~Y)',
    Diagram(
    "Syk(",
    Choice(0, Comment("    "), 'tSH2'
           ),
    Choice(0, Comment("    "),
           Sequence('l',
                    Choice(0, Comment("    "), '~Y'),)
           ),
    Choice(0, Comment("    "),
           Sequence('a',
                    Choice(0, Comment("    "), '~Y'),)
           ),
    ")"
))

add('Syk observable - Syk()',
    Diagram(
    "Syk(",
    Choice(0, Skip(),
           Sequence('tSH2',
                    Choice(0, Skip(), 'bound'),)
           ),
    Choice(0, Skip(),
           Sequence('l',
                    Choice(0, Skip(), '~Y', '~pY'),)
           ),
    Choice(0, Skip(),
           Sequence('a',
                    Choice(0, Skip(), '~Y', '~pY'),)
           ),
    ")"
))


add('Dephosphorylation of Rec beta - Rec(b~pY) →',
    Diagram(
    "Rec",
    Choice(0, Skip(),
           Sequence('a',
                    Choice(0, Skip(), 'bound'),)
           ),
    Choice(0, Comment("    "),
           Sequence('b',
                    Choice(0, Comment("    "), '~pY'),)
           ),
    Choice(0, Skip(),
           Sequence('g',
                    Choice(0, Skip(), '~Y', '~pY'),
                    Choice(0, Skip(), 'bound'))
           ),
    ))

add('goes to Rec(b~Y)',
    Diagram(
    'Rec',
    Choice(0, Skip(),
            Sequence('a',
                    Choice(0, Skip(), 'bound'),)
               ),
    Choice(0, Comment("    "),
            Sequence('b',
                    Choice(0, Comment("    "), '~Y'),)
               ),
    Choice(0, Skip(),
            Sequence('g',
                    Choice(0, Skip(), '~Y', '~pY'),
                    Choice(0, Skip(), 'bound'))
               ),
    ))


add('MAP3K molecule - MAP3K(s,S~I~A)',
    Diagram(
    "Map3K(",
    Choice(0, Comment("    "),'s'),
    Choice(0, Comment("    "),
           Sequence('S',
                    Choice(0, Comment("    "), '~I', '~A'),)
           ),
    ")"
)
)

add('MAP3K species - MAP3K(s,S~I)',
    Diagram(
    "Map3K(",
    Choice(0, Comment("    "),'s'),
    Choice(0, Comment("    "),
           Sequence('S',
                    Choice(0, Comment("    "), '~I'),)
           ),
    ")"
)
)


add('reaction MAP3K(S~A) →',
    Diagram(
    'MAP3K',
    Choice(0, Skip(),
            Sequence('s',
                    Choice(0, Skip(), 'bound'),)
               ),
    Choice(0, Comment("    "),
            Sequence('S',
                    Choice(0, Comment("    "), '~A'),)
               ),
    ))

add('goes to MAP3K(S~I)',
    Diagram(
    'MAP3K',
    Choice(0, Skip(),
            Sequence('s',
                    Choice(0, Skip(), 'bound'),)
               ),
    Choice(0, Comment("    "),
            Sequence('S',
                    Choice(0, Comment("    "), '~l'),)
               ),
    ))
