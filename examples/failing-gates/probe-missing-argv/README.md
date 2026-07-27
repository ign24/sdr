# Missing Probe Argument Vector

Single defect: the probe declares `verify.action` and `verify.expect` but omits both `verify.argv`
and the legacy `verify.command`. Criteria and reproduction content are otherwise complete, so only
`benchmark_reproducible` should fail.
