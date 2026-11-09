
import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from docx import Document
from pypdf import PdfReader
from docx.table import Table
from docx.text.paragraph import Paragraph

REQUIRED_FIELDS = {
    "source_id",
    "title",
    "document_type",
    "version",
    "effective_date",
    "access_label",
    "status",
    "relative_path",
}
ALLOWED_EXTENSIONS = {".docx", ".pdf", ".txt"}
ALLOWED_ACCESS = {"Internal", "Restricted"}


def normalize_whitespace(value):
    return re.sub(r"\s+", " ", value).strip()


def slugify(value):
    return re.sub(
        r"[^a-z0-9]+", "-",
        value.lower()
    ).strip("-") or "section"


def sha256_file(path):
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(lambda: file.read(65536), b""):
            digest.update(block)

    return digest.hexdigest()



def extract_docx(path):
    document = Document(path)
    paragraphs = []

    # Read paragraphs and tables in their original order.
    for block in document.iter_inner_content():

        if isinstance(block, Paragraph):
            content = normalize_whitespace(block.text)

            if not content:
                continue

            style = block.style.name.lower()

            paragraphs.append({
                "text": content,
                "heading": style.startswith("heading")
            })

        elif isinstance(block, Table):
            for row in block.rows:
                cells = [
                    normalize_whitespace(cell.text)
                    for cell in row.cells
                ]

                if any(cells):
                    paragraphs.append({
                        "text": " | ".join(cells),
                        "heading": False
                    })

    return paragraphs


def extract_pdf(path):
    reader = PdfReader(path)
    paragraphs = []

    for page_number, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""

        for line in text.splitlines():
            content = normalize_whitespace(line)

            if content:
                paragraphs.append({
                    "text": content,
                    "heading": bool(
                        re.match(r"^\d+(\.\d+)*\s+\S", content)
                    ),
                    "page": page_number
                })

    return paragraphs


def extract_txt(path):
    paragraphs = []

    for line in path.read_text(
        encoding="utf-8-sig"
    ).splitlines():
        content = normalize_whitespace(line)

        if content:
            paragraphs.append({
                "text": content,
                "heading": content.startswith("#")
            })

    return paragraphs


def extract_text(path):
    extension = path.suffix.lower()

    if extension == ".docx":
        return extract_docx(path)

    if extension == ".pdf":
        return extract_pdf(path)

    if extension == ".txt":
        return extract_txt(path)

    raise ValueError(f"Unsupported extension: {extension}")


def extract_sections(paragraphs):
    sections = []
    heading = "Overview"
    content = []

    def save_section():
        if content:
            sections.append({
                "section_name": heading,
                "sequence_number": len(sections) + 1,
                "chunk_text": "\n".join(content)
            })

    for paragraph in paragraphs:
        text = paragraph["text"]

        if paragraph["heading"]:
            save_section()
            heading = text.lstrip("#").strip()
            content = []
        else:
            content.append(text)

    save_section()

    return sections


