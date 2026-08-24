"""Whether two runs of the same pipeline did the same thing, answered rather than assumed.

AC-016 asks that a second run on the same inputs produce artefacts identical to the first, **save for
recorded timestamps**. That exception is the whole difficulty: everything else has to be identical, and
"identical" needs a form to compare and a name for the first place two runs part company.

XC-012 is the principle underneath - reproducibility before convenience - and XC-046 is where it comes
from: reproducibility is a property of the recorded log, not of anything a model or a renderer produced.

Three things here, and the split matters.

**`canonical`** turns a run record into the form that gets compared: the timestamps removed, everything
else left in the order the run put it in. Nothing is sorted. Sorting would hide a real difference -
two runs that acted on the same cases in a different order are not the same run, and a comparison that
tidied that away would report agreement where there is none.

**`differences`** names where two runs part company, first difference first. A boolean answer to "were
these the same" is the least useful form of a correct answer: what somebody needs is the unit.

**`artefact_digests`** hashes files this layer did not write. The pipeline does not produce artefacts
itself - the caller performs a unit - so comparing outputs means being handed the paths.

Specification: pipeline/AC-016, AC-021, XC-012, XC-046, XC-142.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from service.pipeline.run import RunRecord

#: The fields of a run record that may legitimately differ between two identical runs. Written out,
#: because "anything that looks like a time" is a rule that would one day drop a field somebody needs.
VOLATILE_FIELDS = ("started", "finished")

#: How many bytes are read at once when hashing a file. Nothing subtle - it exists so a large artefact
#: is not loaded whole to be compared.
HASH_CHUNK_BYTES = 1 << 20


def canonical(record: RunRecord) -> dict[str, Any]:
    """The comparable form of a run record: everything except when it happened.

    Order is preserved throughout. A run that produced the same results in a different order is a
    different run, and a canonical form that sorted them would report two such runs as identical.
    """
    return {
        "pipelineId": record.pipeline_id,
        "pipelineRevision": record.pipeline_revision,
        "resolvedCases": list(record.resolved_cases),
        "results": [
            {
                "unit": result.unit_id,
                "case": result.case_id,
                "outcome": result.outcome.value,
                "targetSize": result.target_size,
                "detail": result.detail,
            }
            for result in record.results
        ],
        "produced": dict(record.produced),
        "stoppedAt": record.stopped_at,
        "written": list(record.written),
    }


def as_text(record: RunRecord) -> str:
    """The canonical form as one string, for a digest or for a diff a person reads."""
    return json.dumps(canonical(record), ensure_ascii=False, indent=2, sort_keys=False)


def digest(record: RunRecord) -> str:
    """A single value two runs can be compared by.

    Useful for saying *whether* two runs agree in one comparison; useless for saying *where* they do
    not, which is what `differences` is for.
    """
    return hashlib.sha256(as_text(record).encode("utf-8")).hexdigest()


def identical(first: RunRecord, second: RunRecord) -> bool:
    return digest(first) == digest(second)


def differences(first: RunRecord, second: RunRecord) -> tuple[str, ...]:
    """Where two runs part company, first difference first, as readable paths.

    Returns an empty tuple where they agree. A pair of records that differ in many places produces many
    lines on purpose: the first is usually the cause and the rest are usually its consequences, and
    hiding them would leave somebody guessing which is which.
    """
    return tuple(_walk("", canonical(first), canonical(second)))


def _walk(path: str, left: Any, right: Any) -> Iterable[str]:
    if type(left) is not type(right):
        yield f"{path or '(記録)'}：型が違います（{type(left).__name__} と {type(right).__name__}）"
        return
    if isinstance(left, dict):
        for key in dict.fromkeys([*left, *right]):
            here = f"{path}.{key}" if path else str(key)
            if key not in left:
                yield f"{here}：1 回目にありません"
            elif key not in right:
                yield f"{here}：2 回目にありません"
            else:
                yield from _walk(here, left[key], right[key])
        return
    if isinstance(left, list):
        if len(left) != len(right):
            yield f"{path or '(記録)'}：件数が {len(left)} と {len(right)} で違います"
        for index, (one, other) in enumerate(zip(left, right)):
            yield from _walk(f"{path}[{index}]", one, other)
        return
    if left != right:
        yield f"{path or '(記録)'}：{left!r} と {right!r}"


def file_digest(path: Path) -> str:
    """The sha256 of one file, read in chunks."""
    digest_ = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(HASH_CHUNK_BYTES):
            digest_.update(chunk)
    return digest_.hexdigest()


def artefact_digests(paths: Iterable[Path]) -> dict[str, str]:
    """What a run wrote, by name, so two runs' outputs can be compared (AC-016).

    Keyed by file name rather than by full path: two runs write into two directories, and a comparison
    keyed by absolute path would report every artefact as missing from the other side.
    """
    return {path.name: file_digest(path) for path in sorted(paths, key=lambda p: p.name)}


def artefact_differences(
    first: Mapping[str, str], second: Mapping[str, str]
) -> tuple[str, ...]:
    """Which artefacts differ between two runs, named."""
    found: list[str] = []
    for name in dict.fromkeys([*first, *second]):
        if name not in first:
            found.append(f"{name}：1 回目にありません")
        elif name not in second:
            found.append(f"{name}：2 回目にありません")
        elif first[name] != second[name]:
            found.append(f"{name}：内容が違います")
    return tuple(found)
