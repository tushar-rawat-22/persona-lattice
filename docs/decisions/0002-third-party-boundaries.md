# ADR 0002 — third-party boundaries

**Status:** accepted for bootstrap

PersonaLattice does not copy "the best parts" of open-source projects into one
codebase indiscriminately.

Instead:

- original PersonaLattice code is Apache-2.0;
- MIT projects may later be used through explicit adapters with their notices;
- CC BY-SA datasets are kept outside the Apache core until the share-alike
  implications are reviewed;
- MPL files are not copied into core modules without preserving MPL obligations;
- GPL code is not copied into the core;
- provider API terms are reviewed separately from software licenses.

At bootstrap, no third-party OSINT code is vendored.
