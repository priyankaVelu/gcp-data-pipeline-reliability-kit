# Retained bundle benchmark results

Synthetic model only. Ratios exclude undefined zero-optimum cases. Timing is local wall time, not cloud performance. Candidate work units differ between policy families.

| Phase | Mode | Policy | Optimum matches | Ratio min / median | Cost median | Candidate median | Solver ms median |
|---|---|---|---:|---:|---:|---:|---:|
| expanded | no_sharing | bundle_2 | 21/36 | 0.8155 / 1.0000 | 14.00 | 153.0 | 0.406 |
| expanded | no_sharing | bundle_3 | 21/36 | 0.8155 / 1.0000 | 14.00 | 540.5 | 0.763 |
| expanded | no_sharing | cost_aware_greedy | 14/36 | 0.6090 / 0.9453 | 13.00 | 27.0 | 0.214 |
| expanded | no_sharing | coverage_greedy | 20/36 | 0.5980 / 1.0000 | 14.00 | 26.5 | 0.189 |
| expanded | no_sharing | exact | 36/36 | 1.0000 / 1.0000 | 12.00 | 54.0 | 0.275 |
| expanded | no_sharing | risk_aware_greedy | 21/36 | 0.8155 / 1.0000 | 14.00 | 27.0 | 0.226 |
| expanded | shared | bundle_2 | 23/36 | 0.8155 / 1.0000 | 12.50 | 174.5 | 0.410 |
| expanded | shared | bundle_3 | 23/36 | 0.8155 / 1.0000 | 12.50 | 460.5 | 0.769 |
| expanded | shared | cost_aware_greedy | 18/36 | 0.3683 / 0.9980 | 12.00 | 37.0 | 0.189 |
| expanded | shared | coverage_greedy | 20/36 | 0.6296 / 1.0000 | 13.50 | 37.0 | 0.198 |
| expanded | shared | exact | 36/36 | 1.0000 / 1.0000 | 13.00 | 115.0 | 0.343 |
| expanded | shared | risk_aware_greedy | 19/36 | 0.6405 / 1.0000 | 12.50 | 37.0 | 0.221 |
| frozen | no_sharing | bundle_2 | 40/54 | 0.8726 / 1.0000 | 9.50 | 144.0 | 0.379 |
| frozen | no_sharing | bundle_3 | 40/54 | 0.8726 / 1.0000 | 9.50 | 459.0 | 0.523 |
| frozen | no_sharing | cost_aware_greedy | 32/54 | 0.6013 / 1.0000 | 10.00 | 27.0 | 0.203 |
| frozen | no_sharing | coverage_greedy | 36/54 | 0.7183 / 1.0000 | 9.00 | 27.0 | 0.188 |
| frozen | no_sharing | exact | 54/54 | 1.0000 / 1.0000 | 9.00 | 40.0 | 0.260 |
| frozen | no_sharing | risk_aware_greedy | 40/54 | 0.8726 / 1.0000 | 9.50 | 27.0 | 0.213 |
| frozen | shared | bundle_2 | 43/54 | 0.9135 / 1.0000 | 8.00 | 159.5 | 0.442 |
| frozen | shared | bundle_3 | 43/54 | 0.9135 / 1.0000 | 8.00 | 459.0 | 0.664 |
| frozen | shared | cost_aware_greedy | 39/54 | 0.6013 / 1.0000 | 9.00 | 34.0 | 0.191 |
| frozen | shared | coverage_greedy | 45/54 | 0.8130 / 1.0000 | 9.00 | 33.0 | 0.194 |
| frozen | shared | exact | 54/54 | 1.0000 / 1.0000 | 8.00 | 49.0 | 0.334 |
| frozen | shared | risk_aware_greedy | 42/54 | 0.7879 / 1.0000 | 8.00 | 34.0 | 0.221 |

## Paired outcomes and seed sensitivity

Wins/ties/losses compare union risk at identical budgets within the same cost mode. Seed means average defined optimum-ratio deltas across each seed’s coupled configurations. Range and sample SD describe only three seeds per phase; these are not confidence intervals or independent population estimates.

