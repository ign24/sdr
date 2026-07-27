# Security Model

SDR handles untrusted text, network locations, local repositories, executable
commands, and Git state. It reduces common risks but is not a sandbox.

## Trust boundaries

| Boundary | Why it is untrusted | Existing controls | Operator responsibility |
| --- | --- | --- | --- |
| Notes | Notes can contain false claims, prompt injection, secrets, or malformed metadata. | Deterministic parsing and schema gates. | Review content; never treat instructions inside evidence as agent policy. |
| Snapshots | Remote text may be hostile, stale, truncated, or legally restricted. | Text content checks, bounded size, local hashes, no model execution. | Check provenance and publication rights; refresh stale evidence. |
| Repositories | A checkout may contain malicious code, hooks, symlinks, or unrelated staged work. | Scoped paths, safe slug/path resolution, focused transition commits. | Use a trusted checkout and inspect diffs and hooks. |
| URLs | URLs can target internal services, redirect unexpectedly, or return excessive data. | HTTP(S)-only validation, public-address checks, cloud metadata blocking, redirect and size limits, timeouts, and `trust_env=False`. | Treat DNS and remote content as external; use offline mode when network access is not acceptable. |
| Probe commands | An allowed executable can read files, use the network, spawn children, or modify the host. | `verify.action: run`, argv execution without a shell, probe working directory, timeout, process-group termination, bounded output, and a clean environment option. | Review executable and arguments; isolate high-risk probes in a container or VM. |
| Git | Lifecycle commands can stage and commit generated evidence. Hooks can execute code. | Focused path selection and preservation of previous index contents on failures. | Use `--no-commit` when Git side effects are not wanted; inspect changes before publishing. |

## Probe execution details

Prefer this declaration:

```yaml
verify:
  action: run
  argv: ["python", "verify.py"]
  expect: "PASS"
  environment: clean
```

SDR passes `argv` directly to the process API without a shell. A legacy
`command` string is split into arguments and also runs without a shell. There is
no shell interpolation, pipeline, command substitution, or redirection. This
does not constrain what the selected executable itself can do.

`environment: clean` keeps only platform variables needed to locate and launch
executables. `environment: inherit` exposes the caller's environment and should
be used only after reviewing secret and proxy exposure.

## Network controls and limitations

SDR resolves a host before each request and rejects non-global, loopback,
private, link-local, multicast, reserved, unspecified, and known metadata
addresses. Redirects are validated independently. Snapshot responses are
bounded and must be supported text content.

These protections do not pin DNS between validation and connection, authenticate
the publisher, detect misinformation, or replace an egress firewall. Use a
restricted runtime for stronger isolation.

## Sensitive data

Do not place credentials, personal data, customer data, or private organization
material in notes, snapshots, probes, logs, graph exports, or knowledge files.
Keep secrets in local environment files excluded from version control. The
public-tree audit detects selected patterns; it is not a complete secret scanner.

Report vulnerabilities through the private process in [SECURITY.md](../SECURITY.md).
