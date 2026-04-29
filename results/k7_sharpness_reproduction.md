# K7 sharpness reproduction

This report locally reevaluates the trailing `7 x 7` Bezoutian block used for `H_{d,6}`.
It avoids the full symbolic determinant and instead evaluates the same recurrence numerically at high precision.

The decisive sharpness certificate is the `d=7` sign change near `t=0.041`.

## d=7

- elapsed seconds: `0.706`
- positive root in `[0.04,0.05]`: `0.04092732272294692967755645840492358540672`

| t | normalized det K7 | sign |
|---:|---:|:---:|
| `0` | `1.0` | + |
| `0.001` | `28.574000372242549125365734098255` | + |
| `0.01` | `2952.0966644094996965434225674872` | + |
| `0.02` | `17741.965448116498449612966855291` | + |
| `0.04` | `19363.925524981299582551513576861` | + |
| `0.041` | `-1771.2400046388415222624280542187` | - |
| `0.042` | `-30424.805901304833524083586416358` | - |
| `0.05` | `-721411.28779072997391556784702856` | - |
| `0.1` | `246171202627.69436003070440131942` | + |
| `1` | `2.2830892908880523902419815188597e+33` | + |

## d=8

- elapsed seconds: `0.070`

| t | normalized det K7 | sign |
|---:|---:|:---:|
| `0` | `1.0` | + |
| `0.001` | `-6.2395419485863026257956990133548` | - |
| `0.01` | `-950.85475564061765042408863400709` | - |
| `0.02` | `-4694.5246675559098247885707872827` | - |
| `0.04` | `254880.28305596349821727540004355` | + |
| `0.041` | `229428.31788272516943779397406102` | + |
| `0.042` | `135392.44086199031717478796765949` | + |
| `0.05` | `-18608637.492259804710819885089424` | - |
| `0.1` | `-69250017806714.317018796266566147` | - |
| `1` | `-4.1935386323949094860356768726787e+35` | - |

## Conclusion

- The `d=7` sign change is reproduced and is enough to prove that universal `j=6` positivity fails.
- The `d=8` sample is negative at `t=0.001`, matching the small-positive failure signal.
- The sampled `d=8` sign profile is not monotone in this normalized determinant evaluation, so the stronger phrase `H_{8,6}(t)<0 for all t>0` should be treated as requiring an exact artifact audit before being used as a proof claim.
