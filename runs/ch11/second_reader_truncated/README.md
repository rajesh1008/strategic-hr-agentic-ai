# Superseded: second-reader runs on truncated facts

These three runs (claude-haiku-5-5, commit dc6403c) read Line v1.0 before
commit e25e0e1 quoted its facts lines. Nine rows (A04, A05, A07, B02, C06,
D03, E01, E04, H02) were stored as unquoted YAML flow mappings with a comma
in their facts, so the model was shown each of those facts only up to the
first comma. Chapter 11 quotes the reruns in `runs/ch11/second_reader/`
(172304Z, 172306Z, 172308Z). These records are kept as the evidence for the
fault Chapter 32 describes; no chapter quotes their output.
