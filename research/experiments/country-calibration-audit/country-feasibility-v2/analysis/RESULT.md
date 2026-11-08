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

A subsequent read-only generation-metadata lookup reported the same charge and
native prompt/completion counts. It also reported different normalized token
counts and a dated model identifier in place of the requested alias; the
relationship between those fields is not established. Native reasoning still
exceeded native completion, and the lookup and saved response disagree on
upstream inference cost. The allowlisted metadata is preserved in
`provider-generation-metadata.json`; only a hash of the original lookup
response was retained, so its bytes cannot be independently rechecked here.
This lookup does not reopen the stopped stage or independently verify billing.

For diagnosis only, `failed-call-001-scoreblind.json` is a post-hoc projection
of the saved response's contract-valid text, with the numeric score field
omitted. It is outside the runner's semantic-input path, does not resolve the
failed usage check, and cannot authorize another call or validate a rating.
The explanation may still reveal numerical details or geography. Any review
of it must be reported as an analysis of a failed attempt, not as a completed
or representative result. The earlier v1 attempt also failed and its partial
reasoning had been visible to reviewers before v2 was designed.
