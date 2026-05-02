# Subresultant Recurrence Campaign Report

Status: `RECURRENCE_VERIFIED_FINITE`
Best candidate: `QJR_DEGREE_R_STEP`
Refined subgap: `MISSING_TRUE_H_QUOTIENT_IDENTIFICATION_FOR_QJR`

## Inventory

- Source files scanned: `10`
- Engine CSV files inventoried: `38`
- QJR rows generated: `65`

## Ranked Recurrences

- `QJR_DEGREE_R_STEP` score `0.91`: D(j,r)-D(j,r-1)=j-r for 1<=r<=j.
- `QJR_DEGREE_J_SHIFT` score `0.88`: D(j+1,r)-D(j,r)=r for D(j,r)=r(2j-r-1)/2.
- `QJR_NORMAL_FORM_R_RECURRENCE` score `0.84`: Q(j,r;n)=Q(j,r-1;n)*prod_{a=D(j,r-1)+1}^{D(j,r)}(n+a) in the documented normal form.
- `TOP_RAMP_J_RECURRENCE` score `0.78`: A_j(n)/A_{j-1}(n)=2^j(n+j)^j for fixed n under the top-ramp normal form.
- `SUBRESULTANT_CROSS_RATIO_RECURRENCE_SCHEMA` score `0.73`: rho_{d,j}(t)=C_{d,j} t^{k_{d,j}} H_{d,j-2}H_{d,j}/H_{d,j-1}^2 should induce an r-step quotient recurrence after staircase divisor extraction.

## Verification

Finite checks passed: `True`

No theorem is promoted here. The remaining mathematical obstruction is identifying the normal-form recurrence with the true hidden H quotient extracted from the subresultant chain.
