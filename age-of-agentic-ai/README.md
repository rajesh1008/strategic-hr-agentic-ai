# Strategic HR in the Age of Agentic AI: companion code

Code listings for **Strategic HR in the Age of Agentic AI: Decisions, Evidence and Value for the CHRO** by Rajesh Ranjan Mahapatra and Abhishek Agrawal (AI at Work series).

Every listing printed in the book is here as a file, in the chapter folder it belongs to. Each Python, YAML and SQL file starts with a header naming the chapter and the listing title as printed. The book is the reference: if a file and the page ever disagree, the page wins, so please open an issue.

> All organisations, people and figures here are the book's worked examples or synthetic data. Nothing here is legal advice, and no listing makes a decision about a person: each one stops where the book says a person decides.

## How to use it

```bash
git clone https://github.com/rajesh1008/strategic-hr-agentic-ai.git
cd strategic-hr-agentic-ai/age-of-agentic-ai
python3 ch11_wrong_pay/02_recompute_every_line_route_every_unknown.py
python3 -m pytest -q ../tests/test_age_of_agentic_ai_listings.py   # parses every listing; no key, no network
```

Python 3.11 or later. The listings use the standard library only, except two noted below. Status in the index:

- **Runs as is**: `python3 <file>` completes with no setup.
- **Excerpt**: a fragment from a longer pipeline, printed in the book to show one step. It parses, but needs data or a library that is not part of the listing.
- **Data**: a YAML, JSON or SQL artefact (an agent brief, a registry entry, a handover envelope, a query). The SQL is portable and written against the table names used in the chapter.

## Index by chapter


### Chapter 1: Which Case

| Listing | File | Status |
|---|---|---|
| The Ledger Type: Lines Never Mix *(Under the Hood)* | [`01_the_ledger_type_lines_never_mix.py`](ch01_which_case/01_the_ledger_type_lines_never_mix.py) | Runs; the last line raises the deliberate `TypeError` the chapter describes |
| One Definition, Every Record *(Under the Hood)* | [`02_one_definition_every_record.py`](ch01_which_case/02_one_definition_every_record.py) | Runs as is |

### Chapter 2: Twenty-One Ideas

| Listing | File | Status |
|---|---|---|
| The Agent Brief as a Spec | [`01_the_agent_brief_as_a_spec.yaml`](ch02_twenty_one_ideas/01_the_agent_brief_as_a_spec.yaml) | Data |
| Seal the Set, Then Check for Leaks *(Under the Hood)* | [`02_seal_the_set_then_check_for_leaks.py`](ch02_twenty_one_ideas/02_seal_the_set_then_check_for_leaks.py) | Runs as is |
| The Bound in Three Lines *(Under the Hood)* | [`03_the_bound_in_three_lines.py`](ch02_twenty_one_ideas/03_the_bound_in_three_lines.py) | Runs as is |
| Stability Under Random Weights *(Under the Hood)* | [`04_stability_under_random_weights.py`](ch02_twenty_one_ideas/04_stability_under_random_weights.py) | Runs as is |

### Chapter 3: 549 Hours

| Listing | File | Status |
|---|---|---|
| Who May Receive a Flag *(Under the Hood)* | [`01_who_may_receive_a_flag.py`](ch03_549_hours/01_who_may_receive_a_flag.py) | Runs as is |
| Break-Even, Net Hours and the Doubled-Review Case *(Under the Hood)* | [`02_break_even_net_hours_and_the_doubled_review_case.py`](ch03_549_hours/02_break_even_net_hours_and_the_doubled_review_case.py) | Runs as is |
| The Pune Associate Job, as Data *(Under the Hood)* | [`03_the_pune_associate_job_as_data.yaml`](ch03_549_hours/03_the_pune_associate_job_as_data.yaml) | Data |

### Chapter 4: Seats and People

| Listing | File | Status |
|---|---|---|
| Clean the ID Before Any Model *(Under the Hood)* | [`01_clean_the_id_before_any_model.py`](ch04_seats_and_people/01_clean_the_id_before_any_model.py) | Runs as is |
| Weighted Linkage, Three Routes *(Under the Hood)* | [`02_weighted_linkage_three_routes.py`](ch04_seats_and_people/02_weighted_linkage_three_routes.py) | Runs as is |
| Widening Raw Intervals to Their Stated Coverage *(Under the Hood)* | [`03_widening_raw_intervals_to_their_stated_coverage.py`](ch04_seats_and_people/03_widening_raw_intervals_to_their_stated_coverage.py) | Runs as is |
| The Reason the CFO Cares About Goes to a Person *(Under the Hood)* | [`04_the_reason_the_cfo_cares_about_goes_to_a_person.py`](ch04_seats_and_people/04_the_reason_the_cfo_cares_about_goes_to_a_person.py) | Runs as is |
| The Sourcing Model *(Under the Hood)* | [`05_the_sourcing_model.py`](ch04_seats_and_people/05_the_sourcing_model.py) | Needs `pip install pulp` |

