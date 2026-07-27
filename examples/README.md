# Synthetic Examples

These fixtures contain invented investigations, reserved-domain URLs, and deterministic local
inputs. They do not contain copied third-party snapshots or precomputed lifecycle metadata.

Run either complete example into a new temporary research root:

```bash
uv run python -m examples.runner light-complete --root /tmp/sdr-light
uv run python -m examples.runner full-complete --root /tmp/sdr-full
```

The runner copies source artifacts, creates `sdr.yaml` through the public model, runs every gate
offline, and leaves the source fixture unchanged. The full example explicitly executes a harmless
Python probe without a shell. `failing-gates/` contains deliberately invalid onboarding fixtures.