class IngestionService:

    def __init__(self, supporting_documents, manifest, output_dir):
        self.root = Path(supporting_documents).resolve()
        self.manifest = Path(manifest).resolve()
        self.output_dir = Path(output_dir).resolve()

        self.accepted = []
        self.rejected = []
        self.warnings = []
        self.records = []

    def reject(self, filename, reason):
        self.rejected.append({
            "filename": filename,
            "reason": reason
        })

    def load_manifest(self):
        if not self.manifest.is_file():
            raise FileNotFoundError(
                f"Manifest not found: {self.manifest}"
            )

        with self.manifest.open(
            newline="", encoding="utf-8-sig"
        ) as file:
            reader = csv.DictReader(file)

            headers = set(reader.fieldnames or [])
            missing = REQUIRED_FIELDS - headers

            if missing:
                raise ValueError(
                    f"Missing manifest headers: {sorted(missing)}"
                )

            return list(reader)


    def run(self):
        rows = self.load_manifest()

        ids = Counter(
            (row.get("source_id") or "").strip()
            for row in rows
            if row.get("source_id")
        )

        paths = Counter(
            (row.get("relative_path") or "").strip().replace("\\", "/").casefold()
            for row in rows
            if row.get("relative_path")
        )

        listed_files = set(paths)

        # Scan source folders for unlisted files.
        source_folders = {
            "01_Current_Approved_Policies",
            "02_Operational_Playbooks",
            "03_Knowledge_Articles_and_FAQ",
            "04_Bulletins_and_Versioning",
        }

        for folder_name in source_folders:
            folder = self.root / folder_name

            if not folder.is_dir():
                self.warnings.append({
                    "filename": folder_name,
                    "reason": "Source folder not found"
                })
                continue

            for path in sorted(folder.rglob("*")):
                if not path.is_file():
                    continue

                relative = path.relative_to(self.root).as_posix()

                if relative.casefold() not in listed_files:
                    self.reject(relative, "Unlisted file")

        for row in rows:
            relative_path = (
                row.get("relative_path") or ""
            ).strip().replace("\\", "/")

            source_id = (row.get("source_id") or "").strip()

            missing = [
                field for field in REQUIRED_FIELDS
                if not (row.get(field) or "").strip()
            ]

            if missing:
                self.reject(
                    relative_path or "<missing>",
                    f"Missing fields: {sorted(missing)}"
                )
                continue

            if ids[source_id] > 1:
                self.reject(relative_path, "Duplicate source_id")
                continue

            if paths[relative_path.casefold()] > 1:
                self.reject(relative_path, "Duplicate relative_path")
                continue

            relative = Path(relative_path)

            if relative.is_absolute() or ".." in relative.parts:
                self.reject(relative_path, "Unsafe relative_path")
                continue

            path = (self.root / relative).resolve()

            if not path.is_relative_to(self.root):
                self.reject(relative_path, "Path outside Supporting Documents")
                continue

            if not path.is_file():
                self.reject(relative_path, "Missing source file")
                continue

            if path.suffix.lower() not in ALLOWED_EXTENSIONS:
                self.reject(relative_path, "Unsupported file type")
                continue

            access_label = row["access_label"].strip()

            if access_label not in ALLOWED_ACCESS:
                self.reject(relative_path, "Invalid access_label")
                continue

            approval_status = row["status"].strip()

            # Superseded documents must not enter the
            # current approved retrieval collection.
            if approval_status != "Approved":
                self.reject(
                    relative_path,
                    f"Not approved for current retrieval: {approval_status}"
                )
                continue

            try:
                datetime.strptime(
                    row["effective_date"].strip(),
                    "%Y-%m-%d"
                )

                paragraphs = extract_text(path)
                sections = extract_sections(paragraphs)

                if not sections:
                    raise ValueError("No extractable sections")

                checksum = sha256_file(path)

                metadata = {
                    "source_id": source_id,
                    "title": row["title"].strip(),
                    "document_type": row["document_type"].strip(),
                    "category": (row.get("category") or "").strip() or None,
                    "version": row["version"].strip(),
                    "effective_date": row["effective_date"].strip(),
                    "access_label": access_label,
                    "approval_status": approval_status,
                    "relative_path": relative_path,
                    "filename": path.name,
                    "checksum": checksum,
                }

                if metadata["category"] is None:
                    self.warnings.append({
                        "filename": relative_path,
                        "reason": "Category not supplied in manifest"
                    })

                for section in sections:
                    sequence = section["sequence_number"]

                    chunk_id = (
                        f"{source_id}-V{metadata['version']}"
                        f"-CHUNK-{sequence:04d}"
                    )

                    self.records.append({
                        **metadata,
                        **section,
                        "chunk_id": chunk_id
                    })

                self.accepted.append({
                    "filename": relative_path,
                    "source_id": source_id,
                    "checksum": checksum,
                    "section_count": len(sections)
                })

            except Exception as error:
                self.reject(relative_path, str(error))

        return self.write_outputs()

    def write_outputs(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)

        documents_path = self.output_dir / "documents.jsonl"
        log_path = self.output_dir / "ingestion_run_log.json"

        with documents_path.open("w", encoding="utf-8") as file:
            for record in self.records:
                file.write(
                    json.dumps(record, ensure_ascii=False) + "\n"
                )

        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "accepted_records": self.accepted,
            "rejected_records": self.rejected,
            "warnings": self.warnings,
            "counts": {
                "accepted": len(self.accepted),
                "rejected": len(self.rejected),
                "warnings": len(self.warnings),
                "sections": len(self.records)
            }
        }

        log_path.write_text(
            json.dumps(summary, indent=2),
            encoding="utf-8"
        )

        return summary


def build_argument_parser():
    parser = argparse.ArgumentParser(
        description="Policy RAG ingestion pipeline"
    )

    parser.add_argument(
        "--supporting-documents",
        required=True
    )

    parser.add_argument(
        "--manifest",
        default=None
    )

    parser.add_argument(
        "--output-dir",
        default="reports/ingestion"
    )

    return parser


def main():
    args = build_argument_parser().parse_args()

    root = Path(args.supporting_documents)

    manifest = (
        Path(args.manifest)
        if args.manifest
        else root / "05_Manifests_and_Guides" /
             "knowledge_base_manifest.csv"
    )

    service = IngestionService(
        supporting_documents=root,
        manifest=manifest,
        output_dir=args.output_dir
    )

    summary = service.run()

    print("Ingestion completed")
    print(json.dumps(summary["counts"], indent=2))


if __name__ == "__main__":
    main()
