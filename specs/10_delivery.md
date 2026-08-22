---
status: draft
updated: 2026-08-20
---

# Delivery and operation

How the software reaches its users and how it is kept running. These decisions are expensive to change
late, because installers, update paths and data locations end up on machines the vendor cannot reach.

### XC-050 - Distribution
- form: a signed desktop installer per platform, containing the Electron shell and a pinned Python
  engine with VTK
- target platforms: Windows 10 22H2 and 11 on x64 as the first release; macOS on Apple silicon and
  Linux x64 follow, in that order
- size expectation: several hundred megabytes. The VTK Python wheel alone is 80.4 MB on Windows and
  the Electron runtime 143.2 MB, and ParaView's own Windows installer is 495.5 MB - a comparable
  product built the same way
- installer: writes the application and the engine environment; user data lives in the platform's
  per-user location and is never placed beside the executable
- decidedness: Fixed
- basis: E-021 (T1), E-024 (T1)

### XC-051 - Code signing
- statement: Windows builds are signed with a certificate valid for public trust, and macOS builds are
  signed and notarised
- rationale: Microsoft documents that unsigned applications raise the SmartScreen warning and that
  Smart App Control blocks unknown unsigned applications outright. Shipping unsigned is not a saving,
  it is an installation failure for the customers who matter most
- decidedness: Fixed
- basis: E-022 (T1), E-023 (T1)

The cheapest route is not open to this vendor, and that is worth stating plainly:

| Route | Cost | Availability |
|---|---|---|
| Azure Artifact Signing | USD 9.99 per month | individuals only in the United States and Canada; organisations in a list that includes Japan |
| SSL.com individual validation + eSigner | USD 129 per year + from USD 180 per year | available to an individual in Japan |
| Apple Developer Program | USD 99 per year | required for macOS signing and notarisation |

**An individual developer in Japan cannot use the Microsoft route** - it requires either incorporating
or the individual-validation path above. XC-036 takes the individual path: signing is not a reason to
incorporate before there is a customer who requires it. Extended validation is not needed: Microsoft states that EV
certificates no longer bypass SmartScreen.

Reputation is separate from signing: Microsoft describes it accruing over several weeks and hundreds
of clean installations. **The first release will show a warning to some users no matter what is paid**,
so the download page has to explain it rather than pretend it will not happen.

### XC-052 - Update and rollback
- statement: updates are checked on request, not silently; the user sees what changed and can decline;
  the previous version stays installable and a downgrade never rewrites a @Workspace to an older format
- rationale: an engineer producing two figures for one report cannot have the rendering path change
  between them (XC-024). And a rollback that loses the workspace is not a rollback
- decidedness: Fixed
- basis: E-001 (T1)

### XC-053 - Environments
- statement: the desktop product has one environment - the user's machine. The later hosted service
  has development, staging and production, and no customer data crosses between them
- configuration: settings live in a per-user file; secrets, when the user configures a model provider,
  go to the operating system's credential store, never to a plain file
- decidedness: Fixed
- basis: E-001 (T1)

### XC-053b - What an installation carries besides the program
- statement: an installation ships the **sample workspace** with data this project generated (XC-129),
  the **sample library** of templates, materials, fonts and colour maps (XC-108), and the **licence
  inventory** for every one of them - an asset whose terms do not permit redistribution ships as a
  placeholder rather than as itself (XC-085). The inventory is checked at build time, not at review time
- rationale: the sample content is the first thing a user sees and the easiest thing to acquire an
  unclear licence for, because it arrives one asset at a time from different places
- decidedness: Fixed
- basis: E-062 (T1)

### XC-054 - Monitoring
- statement: the desktop product monitors nothing remotely. It writes a local log the user can read
  and attach to a support request; nothing is sent unless the user attaches it
- rationale: this is the same commitment as XC-026 and XC-027, and it is the one a corporate network
  team verifies rather than believes
- decidedness: Fixed
- basis: E-001 (T1)

### XC-055 - Backup and restore
- statement: a @Workspace is a single file the user can copy; the product keeps the previous good
  version beside it on save and never overwrites the only copy
- restore procedure: opening the previous version is a file operation the user can perform without the
  product
- last exercised: not yet - to be exercised before the first release, and the date recorded here
- decidedness: Fixed
- basis: E-001 (T1)

A restore that has never been tried is a hypothesis. This line exists to be filled in with a date.

### XC-055b - Diagnosis without exfiltration
- statement: logs are local and carry no field values; a **support bundle** lists everything it contains
  before it is created and leaves the machine only with explicit consent, through the egress module and
  into its audit (XC-126)
- rationale: the alternative - automatic crash reporting - produces better diagnostics and sends a
  customer's part names to a third party without anybody deciding to
- decidedness: Fixed
- basis: E-001 (T1)

### XC-056 - Support and vulnerability response
- statement: a published contact route, an inventory of dependencies with their versions (XC-025), and
  a check for known advisories on each release
- rationale: a single-person vendor cannot promise a response time it cannot meet. What it can promise
  - and what a buyer can verify - is that the inventory exists, the check runs, and the route works
- decidedness: Bounded
