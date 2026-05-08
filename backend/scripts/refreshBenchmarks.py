from __future__ import annotations

import hashlib
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT_DIR / "backend" / "datasets" / "public" / "upstreamBenchmarks.json"


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def _download(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read()


def refresh() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    fixtures = manifest.get("fixtures", [])
    failures: list[str] = []

    for fixture in fixtures:
        dataset_id = fixture["datasetId"]
        archive_payload = _download(fixture["sourceUrl"])
        with zipfile.ZipFile(io.BytesIO(archive_payload)) as archive:
            member = fixture["archiveMember"]
            if member not in archive.namelist():
                failures.append(f"{dataset_id}: missing archive member `{member}`")
                continue
            extracted = archive.read(member)

        actual_hash = _sha256(extracted)
        expected_hash = fixture["fixtureSha256"].upper()
        if actual_hash != expected_hash:
            failures.append(
                f"{dataset_id}: sha256 mismatch (expected {expected_hash}, got {actual_hash})",
            )
            continue

        destination = ROOT_DIR / fixture["localPath"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(extracted)
        print(f"refreshed {dataset_id} -> {destination}")

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        return 1

    print(f"refreshed {len(fixtures)} upstream public fixtures")
    return 0


if __name__ == "__main__":
    raise SystemExit(refresh())
