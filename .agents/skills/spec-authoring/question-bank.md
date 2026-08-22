# Question bank

Every question below is asked. Every question offers the same two escapes:

- **Undecided / I don't know** - recorded as `OPEN-NNN`, researched, and brought back as a proposal to confirm.
- **No preference, you decide** - decided by the agent against the product principles, with one line of
  rationale, and not raised again.

Ask in stage order. Within a stage, ask the questions that constrain other answers first.

## S0 Framing

1. Execution capacity: hours per week, and how many people. (Fixes which customer-acquisition models are possible at all.)
2. Target market: domestic, English-speaking global, or domestic first then export.
3. Domain leverage: does existing expertise count as a barrier to entry here, or is the search unconstrained by it?
4. Definition of success: what revenue scale, by when. (Without this, ranking has no objective function.)
5. Capital available, and risk tolerance.
6. Conflict-of-interest constraints with current employment.
7. Existing assets that can be reused: code, data, relationships, distribution.
8. Review appetite: how many decisions to review in one batch.

## S1 Viability (skip for internal tools and contracted scope)

9. Who has this problem today, and what do they do about it now?
10. What do they pay for the current substitute - in money, time, or risk?
11. Which markets does this touch, from the broad category down to the specific segment?
12. Named competitors, and adjacent products that could absorb this as a feature.
13. Why would a buyer pay rather than tolerate the substitute? Is the improvement large enough to justify a purchase decision, or is it a preference?
14. What would make this fail? (Ask before the research, so the answer is not shaped by it.)
15. Which regulatory, licensing or certification constraints apply?

## S2 Product spec

16. Intended users: who they are, what they already know, what they are trying to achieve.
17. What is explicitly **out of scope**?
18. Product principles: when correctness, speed, cost and simplicity conflict, what wins - in order?
19. Terms that mean something specific here, and what each does *not* mean.
20. Units, and the naming convention that carries them.
21. Coordinate frames, origins, axis directions and sign conventions, if the product has geometry.
22. What data crosses a boundary (stored, sent, received), and who reads it at the other end?
23. For each of those: are unknown fields rejected, ignored or preserved? What may an old reader assume?
24. What must always be true - values with one source of truth, concepts with one entry point?
25. On failure: raise, return a missing-value marker, or continue with a default? What does the user see?
26. May a partial result be returned, and how is it marked?
27. Capacity limits: maximum counts, sizes, ranges, rates - and what happens at the limit.
28. For each requirement: priority (MUST / SHOULD / COULD) and phase (first release or later).
29. For each acceptance criterion: how is it verified, with what data, to what tolerance?
30. Where does the verification data come from?

## S3 Technical

31. Which existing system could be reused instead of building this?
32. Module split (capabilities) and layer split (dependency direction).
33. Language, framework, data store, build and packaging toolchain.
34. For each dependency: how broadly is it adopted in production, and what is its support horizon - release cadence, maintainer count, governance, LTS policy?
35. Licence of every dependency, and its compatibility with how this will be distributed.
36. Target operating systems and versions.
37. Installer and update mechanism, and how a bad release is rolled back.
38. Deployment: environments, and what is monitored.
39. Screens, navigation and state transitions, including empty and error states.
40. Shared components, named now so the same concept does not gain a second implementation later.
41. Message and error catalogue: where it lives, and how IDs are assigned.
42. Localisation: which locales, and what happens to an untranslated string.
43. Accessibility: standard and level.
44. Audit and operation logging: what, where, how long, who may read it.
45. Security: authentication, authorisation, retention, personal data, secrets handling.
46. External systems: interface, exact version targeted, and the response required for each failure mode - timeout, disconnect, partial response, out-of-range value, unexpected version.
47. Development environment: pinned tool versions, how to build, run and test, required environment variables.

## S3b Operations and change (asked with S3)

48. Which files hold values the spec must own? (These become `source_of_truth` targets, and check 7 keeps them honest.)
49. What is monitored in production, what alerts, and who receives the alert?
50. How is data written by an older version upgraded, who runs the upgrade, and what happens to a record that fails to upgrade?
51. Rate limits and quotas: the ones this system imposes, and the ones upstream services impose on it.
52. Backup and restore: what is backed up, how often, and when was a restore last exercised?
53. Who may change a Fixed value after release, and how is that change reviewed?

## S4 Gate

54. Anything answered "undecided" that is still open - is it now decided, or does it become a tracked Open in the spec?

An Open that survives to the end is not a failure; an Open with no tracking ID is.