### Chapter 5: 46 Days

| Listing | File | Status |
|---|---|---|
| A Machine Rejects No Candidate | [`01_a_machine_rejects_no_candidate.py`](ch05_46_days/01_a_machine_rejects_no_candidate.py) | Runs as is |
| Offer Approval: Two Signatures or Four *(Under the Hood)* | [`02_offer_approval_two_signatures_or_four.py`](ch05_46_days/02_offer_approval_two_signatures_or_four.py) | Runs as is |
| The Only Shortlist Operation the Matcher Has *(Under the Hood)* | [`03_the_only_shortlist_operation_the_matcher_has.py`](ch05_46_days/03_the_only_shortlist_operation_the_matcher_has.py) | Runs as is |
| Group Applications by Shared Identifiers *(Under the Hood)* | [`04_group_applications_by_shared_identifiers.py`](ch05_46_days/04_group_applications_by_shared_identifiers.py) | Runs as is |

### Chapter 6: Overlooked for Promotion

| Listing | File | Status |
|---|---|---|
| The Pool Rule *(Under the Hood)* | [`01_the_pool_rule.py`](ch06_overlooked_for_promotion/01_the_pool_rule.py) | Runs as is |
| Quote, Do Not Paraphrase *(Under the Hood)* | [`02_quote_do_not_paraphrase.py`](ch06_overlooked_for_promotion/02_quote_do_not_paraphrase.py) | Runs as is |

### Chapter 7: The One Person

| Listing | File | Status |
|---|---|---|
| The Holdout That Measures the Save Rate *(Under the Hood)* | [`01_the_holdout_that_measures_the_save_rate.py`](ch07_the_one_person/01_the_holdout_that_measures_the_save_rate.py) | Runs as is |
| Single Points of Knowledge *(Under the Hood)* | [`02_single_points_of_knowledge.sql`](ch07_the_one_person/02_single_points_of_knowledge.sql) | Data |

### Chapter 8: Defend This Salary

| Listing | File | Status |
|---|---|---|
| Route a Benchmark Match *(Under the Hood)* | [`01_route_a_benchmark_match.py`](ch08_defend_this_salary/01_route_a_benchmark_match.py) | Runs as is |
| The Red Rule From the Quarterly Note *(Under the Hood)* | [`02_the_red_rule_from_the_quarterly_note.py`](ch08_defend_this_salary/02_the_red_rule_from_the_quarterly_note.py) | Runs as is |
| The Offer Check: Fund Peers at the 90th, or Add an Expiry *(Under the Hood)* | [`03_the_offer_check_fund_peers_at_the_90th_or_add_an.py`](ch08_defend_this_salary/03_the_offer_check_fund_peers_at_the_90th_or_add_an.py) | Runs as is |

### Chapter 9: The Pay Gap

