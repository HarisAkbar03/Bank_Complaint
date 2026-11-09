
import csv
import json

from ingestion_service import IngestionService


FIELDS = [
    "source_id",
    "title",
    "document_type",
    "version",
    "effective_date",
    "access_label",
    "status",
    "relative_path",
]


def create_test_environment(tmp_path, rows, files):
    root = tmp_path / "Supporting Documents"

    policy_folder = root / "01_Current_Approved_Policies"
    manifest_folder = root / "05_Manifests_and_Guides"

    policy_folder.mkdir(parents=True)
    manifest_folder.mkdir(parents=True)

    for filename, content in files.items():
        (policy_folder / filename).write_text(
            content,
            encoding="utf-8"
        )

    manifest = manifest_folder / "knowledge_base_manifest.csv"

    with manifest.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    return root, manifest


def valid_row(filename="policy.txt", source_id="KB-001"):
    return {
        "source_id": source_id,
        "title": "Complaint Management Policy",
        "document_type": "Policy",
        "version": "3.0",
        "effective_date": "2026-01-01",
        "access_label": "Internal",
        "status": "Approved",
        "relative_path": (
            f"01_Current_Approved_Policies/{filename}"
        ),
    }


def run_ingestion(tmp_path, rows, files):
    root, manifest = create_test_environment(
        tmp_path, rows, files
    )

    service = IngestionService(
        supporting_documents=root,
        manifest=manifest,
        output_dir=tmp_path / "output"
    )

    return service.run()


def test_valid_document_accepted(tmp_path):
    result = run_ingestion(
        tmp_path,
        [valid_row()],
        {"policy.txt": "# Overview\nComplaint handling policy."}
    )

    assert result["counts"]["accepted"] == 1
    assert result["counts"]["rejected"] == 0
    assert result["counts"]["sections"] == 1


def test_missing_file_rejected(tmp_path):
    result = run_ingestion(
        tmp_path,
        [valid_row()],
        {}
    )

    assert result["counts"]["accepted"] == 0
    assert result["counts"]["rejected"] == 1


def test_unlisted_file_rejected(tmp_path):
    result = run_ingestion(
        tmp_path,
        [valid_row()],
        {
            "policy.txt": "# Overview\nApproved content.",
            "unknown.txt": "Unlisted document"
        }
    )

    assert result["counts"]["accepted"] == 1
    assert result["counts"]["rejected"] == 1
    assert result["rejected_records"][0]["reason"] == "Unlisted file"


def test_duplicate_source_id_rejected(tmp_path):
    result = run_ingestion(
        tmp_path,
        [
            valid_row("first.txt", "KB-001"),
            valid_row("second.txt", "KB-001")
        ],
        {
            "first.txt": "First policy",
            "second.txt": "Second policy"
        }
    )

    assert result["counts"]["accepted"] == 0
    assert result["counts"]["rejected"] == 2


def test_superseded_document_rejected(tmp_path):
    row = valid_row()
    row["status"] = "Superseded"

    result = run_ingestion(
        tmp_path,
        [row],
        {"policy.txt": "Old policy content"}
    )

    assert result["counts"]["accepted"] == 0
    assert result["counts"]["rejected"] == 1


def test_invalid_access_label_rejected(tmp_path):
    row = valid_row()
    row["access_label"] = "Unknown"

    result = run_ingestion(
        tmp_path,
        [row],
        {"policy.txt": "Policy content"}
    )

    assert result["counts"]["rejected"] == 1


def test_metadata_and_checksum(tmp_path):
    run_ingestion(
        tmp_path,
        [valid_row()],
        {"policy.txt": "# Overview\nComplaint handling policy."}
    )

    output = tmp_path / "output" / "documents.jsonl"

    record = json.loads(
        output.read_text(encoding="utf-8").splitlines()[0]
    )

    assert record["source_id"] == "KB-001"
    assert record["version"] == "3.0"
    assert record["approval_status"] == "Approved"
    assert record["access_label"] == "Internal"
    assert record["section_name"] == "Overview"
    assert len(record["checksum"]) == 64
    assert record["chunk_id"] == "KB-001-V3.0-CHUNK-0001"


def test_repeatable_ingestion(tmp_path):
    root, manifest = create_test_environment(
        tmp_path,
        [valid_row()],
        {"policy.txt": "# Overview\nComplaint handling policy."}
    )

    output = tmp_path / "output"

    first_service = IngestionService(root, manifest, output)
    first_service.run()

    first = (output / "documents.jsonl").read_bytes()

    second_service = IngestionService(root, manifest, output)
    second_service.run()

    second = (output / "documents.jsonl").read_bytes()

    assert first == second
