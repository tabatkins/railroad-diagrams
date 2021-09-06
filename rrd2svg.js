import { readFileSync } from 'fs';
import { join, extname } from 'path';
import { safeLoad } from 'js-yaml';
import rr, { Diagram, Options } from 'railroad-diagrams';

const args = process.argv;
let standalone = true;
let verbose = false;
let source, inputType;

function usage () {
  console.log(`Generates railroad diagrams from JSON, YAML or JavaScript to SVG.

Usage: rrd2svg [option...] [file]

Options:
  --[no]-standalone  add stylesheet to the SVG element. defaults to true
  --[no]-debug       add sizing data into the SVG element. defaults to false
  -i|--input <type>  read input from json, yaml or javascript. defaults to json
  -v|--verbose       print error stacktrace
  -V|--version       print version number
  -h|--help          print usage instructions

If no file name is provided, standard input will be read. If no input type
is provided, it will be inferred from the file extension: ".json" -> json,
".yaml" or ".yml" -> yaml, ".js" -> javascript.
  
Examples:
  cat foo.yaml | rrd2svg -i yaml
  rrd2svg foo.json`);
  process.exit(0);
}

if (!args.length) usage();

for (let i = 2, l = args.length; i < l; ++i) {
  const arg = args[i];
  let match;
  if ((match = /^(?:-|--)(?:(no)-)?(\w+)$/.exec(arg))) {
    const value = match[1] !== 'no';
    switch (match[2]) {
      case 'standalone':
        standalone = value;
        continue;
      case 'debug':
        Options.DEBUG = value;
        continue;
      case 'v': case 'verbose':
        verbose = true;
        continue;
      case 'i': case 'input':
        inputType = args[++i];
        if (inputType !== 'json' && inputType !== 'yaml' && inputType !== 'javascript') {
          console.error(`Invalid input type: "${inputType}".`);
          process.exit(2);
        }
        continue;
      case 'V': case 'version':
        console.log(JSON.parse(readFileSync(join(
          __dirname, '../package.json'), 'utf-8')).version);
        process.exit(0);
        continue;
      case 'h': case 'help':
        usage();
    }
    console.error(`Unknown option: "${match[0]}".`);
    process.exit(2);
  }
  if (source) {
    console.error('More than one file supplied.');
    process.exit(2);
  }
  source = { name: arg, code: readFileSync(arg, 'utf-8') };
  if (inputType === undefined) {
    const ext = extname(arg);
    switch (ext) {
      case '.json': inputType = 'json'; break;
      case '.yml': case '.yaml': inputType = 'yaml'; break;
      case '.js': inputType = 'javascript';
    }
  }
}

function run () {
  try {
    let diagram;
    switch (inputType) {
      case 'javascript':
        diagram = fromJavaScript(source.code); break;
      case 'yaml':
        diagram = Diagram.fromJSON(safeLoad(source.code)); break;
      case 'json':
      default:
        diagram = Diagram.fromJSON(JSON.parse(source.code));
    }
    console.log(diagram[standalone ? 'toStandalone' : 'toString']());
  } catch (error) {
    console.error(`${source.name}: ${error.message}`);
    if (verbose) console.log(error.stack);
    process.exitCode = 1;
  }
}

function fromJavaScript (input) {
  global.rr = rr;
  const diagramFunctions = `const { ${Object.keys(rr).join(', ')} } = rr;`;
  const createDiagram = new Function(`${diagramFunctions}
return ${input}`);
  return createDiagram();
}

if (source) {
  run();
} else {
  let input = '';
  process.stdin.setEncoding('utf8');
  process.stdin
    .on('data', chunk => (input += chunk))
    .on('end', () => {
      source = { name: 'snippet', code: input };
      run();
    })
    .resume();
}
