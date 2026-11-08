# Stage-one result: stopped on the first call

This is a post-run research record, not travel advice or a validated rating.
The frozen protocol and receipt describe the pre-dispatch state and remain
unchanged as historical evidence.

The first scheduled v2 call returned HTTP 200 and `finish_reason: stop`, but
reported 1,119 completion tokens and 1,148 reasoning tokens. The predeclared
usage-consistency check therefore stopped the stage. Its terminal attempt and
provider response are preserved in `../runs/v2-stage1-call-001/`; the other
19 cells were not attempted. No runner-approved semantic sidecar, review or
rating exists, and this version cannot be resumed or retried.

The provider-reported charge for the failed call was $0.000628782. Together
with the four earlier probes and the failed v1 country call, exact recorded
charges total $0.002622058. These are provider-reported amounts, not an
independent billing reconciliation; the $10 limit was a local postpaid guard,
not a provider-enforced hard cap.

OpenRouter's [reasoning-token documentation](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens)
says that, for chat completions, subtracting
`completion_tokens_details.reasoning_tokens` from `completion_tokens` gives
the visible output token count. The reported values in this call cannot be
interpreted that way without a negative result. This supports describing an
inconsistent usage report; it does not establish the cause or prove the
provider-reported monetary charge was wrong.

For diagnosis only, `failed-call-001-scoreblind.json` is a post-hoc projection
of the saved response's contract-valid text, with the numeric score field
omitted. It is outside the runner's semantic-input path, does not resolve the
failed usage check, and cannot authorize another call or validate a rating.
The explanation may still reveal numerical details or geography. Any review
of it must be reported as an analysis of a failed attempt, not as a completed
or representative result. The earlier v1 attempt also failed and its partial
reasoning had been visible to reviewers before v2 was designed.
