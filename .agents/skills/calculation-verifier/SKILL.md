---
name: calculation-verifier
description: Batch-verify civil and structural engineering calculators with independent Python references, deterministic random cases, boundary cases, mathematical properties, and reproducible reports. Use when adding, changing, auditing, validating, or releasing any calculator in the engineering-calc repository, or when a user asks to 验算、批量算例验证、正确性检查、随机测试、边界测试、差分测试 or calculation QA.
---

# Engineering Calculation Verifier

Use independent evidence to verify calculations. Never treat a successful build or a duplicated formula as proof of correctness.

## Required verification layers

1. Run authoritative fixed examples from standards, textbooks, or manually checked derivations.
2. Run Python/JavaScript differential cases with a fixed seed.
3. Test valid boundaries, invalid inputs, and branch thresholds.
4. Test mathematical properties such as symmetry, equilibrium, monotonicity, conservation, and scaling.
5. Build H5 to verify page integration.
6. Test the visible website only when browser interaction is explicitly requested.

Read [verification-policy.md](references/verification-policy.md) before deciding that a tool passes. Read [tool-contracts.md](references/tool-contracts.md) when adding or changing a calculator.

## Run the current project suite

From the repository root, run:

```powershell
pnpm run test:authoritative-cases
python .agents/skills/calculation-verifier/scripts/verify_project.py --cases-per-tool 500
```

If `node` is not on PATH, pass its executable:

```powershell
python .agents/skills/calculation-verifier/scripts/verify_project.py --node C:\path\to\node.exe --cases-per-tool 500
```

Use `--seed` to reproduce a run and `--tools` to limit the run. Reports are written to `verification/reports/` unless `--report` is provided.

## Interpret results

- Treat any mismatch, unexpected exception, missing field, or non-finite value as a failure.
- Report the exact seed, tool, input, Python result, JavaScript result, absolute error, and tolerance.
- Do not weaken tolerance merely to make a failure pass. Explain the engineering precision that justifies a tolerance change.
- Distinguish formula errors from display-rounding differences.
- Preserve the first failing cases as permanent regression tests after fixing a defect.

## Add a calculator

1. Add its generator to `verify_project.py`.
2. Add an independent Python reference adapter.
3. Add its JavaScript adapter to `js_batch_runner.mjs`.
4. Declare compared fields and justified tolerances.
5. Add at least one authoritative fixed example and one invalid-input case to the project tests.
6. Add at least two mathematical properties to [tool-contracts.md](references/tool-contracts.md).
7. Run at least 500 deterministic cases before merge and at least 5,000 before a public release.

## Release gate

Do not call a calculator verified unless:

- fixed examples pass;
- differential tests pass at the declared tolerance;
- boundary and invalid-input tests pass;
- required properties pass;
- Python regression tests pass;
- browser calculation tests pass;
- H5 build succeeds;
- the report records the seed and case count.

When external standards or published examples are used, record the exact edition, clause/page, units, and any assumptions. Never invent an authoritative source.
