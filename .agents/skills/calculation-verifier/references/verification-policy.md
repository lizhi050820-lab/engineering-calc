# Verification policy

## Evidence hierarchy

Use multiple independent layers. Higher layers do not replace lower ones.

1. Published standard clauses and official worked examples.
2. Trusted textbook examples with complete assumptions and units.
3. Hand derivations checked dimensionally.
4. Independent Python/Decimal/SymPy implementation.
5. Mathematical properties and metamorphic relations.
6. Website JavaScript implementation.

The Python backend is independent enough for differential regression because it predates the browser port, but it is not an authority by itself. A shared wrong formula can still pass differential testing.

## Case classes

- Typical: ordinary design ranges and common material grades.
- Branch: minimum reinforcement, limiting compression zone, double reinforcement, support changes, saturation, critical gradient, slip/bearing control.
- Boundary: minimum positive dimensions, maximum UI values, positions at member ends, equal geometric dimensions, nearly limiting ratios.
- Invalid: zero, negative, missing, reversed ranges, impossible geometry, nonphysical saturation, unsupported grades.
- Random: legal values generated from a recorded seed.

## Numeric comparison

Compare unrounded internal results where both sides expose them. Otherwise compare the published precision.

Use:

`|actual − expected| ≤ absolute_tolerance + relative_tolerance × |expected|`

Default differential tolerances:

- displayed three-decimal values: absolute `0.0011`;
- reinforcement area displayed to 0.1 mm²: absolute `0.11`;
- centroid and radius values displayed to 0.1 mm: absolute `0.1000001` (permits one last-place difference only at a rounding tie);
- reinforcement ratios displayed to four decimals: absolute `0.00011`;
- large section properties rounded to integer units: absolute `1.1`;
- unrounded dimensionless values: relative `1×10⁻⁹` when implementations expose the same formula stage.

Never hide NaN, Infinity, missing fields, or sign disagreement behind a large relative tolerance.

## Failure handling

1. Re-run the exact seed and case id.
2. Reduce the failing case to the smallest useful input.
3. Check units and rounding before changing formulas.
4. Decide which implementation disagrees with the governing source.
5. Fix the incorrect implementation.
6. Add the reduced case as a permanent fixed regression.
7. Re-run the full suite.

## Reporting

Every report must contain repository revision, timestamp, seed, case count, tool-level pass rate, maximum error, failures, and commands used. A 100% differential pass rate means the implementations agree; it does not by itself prove that the governing engineering formula is correct.
