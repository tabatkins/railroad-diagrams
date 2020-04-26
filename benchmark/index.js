/* eslint-disable no-new */

import createSuite from './create-suite';
import rr, {
  ComplexDiagram, Diagram, NonTerminal, Sequence, Optional, Choice, Skip,
  MultipleChoice, ZeroOrMore, OneOrMore, AlternatingSequence, OptionalSequence,
  Stack, Comment
} from '../railroad';
import { safeLoad } from 'js-yaml';
import { readFileSync } from 'fs';
import { join } from 'path';

function usingFunctions () {
  // ident
  rr.ComplexDiagram(
    rr.Choice(0, rr.Skip(), '-'),
    rr.Choice(0, rr.NonTerminal('name-start char'), rr.NonTerminal('escape')),
    rr.ZeroOrMore(
      rr.Choice(0, rr.NonTerminal('name char'), rr.NonTerminal('escape'))));
  // function
  rr.Diagram(rr.NonTerminal('IDENT'), '(');
  // at-keyword
  rr.Diagram('@', rr.NonTerminal('IDENT'));
  // hash
  rr.Diagram('#', rr.NonTerminal('IDENT'));
  // string
  rr.Diagram(
    rr.Choice(0,
      rr.Sequence(
        '"',
        rr.ZeroOrMore(
          rr.Choice(0,
            rr.NonTerminal('not " or \\'),
            rr.NonTerminal('escape'))),
        '"'),
      rr.Sequence(
        "'",
        rr.ZeroOrMore(
          rr.Choice(0,
            rr.NonTerminal("not ' or \\"),
            rr.NonTerminal('escape'))),
        "'")));
  // url
  rr.Diagram(
    rr.Choice(0, 'u', 'U'),
    rr.Choice(0, 'r', 'R'),
    rr.Choice(0, 'l', 'L'),
    '(',
    rr.Choice(1,
      rr.Optional(rr.NonTerminal('WS')),
      rr.Sequence(
        rr.Optional(rr.NonTerminal('WS')),
        rr.NonTerminal('STRING', '#string'),
        rr.Optional(rr.NonTerminal('WS'))),
      rr.Sequence(
        rr.Optional(rr.NonTerminal('WS')),
        rr.OneOrMore(
          rr.Choice(0,
            rr.NonTerminal('not " \' ( ) WS or NPC'),
            rr.NonTerminal('escape'))),
        rr.Optional(rr.NonTerminal('WS')))),
    ')');
  // number
  rr.Diagram(
    rr.Choice(1, '+', rr.Skip(), '-'),
    rr.Choice(0,
      rr.Sequence(
        rr.OneOrMore(rr.NonTerminal('digit')),
        '.',
        rr.OneOrMore(rr.NonTerminal('digit'))),
      rr.OneOrMore(rr.NonTerminal('digit')),
      rr.Sequence(
        '.',
        rr.OneOrMore(rr.NonTerminal('digit')))),
    rr.Choice(0,
      rr.Skip(),
      rr.Sequence(
        rr.Choice(0, 'e', 'E'),
        rr.Choice(1, '+', rr.Skip(), '-'),
        rr.OneOrMore(rr.NonTerminal('digit')))));
  // dimension
  rr.Diagram(rr.NonTerminal('NUMBER', '#number'), rr.NonTerminal('IDENT'));
  // percentage
  rr.Diagram(rr.NonTerminal('NUMBER', '#number'), '%');
  // unicode-range
  rr.Diagram(
    rr.Choice(0,
      'U',
      'u'),
    '+',
    rr.Choice(0,
      rr.Sequence(rr.OneOrMore(rr.NonTerminal('hex digit'), rr.Comment('1-6 times'))),
      rr.Sequence(
        rr.ZeroOrMore(rr.NonTerminal('hex digit'), rr.Comment('1-5 times')),
        rr.OneOrMore('?', rr.Comment('1 to (6 - digits) times'))),
      rr.Sequence(
        rr.OneOrMore(rr.NonTerminal('hex digit'), rr.Comment('1-6 times')),
        '-',
        rr.OneOrMore(rr.NonTerminal('hex digit'), rr.Comment('1-6 times')))));
  // comment
  rr.Diagram(
    '/*',
    rr.ZeroOrMore(
      rr.NonTerminal('anything but * followed by /')),
    '*/');
  // cdo
  rr.Diagram('<' + '!--');
  // cdc
  rr.Diagram('-->');
  // sql
  rr.Diagram(
    rr.Stack(
      rr.Sequence(
        'SELECT',
        rr.Optional('DISTINCT', 'skip'),
        rr.Choice(0,
          '*',
          rr.OneOrMore(
            rr.Sequence(rr.NonTerminal('expression'), rr.Optional(rr.Sequence('AS', rr.NonTerminal('output_name')))),
            ','
          )
        ),
        'FROM',
        rr.OneOrMore(rr.NonTerminal('from_item'), ','),
        rr.Optional(rr.Sequence('WHERE', rr.NonTerminal('condition')))
      ),
      rr.Sequence(
        rr.Optional(rr.Sequence('GROUP BY', rr.NonTerminal('expression'))),
        rr.Optional(rr.Sequence('HAVING', rr.NonTerminal('condition'))),
        rr.Optional(rr.Sequence(
          rr.Choice(0, 'UNION', 'INTERSECT', 'EXCEPT'),
          rr.Optional('ALL'),
          rr.NonTerminal('select')
        ))
      ),
      rr.Sequence(
        rr.Optional(rr.Sequence(
          'ORDER BY',
          rr.OneOrMore(rr.Sequence(rr.NonTerminal('expression'), rr.Choice(0, rr.Skip(), 'ASC', 'DESC')), ','))
        ),
        rr.Optional(rr.Sequence(
          'LIMIT',
          rr.Choice(0, rr.NonTerminal('count'), 'ALL')
        )),
        rr.Optional(rr.Sequence('OFFSET', rr.NonTerminal('start'), rr.Optional('ROWS')))
      )
    )
  );
  // image-func
  rr.Diagram(
    rr.Optional(
      rr.Sequence(
        rr.Choice(0, 'ltr', 'rtl')
      )
    ),
    rr.OptionalSequence(
      rr.Choice(0, rr.NonTerminal('<url>'), rr.NonTerminal('<string>')),
      rr.NonTerminal('<color>')
    )
  );
  // glob
  rr.Diagram(
    rr.AlternatingSequence(
      rr.OneOrMore(rr.NonTerminal('alphanumeric')),
      '*'
    )
  );
  // grid-auto-flow
  rr.Diagram(
    rr.MultipleChoice(0, 'any',
      rr.Choice(1, 'row', 'column'),
      'dense'
    )
  );
}

