import { Suite } from 'benchmark';

function createSuite (description) {
  const suite = new Suite();
  suite.start = () => suite.run();
  console.log(description);
  return suite
    .on('cycle', ({ target }) => {
      const { error, name } = target;
      if (error) {
        console.error(`  ${name} failed`);
      } else {
        console.log(`  ${target}`);
      }
    })
    .on('error', ({ target }) => console.warn(target.error))
    .on('complete', () =>
      console.log(`The fastest one was ${suite.filter('fastest').map('name')[0]}.`));
}

export default createSuite;
