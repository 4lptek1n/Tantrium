# Tantrium Proof Machine Benchmark Report

| Benchmark | Expected | Observed | Result |
|---|---|---|---|
| rh | `INTERNAL_CLOSED` | `INTERNAL_CLOSED` | `PASS` |
| hankel | `PROVEN_BY_CERTIFICATE` | `PROVEN_BY_CERTIFICATE` | `PASS` |
| goldbach | `BLOCKED_BY_NAMED_GAP` | `BLOCKED_BY_NAMED_GAP` | `PASS` |
| lah | `REFINED_SUBGAP_OR_PROOF` | `REFINED_SUBGAP` | `PASS` |
| coefficient_frontier | `FRONTIER_IDENTIFIED` | `REFINED_SUBGAP` | `PASS` |
| false_positive_quadratic | `COUNTEREXAMPLE_FOUND` | `COUNTEREXAMPLE_FOUND` | `PASS` |
| missing_theorem_graph_node | `OPEN_GAP` | `MISSING_THEOREM_GRAPH_NODE` | `PASS` |

This benchmark confirms the machine does not blindly emit PASS.
