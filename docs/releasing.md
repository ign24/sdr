# Releasing

## Current policy

CI builds and audits wheel and source distributions, then retains them only as a
short-lived GitHub Actions artifact. The repository does not publish to PyPI and
does not store or consume a PyPI API token.

## Future Trusted Publishing

PyPI Trusted Publishing through GitHub Actions OIDC is the intended future
release mechanism. It is not enabled. Enabling it requires all of the following
in a separately reviewed OpenSpec change:

1. Create the real PyPI project and configure its trusted publisher for the
   exact repository, release workflow filename, and protected environment.
2. Add a release-only workflow with an explicit version tag trigger, GitHub
   environment approval, `contents: read`, and job-scoped `id-token: write`.
3. Download the already validated distributions by digest and publish with the
   official PyPA action pinned to a reviewed full commit SHA.
4. Keep pull-request workflows secretless and read-only; never add a PyPI token.
5. Record provenance, package index response, and the approved release version.

No operational publish workflow or placeholder token is included until those
preconditions exist.
