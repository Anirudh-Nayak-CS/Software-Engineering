from pathlib import Path

from models.documents import Document


SAMPLE_DOCUMENTS = {
    "appointment_scheduling_requirements.md": """
Healthcare appointment scheduling requirements:
- Patients shall view available appointment slots and book, reschedule, or cancel appointments.
- The system shall prevent double booking and notify affected users when an appointment changes.
- Providers shall view schedules and receive alerts about conflicts.
- Appointment reminders shall be sent through configured communication channels.
- The system shall record appointment changes for operational review.
""",
    "patient_portal_security_requirements.md": """
Healthcare patient portal requirements:
- Patients shall access only their own health information.
- Staff access shall be based on an assigned role and least privilege.
- Sensitive health information shall be protected in transit and at rest.
- The system shall maintain an audit record for access to and changes in patient data.
- Privacy, retention, and disclosure rules must be confirmed with the responsible compliance officer.
""",
}


SUPPORTED_EXTENSIONS = {".pdf", ".md", ".txt"}


def load_requirement_documents(directory: Path) -> list[Document]:
    """Load supported requirement documents while preserving source metadata."""
    documents: list[Document] = []

    if directory.exists():
        for path in sorted(directory.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            doc_type = path.parent.name

            if path.suffix.lower() == ".pdf":
                documents.extend(_load_pdf(path, doc_type))
            else:
                text = path.read_text(encoding="utf-8").strip()
                if text:
                    documents.append(
                        Document(
                            name=path.name,
                            doc_type=doc_type,
                            source=str(path),
                            text=text,
                            page=1,
                        )
                    )

    if documents:
        return documents

    return [
        Document(
            name=name,
            doc_type="sample",
            source=name,
            text=text.strip(),
            page=1,
        )
        for name, text in SAMPLE_DOCUMENTS.items()
    ]


def _load_pdf(path: Path, doc_type: str) -> list[Document]:
    import fitz

    documents: list[Document] = []
    with fitz.open(path) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text().strip()
            if text:
                documents.append(
                    Document(
                        name=path.name,
                        doc_type=doc_type,
                        source=str(path),
                        text=text,
                        page=page_number,
                    )
                )
    return documents
