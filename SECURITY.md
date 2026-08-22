# Security

## Reporting

Open a private advisory:
<https://github.com/take-works-tech/261SV/security/advisories/new>

Never open a public issue for a vulnerability, and **never attach a result file**. If a defect depends
on the contents of a customer's data, describe its shape instead — counts, field names, associations,
partition layout.

**A single-person vendor cannot promise a response time it cannot meet** (XC-029, XC-056). What is
promised, and what you can verify: an inventory of dependencies with their versions exists, a check for
known advisories runs on each release, and this route works.

## What this product's threat model actually is

Two things, and neither is the usual web-application list.

**Files are hostile input.** Users open result files sent to them by customers — the definition of
untrusted input. Parsing happens in the engine process with no network access and limited filesystem
reach (XC-047). Formats whose readers carry unfixed upstream advisories are disabled by default and
named in the release notes; four heap-overflow and use-after-free advisories at CVSS 7.5 affect the
glTF loader in the embedded library with no fixed version indicated, and waiting for upstream is not a
strategy. Imported MaterialX documents are data, never executable extensions: a URI, XInclude or
symlink that leaves the package is refused without being opened, and imported shader source is
preserved inert rather than compiled (EXT-010).

**Nothing leaves the machine unless the user says so.** No dataset, workspace or reference content is
sent anywhere unless a network feature is enabled for that workspace and the user confirms what would
be sent (XC-026). Permission checks deny by default. There is no telemetry unless it is turned on, and
when it is, the payload is visible before it is sent (XC-027). One background request to a vendor
endpoint, found by a customer's network team, ends the sale and the reference — so there is no
exception here to be traded for convenience. `MOD-014` is the only module that opens a connection,
which is what makes "what leaves this machine" a directory rather than a search.

## Dependency licences are a separate obligation

`LICENSE.md` covers this project's own source. It discharges nothing that the embedded libraries
require: the notices file is generated from the **actual build closure**, not by hand and not from a
dependency's own install tree (XC-025). Upstream practice is not the model — the official VTK wheel
ships its own copyright file alone, with none of the vendored libraries' notices, and NumPy's published
wheel declares four licences beyond the BSD-3-Clause a reader of its repository would expect.
