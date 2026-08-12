# Backlog

Working queue. The next unchecked item is the one being built. An item stays
unchecked and picks up a `status:` note if it spans more than one working
session — finishing something half-built takes priority over starting the next
one.

Rules of thumb applied to every item:

- one job per tool, done properly, rather than a suite of half-features
- standard library unless a dependency earns its place
- tests that assert a real property, not that the code ran
- a README that says what the tool is *not* for
- any published factor, threshold or rate gets a citation and a vintage

---

## Done

- [x] **001 — dimensions** · Exact rational dimension algebra over the seven SI base dimensions, with the abelian group axioms asserted directly. 41 tests, zero dependencies.

## Queue

- [ ] **002 — quantity** · A quantity type carrying magnitude and unit, with arithmetic that refuses to add incompatible dimensions.
- [ ] **003 — registry** · Unit parsing and a registry covering the energy, mass, emissions and currency-per-unit vocabulary these models actually use.
- [ ] **004 — carbon-units** · The conversions that bite: carbon versus carbon dioxide, CO2 versus CO2e, and global warming potentials that differ by IPCC assessment report.
- [ ] **005 — ambiguity** · Raise rather than resolve when a conversion is underdetermined, and say what extra information would settle it.
- [ ] **006 — check-formula** · Dimensional analysis over an expression tree, reporting the first inconsistent operation rather than the last.
- [ ] **007 — check-table** · Infer column dimensions from headers and data, and flag arithmetic between columns that cannot be dimensionally valid.
- [ ] **008 — annotations** · Check function signatures at call time from ordinary type annotations, with no runtime cost when disabled.
- [ ] **009 — report** · Human-readable violation reports that point at the offending operation and suggest the conversion that would fix it.
- [ ] **010 — cli** · Check a file or a directory from the terminal and exit non-zero on a violation, so it can sit in CI.