| Phase/mode/policy | Baseline | Win/tie/loss | Seed means | Mean | Range | Sample SD |
|---|---|---|---|---:|---|---:|
| expanded/no_sharing/bundle_2 | bundle_2 | 0/36/0 | {'101': 0.0, '211': 0.0, '43': 0.0} | 0.00000 | [0.0, 0.0] | 0.00000 |
| expanded/no_sharing/bundle_2 | cost_aware_greedy | 15/19/2 | {'101': 0.03844416237773538, '211': 0.017078460589344428, '43': 0.13338945700634555} | 0.06297 | [0.017078460589344428, 0.13338945700634555] | 0.06191 |
| expanded/no_sharing/bundle_2 | coverage_greedy | 14/15/7 | {'101': -0.0026150215969544745, '211': 0.021454861530602092, '43': 0.0931677228005861} | 0.03734 | [-0.0026150215969544745, 0.0931677228005861] | 0.04983 |
| expanded/no_sharing/bundle_2 | risk_aware_greedy | 0/36/0 | {'101': 0.0, '211': 0.0, '43': 0.0} | 0.00000 | [0.0, 0.0] | 0.00000 |
| expanded/no_sharing/bundle_3 | bundle_2 | 0/36/0 | {'101': 0.0, '211': 0.0, '43': 0.0} | 0.00000 | [0.0, 0.0] | 0.00000 |
| expanded/no_sharing/bundle_3 | cost_aware_greedy | 15/19/2 | {'101': 0.03844416237773538, '211': 0.017078460589344428, '43': 0.13338945700634555} | 0.06297 | [0.017078460589344428, 0.13338945700634555] | 0.06191 |
| expanded/no_sharing/bundle_3 | coverage_greedy | 14/15/7 | {'101': -0.0026150215969544745, '211': 0.021454861530602092, '43': 0.0931677228005861} | 0.03734 | [-0.0026150215969544745, 0.0931677228005861] | 0.04983 |
| expanded/no_sharing/bundle_3 | risk_aware_greedy | 0/36/0 | {'101': 0.0, '211': 0.0, '43': 0.0} | 0.00000 | [0.0, 0.0] | 0.00000 |
| expanded/shared/bundle_2 | bundle_2 | 0/36/0 | {'101': 0.0, '211': 0.0, '43': 0.0} | 0.00000 | [0.0, 0.0] | 0.00000 |
| expanded/shared/bundle_2 | cost_aware_greedy | 11/22/3 | {'101': -0.0077368250332735, '211': 0.023322447948800954, '43': 0.13480047456036098} | 0.05013 | [-0.0077368250332735, 0.13480047456036098] | 0.07495 |
| expanded/shared/bundle_2 | coverage_greedy | 14/15/7 | {'101': -0.007106185032877225, '211': -0.006872096170389058, '43': 0.11652715336714241} | 0.03418 | [-0.007106185032877225, 0.11652715336714241] | 0.07131 |
| expanded/shared/bundle_2 | risk_aware_greedy | 7/26/3 | {'101': 0.005208158785496725, '211': 0.04749385190023208, '43': 0.025953836891578604} | 0.02622 | [0.005208158785496725, 0.04749385190023208] | 0.02114 |
| expanded/shared/bundle_3 | bundle_2 | 0/36/0 | {'101': 0.0, '211': 0.0, '43': 0.0} | 0.00000 | [0.0, 0.0] | 0.00000 |
| expanded/shared/bundle_3 | cost_aware_greedy | 11/22/3 | {'101': -0.0077368250332735, '211': 0.023322447948800954, '43': 0.13480047456036098} | 0.05013 | [-0.0077368250332735, 0.13480047456036098] | 0.07495 |
| expanded/shared/bundle_3 | coverage_greedy | 14/15/7 | {'101': -0.007106185032877225, '211': -0.006872096170389058, '43': 0.11652715336714241} | 0.03418 | [-0.007106185032877225, 0.11652715336714241] | 0.07131 |
| expanded/shared/bundle_3 | risk_aware_greedy | 7/26/3 | {'101': 0.005208158785496725, '211': 0.04749385190023208, '43': 0.025953836891578604} | 0.02622 | [0.005208158785496725, 0.04749385190023208] | 0.02114 |
| frozen/no_sharing/bundle_2 | bundle_2 | 0/54/0 | {'17': 0.0, '29': 0.0, '7': 0.0} | 0.00000 | [0.0, 0.0] | 0.00000 |
| frozen/no_sharing/bundle_2 | cost_aware_greedy | 17/33/4 | {'17': 0.021379261956085336, '29': 0.07022253737518055, '7': 0.05802934800414551} | 0.04988 | [0.021379261956085336, 0.07022253737518055] | 0.02542 |
| frozen/no_sharing/bundle_2 | coverage_greedy | 15/32/7 | {'17': 0.003994462598496316, '29': 0.07022253737518055, '7': 0.0225540979931918} | 0.03226 | [0.003994462598496316, 0.07022253737518055] | 0.03416 |
| frozen/no_sharing/bundle_2 | risk_aware_greedy | 0/54/0 | {'17': 0.0, '29': 0.0, '7': 0.0} | 0.00000 | [0.0, 0.0] | 0.00000 |
| frozen/no_sharing/bundle_3 | bundle_2 | 0/54/0 | {'17': 0.0, '29': 0.0, '7': 0.0} | 0.00000 | [0.0, 0.0] | 0.00000 |
| frozen/no_sharing/bundle_3 | cost_aware_greedy | 17/33/4 | {'17': 0.021379261956085336, '29': 0.07022253737518055, '7': 0.05802934800414551} | 0.04988 | [0.021379261956085336, 0.07022253737518055] | 0.02542 |
| frozen/no_sharing/bundle_3 | coverage_greedy | 15/32/7 | {'17': 0.003994462598496316, '29': 0.07022253737518055, '7': 0.0225540979931918} | 0.03226 | [0.003994462598496316, 0.07022253737518055] | 0.03416 |
| frozen/no_sharing/bundle_3 | risk_aware_greedy | 0/54/0 | {'17': 0.0, '29': 0.0, '7': 0.0} | 0.00000 | [0.0, 0.0] | 0.00000 |
| frozen/shared/bundle_2 | bundle_2 | 0/54/0 | {'17': 0.0, '29': 0.0, '7': 0.0} | 0.00000 | [0.0, 0.0] | 0.00000 |
| frozen/shared/bundle_2 | cost_aware_greedy | 8/45/1 | {'17': 0.03399066102155765, '29': 0.02245011086474501, '7': 0.01708353165043318} | 0.02451 | [0.01708353165043318, 0.03399066102155765] | 0.00864 |
| frozen/shared/bundle_2 | coverage_greedy | 7/39/8 | {'17': 0.009561586160605071, '29': 0.019367496808024912, '7': -0.0062120471871555194} | 0.00757 | [-0.0062120471871555194, 0.019367496808024912] | 0.01291 |
| frozen/shared/bundle_2 | risk_aware_greedy | 3/51/0 | {'17': 0.0, '29': 0.022965474722564737, '7': 0.005544943224026318} | 0.00950 | [0.0, 0.022965474722564737] | 0.01198 |
| frozen/shared/bundle_3 | bundle_2 | 0/54/0 | {'17': 0.0, '29': 0.0, '7': 0.0} | 0.00000 | [0.0, 0.0] | 0.00000 |
| frozen/shared/bundle_3 | cost_aware_greedy | 8/45/1 | {'17': 0.03399066102155765, '29': 0.02245011086474501, '7': 0.01708353165043318} | 0.02451 | [0.01708353165043318, 0.03399066102155765] | 0.00864 |
| frozen/shared/bundle_3 | coverage_greedy | 7/39/8 | {'17': 0.009561586160605071, '29': 0.019367496808024912, '7': -0.0062120471871555194} | 0.00757 | [-0.0062120471871555194, 0.019367496808024912] | 0.01291 |
| frozen/shared/bundle_3 | risk_aware_greedy | 3/51/0 | {'17': 0.0, '29': 0.022965474722564737, '7': 0.005544943224026318} | 0.00950 | [0.0, 0.022965474722564737] | 0.01198 |

