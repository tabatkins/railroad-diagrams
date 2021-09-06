import cleanup from 'rollup-plugin-cleanup';
import { terser } from 'rollup-plugin-terser';

const banner = '#!/usr/bin/env node';
const paths = { 'railroad-diagrams': '../lib/index.js' };
const external = ['fs', 'path', 'js-yaml', 'tiny-glob/sync', 'railroad-diagrams'];
const plugins = [cleanup()];
const sourcemap = true;

export default [
  {
    input: 'railroad.js',
    output: [
      {
        file: 'lib/index.mjs',
        format: 'esm',
        sourcemap
      },
      {
        file: 'lib/index.js',
        format: 'cjs',
        exports: 'named',
        sourcemap
      },
      {
        file: 'lib/index.umd.js',
        format: 'umd',
        exports: 'named',
        name: 'railroadDiagrams',
        sourcemap
      },
      {
        file: 'lib/index.umd.min.js',
        format: 'umd',
        exports: 'named',
        name: 'railroadDiagrams',
        sourcemap,
        plugins: [terser()]
      }
    ],
    external,
    plugins
  },
  {
    input: 'rrd2svg.js',
    output: {
      file: 'bin/rrd2svg',
      format: 'cjs',
      paths,
      banner,
      sourcemap
    },
    external,
    plugins
  },
  {
    input: 'rrdlint.js',
    output: {
      file: 'bin/rrdlint',
      format: 'cjs',
      paths,
      banner,
      sourcemap
    },
    external,
    plugins
  }
];
