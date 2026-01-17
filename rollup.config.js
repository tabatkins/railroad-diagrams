import resolve from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import babel from '@rollup/plugin-babel';

export default {
  input: 'railroad.js', // Pfad zur Originalquelle
  output: {
    file: 'dist/railroad-diagrams.umd.js',
    format: 'umd',        // UMD für Browser
    name: 'railroad',     // globale Variable
    sourcemap: true
  },
  plugins: [
    resolve(),
    commonjs(),
    babel({
      babelHelpers: 'bundled',
      presets: ['@babel/preset-env']
    })
  ]
};