## Deterministic fixtures

| Fixture/mode | Policy | Union risk | Cost |
|---|---|---:|---:|
| overlap/no_sharing | exact | 50 | 5 |
| overlap/no_sharing | risk_aware_greedy | 50 | 5 |
| overlap/no_sharing | coverage_greedy | 22 | 5 |
| overlap/no_sharing | cost_aware_greedy | 22 | 5 |
| overlap/no_sharing | bundle_2 | 50 | 5 |
| overlap/no_sharing | bundle_3 | 50 | 5 |
| overlap/shared | exact | 52 | 6 |
| overlap/shared | risk_aware_greedy | 52 | 6 |
| overlap/shared | coverage_greedy | 52 | 6 |
| overlap/shared | cost_aware_greedy | 52 | 6 |
| overlap/shared | bundle_2 | 52 | 6 |
| overlap/shared | bundle_3 | 52 | 6 |
| shared_scan_trap/no_sharing | exact | 12 | 6 |
| shared_scan_trap/no_sharing | risk_aware_greedy | 12 | 6 |
| shared_scan_trap/no_sharing | coverage_greedy | 12 | 6 |
| shared_scan_trap/no_sharing | cost_aware_greedy | 12 | 6 |
| shared_scan_trap/no_sharing | bundle_2 | 12 | 6 |
| shared_scan_trap/no_sharing | bundle_3 | 12 | 6 |
| shared_scan_trap/shared | exact | 16 | 7 |
| shared_scan_trap/shared | risk_aware_greedy | 12 | 6 |
| shared_scan_trap/shared | coverage_greedy | 12 | 6 |
| shared_scan_trap/shared | cost_aware_greedy | 12 | 6 |
| shared_scan_trap/shared | bundle_2 | 16 | 7 |
| shared_scan_trap/shared | bundle_3 | 16 | 7 |
| triple_trap/no_sharing | exact | 15 | 6 |
| triple_trap/no_sharing | risk_aware_greedy | 15 | 6 |
| triple_trap/no_sharing | coverage_greedy | 8 | 6 |
| triple_trap/no_sharing | cost_aware_greedy | 8 | 6 |
| triple_trap/no_sharing | bundle_2 | 15 | 6 |
| triple_trap/no_sharing | bundle_3 | 15 | 6 |
| triple_trap/shared | exact | 24 | 8 |
| triple_trap/shared | risk_aware_greedy | 15 | 6 |
| triple_trap/shared | coverage_greedy | 24 | 8 |
| triple_trap/shared | cost_aware_greedy | 24 | 8 |
| triple_trap/shared | bundle_2 | 15 | 6 |
| triple_trap/shared | bundle_3 | 24 | 8 |

All 216 historical shared baseline rows reproduce every non-timing field. See results.json for all selected plans, timings, step witnesses, gaps and zero-optimum ratios; inputs.json retains both cost modes. SHA256.json authenticates the retained measurement files.

