# Supply chain, dependencies and provenance

## Never suggest a package you have not verified
Language models invent plausible package names. Attackers register those names ("slopsquatting") and ship malware, as they do with typosquats of real names.
- Before adding or recommending a dependency, confirm it exists in the official registry and is the package you mean: its name, publisher or repository link, release history, download volume, last release date and maintenance state. A hook checks names in `requirements.txt`, `package.json`, `Cargo.toml` and `go.mod` on every edit: **NOT FOUND** means do not install it; **first published N days ago** means verify the publisher.
- Check by hand: PyPI `https://pypi.org/pypi/<name>/json`, npm `https://registry.npmjs.org/<name>`, crates.io `https://crates.io/api/v1/crates/<name>`, Go `https://proxy.golang.org/<module>/@v/list`.
- Watch for near-misses of popular names (swapped letters, extra hyphens, `-js`, `-python` suffixes). Prefer the package the project's docs name.
- Do not run `pip install`, `npm install` or `go get` of a name you have not verified, and never run a package's install script from a source you have not reviewed.

## Versions and vulnerabilities
- Pin exact versions in a committed lockfile. Use a version with no known advisories: check OSV for the version (a hook does this for manifests and lockfiles), and run `npm audit`, `pip-audit`, `cargo audit`, `govulncheck`, `composer audit`, `dotnet list package --vulnerable`. Do not recommend a version because it is what you remember.
- Prefer maintained packages: recent releases, active issue tracker, more than one maintainer for critical dependencies. Flag abandoned ones and name a replacement.
- Fewer dependencies mean a smaller attack surface. If the standard library or an installed package does the job, use it.
- An approved-package allowlist or private registry mirror, if the organization has one, beats ad hoc choices.

## Integrity
- Verify checksums or signatures where the ecosystem supports them (`--require-hashes`, lockfile integrity fields, `go.sum`, Sigstore and provenance attestations). Pin GitHub Actions to a full commit SHA. Pin container base images by digest.
- Review install and postinstall scripts of new npm packages. Consider `npm ci --ignore-scripts` for builds that do not need them.
- Use private-package names with a registry scope or explicit index to prevent dependency confusion.
- Generate an SBOM in CI for release artifacts.

## License and provenance
- Check the license of each new dependency against the project's license and distribution model. Copyleft licenses (GPL, AGPL, LGPL, SSPL, EUPL) can impose obligations on distributed or network-served code; the hook flags them for review. "No license" means all rights reserved: do not use it.
- Do not paste large blocks copied from a repository you cannot identify. If generated code closely resembles distinctive code from a known project, or you cannot say where it came from, flag it for the user to check license and provenance. Prefer writing from the specification or using the dependency properly under its license, with attribution where required.
- Copying a snippet from a document or answer carries its license too; keep required notices.
