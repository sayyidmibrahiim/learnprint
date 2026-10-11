# Why Python, not Go/Rust (October 2026)

**Decision: keep the tested Python 3.9+ standard-library engine during teaching-workflow hardening.**

Current defects are learner experience and data/evidence integrity problems, not
benchmarked CPU performance bottlenecks. Rewriting in another language cannot
make a tutor follow its teaching protocol, provide a syllabus, or create honest grades.

- Python: needs interpreter; fast iteration; stdlib JSON, locking and filesystem
  already tested on Windows, macOS, Ubuntu in the current repository.
- Go: native binaries and generally lower CLI cold startup overhead, but require
  builds for supported OS/architecture and a port of the state/ledger engine.
- Rust: native code and strong memory-safety tools, but requires build targets
  and sometimes target-specific linkers; port/revalidation is significant.

No numeric speedup is claimed because no comparison benchmark was run.
Benchmark cold CLI startup, 10k/100k JSONL records, durability, actual
concurrent appends and crash recovery on real users' supported platforms.
Do not migrate before proving measured benefit and backward-compatible
learner data and parity of the full regression suite.

References:
- Python stdlib: https://docs.python.org/3/library/index.html
- Go target toolchains: https://go.dev/doc/install/source
- Rust targets: https://rust-lang.github.io/rustup/cross-compilation.html