| Listing | File | Status |
|---|---|---|
| Two Controls, One Function *(Under the Hood)* | [`01_two_controls_one_function.py`](ch09_the_pay_gap/01_two_controls_one_function.py) | Excerpt (needs the chapter's pay table loaded as `df`) |
| The Reason Gate *(Under the Hood)* | [`02_the_reason_gate.py`](ch09_the_pay_gap/02_the_reason_gate.py) | Runs as is |
| Read the Form of the Pay Statement *(Under the Hood)* | [`03_read_the_form_of_the_pay_statement.py`](ch09_the_pay_gap/03_read_the_form_of_the_pay_statement.py) | Runs as is |

### Chapter 10: People Who Left

| Listing | File | Status |
|---|---|---|
| Member-Level Match, Not a 2% Total Check | [`01_member_level_match_not_a_2_total_check.sql`](ch10_people_who_left/01_member_level_match_not_a_2_total_check.sql) | Data |
| Banded Identity Matching *(Under the Hood)* | [`02_banded_identity_matching.py`](ch10_people_who_left/02_banded_identity_matching.py) | Runs as is |
| Enrolment Check for the New Band *(Under the Hood)* | [`03_enrolment_check_for_the_new_band.sql`](ch10_people_who_left/03_enrolment_check_for_the_new_band.sql) | Data |

### Chapter 11: Wrong Pay

| Listing | File | Status |
|---|---|---|
| The Rule That Recomputes Every Line | [`01_the_rule_that_recomputes_every_line.py`](ch11_wrong_pay/01_the_rule_that_recomputes_every_line.py) | Runs as is |
| Recompute Every Line, Route Every Unknown *(Under the Hood)* | [`02_recompute_every_line_route_every_unknown.py`](ch11_wrong_pay/02_recompute_every_line_route_every_unknown.py) | Runs as is |
| The Note Guard: No Digit Without a Slot *(Under the Hood)* | [`03_the_note_guard_no_digit_without_a_slot.py`](ch11_wrong_pay/03_the_note_guard_no_digit_without_a_slot.py) | Runs as is |
| Queue Item, Code to Person *(Under the Hood)* | [`04_queue_item_code_to_person.json`](ch11_wrong_pay/04_queue_item_code_to_person.json) | Data |
| Decision, Person to Code *(Under the Hood)* | [`05_decision_person_to_code.json`](ch11_wrong_pay/05_decision_person_to_code.json) | Data |

### Chapter 12: Year Two

| Listing | File | Status |
|---|---|---|
| The Guardrail That Blocks a Figure the Code Did Not Produce | [`01_the_guardrail_that_blocks_a_figure_the_code_did.diff`](ch12_year_two/01_the_guardrail_that_blocks_a_figure_the_code_did.diff) | Data (a before/after rule change, shown as a diff) |
| Mask Personal Data Before Any Model Call | [`02_mask_personal_data_before_any_model_call.py`](ch12_year_two/02_mask_personal_data_before_any_model_call.py) | Runs as is |
| Registry Entry: Payroll Pre-Check *(Under the Hood)* | [`03_registry_entry_payroll_pre_check.yaml`](ch12_year_two/03_registry_entry_payroll_pre_check.yaml) | Data |
| Stale Rules Fail in the Open *(Under the Hood)* | [`04_stale_rules_fail_in_the_open.py`](ch12_year_two/04_stale_rules_fail_in_the_open.py) | Runs as is |
| One Wrapper, Six Guards *(Under the Hood)* | [`05_one_wrapper_six_guards.py`](ch12_year_two/05_one_wrapper_six_guards.py) | Runs as is |
| The Exit Drill *(Under the Hood)* | [`06_the_exit_drill.py`](ch12_year_two/06_the_exit_drill.py) | Runs as is |

### Chapter 13: Still Checking

| Listing | File | Status |
|---|---|---|
| The Stop Rule as a Test | [`01_the_stop_rule_as_a_test.py`](ch13_still_checking/01_the_stop_rule_as_a_test.py) | Runs as is |
| Plant, Then Measure With an Honest Interval *(Under the Hood)* | [`02_plant_then_measure_with_an_honest_interval.py`](ch13_still_checking/02_plant_then_measure_with_an_honest_interval.py) | Runs as is |

### Chapter 14: The Audit

| Listing | File | Status |
|---|---|---|
| Floors in Code, Duties to a Person *(Under the Hood)* | [`01_floors_in_code_duties_to_a_person.py`](ch14_the_audit/01_floors_in_code_duties_to_a_person.py) | Runs as is |
| What Gap Could This Audit Have Found? *(Under the Hood)* | [`02_what_gap_could_this_audit_have_found.py`](ch14_the_audit/02_what_gap_could_this_audit_have_found.py) | Runs as is |

### Chapter 15: Month Six

| Listing | File | Status |
|---|---|---|
| A Stop Rule Is Data, Not a Sentence *(Under the Hood)* | [`01_a_stop_rule_is_data_not_a_sentence.py`](ch15_month_six/01_a_stop_rule_is_data_not_a_sentence.py) | Runs as is |
| The Board Page Builder *(Under the Hood)* | [`02_the_board_page_builder.py`](ch15_month_six/02_the_board_page_builder.py) | Runs as is |

## What is not here

The rule packs, data provenance notes, assumption tables and the fourteen anonymised field interviews referred to in the book are published separately with the companion volume.

## Licence

Code in this folder is under the repository's [MIT License](../LICENSE). The text of the book is not licensed: © 2026 Rajesh Ranjan Mahapatra & Abhishek Agrawal, all rights reserved.

## Contact

- Rajesh Ranjan Mahapatra: [rajeshrmahapatra.com](https://rajeshrmahapatra.com), [LinkedIn](https://www.linkedin.com/in/rajeshranjanmahapatra/), mahapatra.rajeshranjan@gmail.com
- Abhishek Agrawal: [LinkedIn](https://www.linkedin.com/in/abhishek-xlhr2018), abhishek.agrawal2013@gmail.com
