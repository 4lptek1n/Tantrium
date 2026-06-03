# Moment / Path Program

## Goal

Find a positive moment or path model for the Newton sums and Hankel tau determinants.

The target shape is:

```text
s_m(d,t) = sum positive_weight * positive_node^m
```

or a path model whose Hankel determinant expands as a positive sum over nonintersecting paths.

## Why this matters

If the Newton sums admit a positive moment model, then the Hermite-Hankel determinants may inherit positivity from moment theory. If a path model exists, a Lindstrom-Gessel-Viennot style determinant expansion could make tau positivity structural.

This could prove whole families of H_{d,j}(t) at once instead of proving each coefficient separately.

## Current clue

The project has repeatedly observed binomial-positive behavior in signed Newton sums. This suggests that the source of coefficient positivity may live before the determinant stage.

## Search tasks

1. Express signed Newton sums in a positive binomial basis.
2. Test whether the basis has a moment interpretation.
3. Search for a path graph whose path weights reproduce s_m(d,t).
4. Compare determinant expansions with the coefficient atlas.
5. Use failures, if any, to refine the model.

## Status

Open. This is the main theoretical route beyond finite atlas evidence.
