import globSync from 'tiny-glob/sync';
import { readFileSync } from 'fs';
import { join, extname } from 'path';
import { safeLoad } from 'js-yaml';
import rr, { Diagram } from 'railroad-diagrams';

const args = process.argv;
let verbose = false;
const patterns = [];
let forcedInputType;

function usage () {
  console.log(`Checks the syntax of railroad diagrams in JSON, YAML or JavaScript.

Usage: rrdlint [option...] [pattern...]

Options:
  -i|--input <type>  read input from json, yaml or javascript. defaults to json
  -v|--verbose       print checked file names and error stacktrace
  -V|--version       print version number
  -h|--help          print usage instructions

If no file name pattern is provided, standard input will be read.
If no input type is provided, it will be inferred from the file extension:
".json" -> json, ".yaml" or ".yml" -> yaml, ".js" -> javascript.
    
Examples:
  cat foo.yaml | rrdlint -i yaml
  rrdlint diagrams/*`);
  process.exit(0);
}

if (!args.length) usage();

for (let i = 2, l = args.length; i < l; ++i) {
  const arg = args[i];
  let match;
  if ((match = /^(?:-|--)(?:(no)-)?(\w+)$/.exec(arg))) {
    switch (match[2]) {
      case 'v': case 'verbose':
        verbose = true;
        continue;
      case 'i': case 'input':
        forcedInputType = args[++i];
        if (forcedInputType !== 'json' && forcedInputType !== 'yaml' && forcedInputType !== 'javascript') {
          console.error(`Invalid input type: "${forcedInputType}".`);
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
  patterns.push(arg);
}

if (patterns.length) {
  for (const pattern of patterns) {
    const names = globSync(pattern, { filesOnly: true });
    for (const name of names) {
      let inputType;
      if (forcedInputType === undefined) {
        const ext = extname(name);
        switch (ext) {
          case '.json': inputType = 'json'; break;
          case '.yml': case '.yaml': inputType = 'yaml'; break;
          case '.js': inputType = 'javascript';
        }
      } else {
        inputType = forcedInputType;
      }
      run({ name, code: readFileSync(name, 'utf-8') }, inputType);
    }
  }
}

function run (source, inputType) {
  try {
    switch (inputType) {
      case 'javascript':
        fromJavaScript(source.code); break;
      case 'yaml':
        Diagram.fromJSON(safeLoad(source.code)); break;
      case 'json':
      default:
        Diagram.fromJSON(JSON.parse(source.code));
    }
    if (verbose) console.log(`${source.name}: OK`);
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
${input}`);
  createDiagram();
}

if (!patterns.length) {
  let input = '';
  process.stdin.setEncoding('utf8');
  process.stdin
    .on('data', chunk => (input += chunk))
    .on('end', () => {
      run({ name: 'snippet', code: input }, forcedInputType);
    })
    .resume();
}