function usingConstructors () {
  // ident
  new ComplexDiagram(
    new Choice(0, new Skip(), '-'),
    new Choice(0, new NonTerminal('name-start char'), new NonTerminal('escape')),
    new ZeroOrMore(
      new Choice(0, new NonTerminal('name char'), new NonTerminal('escape'))));
  // function
  new Diagram(new NonTerminal('IDENT'), '(');
  // at-keyword
  new Diagram('@', new NonTerminal('IDENT'));
  // hash
  new Diagram('#', new NonTerminal('IDENT'));
  // string
  new Diagram(
    new Choice(0,
      new Sequence(
        '"',
        new ZeroOrMore(
          new Choice(0,
            new NonTerminal('not " or \\'),
            new NonTerminal('escape'))),
        '"'),
      new Sequence(
        "'",
        new ZeroOrMore(
          new Choice(0,
            new NonTerminal("not ' or \\"),
            new NonTerminal('escape'))),
        "'")));
  // url
  new Diagram(
    new Choice(0, 'u', 'U'),
    new Choice(0, 'r', 'R'),
    new Choice(0, 'l', 'L'),
    '(',
    new Choice(1,
      new Optional(new NonTerminal('WS')),
      new Sequence(
        new Optional(new NonTerminal('WS')),
        new NonTerminal('STRING', '#string'),
        new Optional(new NonTerminal('WS'))),
      new Sequence(
        new Optional(new NonTerminal('WS')),
        new OneOrMore(
          new Choice(0,
            new NonTerminal('not " \' ( ) WS or NPC'),
            new NonTerminal('escape'))),
        new Optional(new NonTerminal('WS')))),
    ')');
  // number
  new Diagram(
    new Choice(1, '+', new Skip(), '-'),
    new Choice(0,
      new Sequence(
        new OneOrMore(new NonTerminal('digit')),
        '.',
        new OneOrMore(new NonTerminal('digit'))),
      new OneOrMore(new NonTerminal('digit')),
      new Sequence(
        '.',
        new OneOrMore(new NonTerminal('digit')))),
    new Choice(0,
      new Skip(),
      new Sequence(
        new Choice(0, 'e', 'E'),
        new Choice(1, '+', new Skip(), '-'),
        new OneOrMore(new NonTerminal('digit')))));
  // dimension
  new Diagram(new NonTerminal('NUMBER', '#number'), new NonTerminal('IDENT'));
  // percentage
  new Diagram(new NonTerminal('NUMBER', '#number'), '%');
  // unicode-range
  new Diagram(
    new Choice(0,
      'U',
      'u'),
    '+',
    new Choice(0,
      new Sequence(new OneOrMore(new NonTerminal('hex digit'), new Comment('1-6 times'))),
      new Sequence(
        new ZeroOrMore(new NonTerminal('hex digit'), new Comment('1-5 times')),
        new OneOrMore('?', new Comment('1 to (6 - digits) times'))),
      new Sequence(
        new OneOrMore(new NonTerminal('hex digit'), new Comment('1-6 times')),
        '-',
        new OneOrMore(new NonTerminal('hex digit'), new Comment('1-6 times')))));
  // comment
  new Diagram(
    '/*',
    new ZeroOrMore(
      new NonTerminal('anything but * followed by /')),
    '*/');
  // cdo
  new Diagram('<' + '!--');
  // cdc
  new Diagram('-->');
  // sql
  new Diagram(
    new Stack(
      new Sequence(
        'SELECT',
        new Optional('DISTINCT', 'skip'),
        new Choice(0,
          '*',
          new OneOrMore(
            new Sequence(new NonTerminal('expression'), new Optional(new Sequence('AS', new NonTerminal('output_name')))),
            ','
          )
        ),
        'FROM',
        new OneOrMore(new NonTerminal('from_item'), ','),
        new Optional(new Sequence('WHERE', new NonTerminal('condition')))
      ),
      new Sequence(
        new Optional(new Sequence('GROUP BY', new NonTerminal('expression'))),
        new Optional(new Sequence('HAVING', new NonTerminal('condition'))),
        new Optional(new Sequence(
          new Choice(0, 'UNION', 'INTERSECT', 'EXCEPT'),
          new Optional('ALL'),
          new NonTerminal('select')
        ))
      ),
      new Sequence(
        new Optional(new Sequence(
          'ORDER BY',
          new OneOrMore(new Sequence(new NonTerminal('expression'), new Choice(0, new Skip(), 'ASC', 'DESC')), ','))
        ),
        new Optional(new Sequence(
          'LIMIT',
          new Choice(0, new NonTerminal('count'), 'ALL')
        )),
        new Optional(new Sequence('OFFSET', new NonTerminal('start'), new Optional('ROWS')))
      )
    )
  );
  // image-func
  new Diagram(
    new Optional(
      new Sequence(
        new Choice(0, 'ltr', 'rtl')
      )
    ),
    new OptionalSequence(
      new Choice(0, new NonTerminal('<url>'), new NonTerminal('<string>')),
      new NonTerminal('<color>')
    )
  );
  // glob
  new Diagram(
    new AlternatingSequence(
      new OneOrMore(new NonTerminal('alphanumeric')),
      '*'
    )
  );
  // grid-auto-flow
  new Diagram(
    new MultipleChoice(0, 'any',
      new Choice(1, 'row', 'column'),
      'dense'
    )
  );
}

