#!/usr/bin/env node
// Compile-checks .ink files with inkjs and reports errors. Usage: node ink-check.js <file...>
const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');
const inkRequire = createRequire(path.join(__dirname, '..', 'ink-app', 'package.json'));
const { Compiler } = inkRequire('inkjs/full');

let failed = 0;
for (const file of process.argv.slice(2)) {
  const src = fs.readFileSync(file, 'utf8');
  const messages = [];
  try {
    new Compiler(src, {
      errorHandler: (msg, type) => messages.push(`${type === 3 ? 'ERROR' : 'WARN'}: ${msg}`),
    }).Compile();
  } catch (e) {
    messages.push(`ERROR: ${e.message}`);
  }
  const errors = messages.filter((m) => m.startsWith('ERROR'));
  if (errors.length) {
    failed++;
    console.log(`FAIL ${path.basename(file)}`);
    for (const m of errors) console.log(`   ${m}`);
  } else {
    console.log(`OK   ${path.basename(file)}`);
  }
}
console.log(failed ? `\n${failed} file(s) failed` : `\nall ${process.argv.length - 2} file(s) compiled`);
process.exit(failed ? 1 : 0);