function loadDiagram (name) {
  const fileName = join(__dirname, `../examples/${name}.yml`);
  return safeLoad(readFileSync(fileName, 'utf-8'));
}

const identDiagram = loadDiagram('ident');
const functionDiagram = loadDiagram('function');
const atKeywordDiagram = loadDiagram('at-keyword');
const hashDiagram = loadDiagram('hash');
const stringDiagram = loadDiagram('string');
const urlDiagram = loadDiagram('url');
const number = loadDiagram('number');
const dimension = loadDiagram('dimension');
const percentage = loadDiagram('percentage');
const unicodeRange = loadDiagram('unicode-range');
const comment = loadDiagram('comment');
const cdo = loadDiagram('cdo');
const cdc = loadDiagram('cdc');
const sql = loadDiagram('sql');
const imageFunc = loadDiagram('image-func');
const glob = loadDiagram('glob');
const gridAutoFlow = loadDiagram('grid-auto-flow');

function usingFromJSON () {
  ComplexDiagram.fromJSON(identDiagram);
  Diagram.fromJSON(functionDiagram);
  Diagram.fromJSON(atKeywordDiagram);
  Diagram.fromJSON(hashDiagram);
  Diagram.fromJSON(stringDiagram);
  Diagram.fromJSON(urlDiagram);
  Diagram.fromJSON(number);
  Diagram.fromJSON(dimension);
  Diagram.fromJSON(percentage);
  Diagram.fromJSON(unicodeRange);
  Diagram.fromJSON(comment);
  Diagram.fromJSON(cdo);
  Diagram.fromJSON(cdc);
  Diagram.fromJSON(sql);
  Diagram.fromJSON(imageFunc);
  Diagram.fromJSON(glob);
  Diagram.fromJSON(gridAutoFlow);
}

createSuite('Creating 17 diagrams...')
  .add('using functions', usingFunctions)
  .add('using constructors', usingConstructors)
  .add('using fromJSON', usingFromJSON)
  .start();
