"""Read-only endpoints for legal cases stored in MongoDB."""
import re
import os
import re
import shutil
import tarfile
import tempfile

from pathlib import Path, PurePosixPath
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from fastapi.responses import FileResponse, RedirectResponse
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.deps import get_db

router = APIRouter(tags=["cases"])


CASE_FIELDS = {
    "_id": 0,
    "case_id": 1,
    "case_name": 1,
    "case_number": 1,
    "judgment_date": 1,
    "court_name": 1,
    "case_type": 1,
    "decision": 1,
    "location": 1,
    "court_level": 1,
    "cnr_number": 1,
    "neutral_citation": 1,
    "law_report_citation": 1,
    "source_pdf_s3_url": 1,
    "case_type_basis": 1,
    "bench_name": 1,
    "coram_members_text": 1,
    "judges": 1,
    "source_json_s3_url": 1,
}


@router.get("/cases")
def search_cases(
    q: Optional[str] = Query(default=None, max_length=200),
    limit: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db),
):
    """List recent cases or search by case name or number."""
    try:
        query = {}

        if q and q.strip():
            term = re.escape(q.strip())
            query = {
                "$or": [
                    {"case_name": {"$regex": term, "$options": "i"}},
                    {"case_number": {"$regex": term, "$options": "i"}},
                ]
            }

        rows = list(
            db["case_catalog"]
            .find(query, CASE_FIELDS)
            .sort([("judgment_date", -1), ("case_id", -1)])
            .limit(limit)
        )

        return {"count": len(rows), "cases": rows}

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve legal cases.",
        ) from exc


@router.get("/cases/{case_id}")
def get_case(case_id: int, db=Depends(get_db)):
    """Retrieve one case from the MongoDB case catalogue."""
    try:
        row = db["case_catalog"].find_one(
            {"case_id": case_id},
            CASE_FIELDS,
        )

        if row is None:
            raise HTTPException(status_code=404, detail="Case not found.")

        return row

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve the case.",
        ) from exc


PDF_SOURCE_HOSTS = {
    "indian-supreme-court-judgments.s3.amazonaws.com",
    "indian-supreme-court-judgments.s3.ap-south-1.amazonaws.com",
    "indian-high-court-judgments.s3.amazonaws.com",
    "indian-high-court-judgments.s3.ap-south-1.amazonaws.com",
}

PDF_CACHE = Path(tempfile.gettempdir()) / "legal-case-pdf-cache"


def _parse_pdf_source(raw_url):
    if not raw_url:
        return None

    parsed = urlsplit(raw_url)

    if (
        parsed.scheme != "https"
        or parsed.hostname not in PDF_SOURCE_HOSTS
    ):
        return None

    return parsed


def _member_name(parsed):
    member = parse_qs(parsed.fragment).get("member", [None])[0]

    if not member:
        if parsed.path.lower().endswith(".pdf"):
            member = PurePosixPath(parsed.path).name
        else:
            return None

    filename = PurePosixPath(member.replace("\\", "/")).name

    if not re.fullmatch(r"[A-Za-z0-9._-]+\.pdf", filename):
        return None

    return filename


def _archive_url(parsed):
    return urlunsplit((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.query,
        "",
    ))


def _individual_pdf_url(parsed, filename):
    if parsed.path.lower().endswith(".pdf"):
        return _archive_url(parsed)

    # Convert the archive folder into the individual-PDF folder.
    if "/data/tar/" not in parsed.path:
        return None

    pdf_path = parsed.path.replace("/data/tar/", "/data/pdf/", 1)
    folder = pdf_path.rsplit("/", 1)[0]
    pdf_path = f"{folder}/{quote(filename, safe='._-')}"

    return urlunsplit((
        parsed.scheme,
        parsed.netloc,
        pdf_path,
        "",
        "",
    ))


def _url_exists(url):
    try:
        request = Request(
            url,
            method="HEAD",
            headers={"User-Agent": "LegalCaseCitationAnalyzer/1.0"},
        )
        with urlopen(request, timeout=10) as response:
            return 200 <= response.status < 300
    except (HTTPError, URLError, TimeoutError, OSError):
        return False


def _is_pdf(path):
    try:
        with open(path, "rb") as file:
            return file.read(5) == b"%PDF-"
    except OSError:
        return False


def _extract_pdf_from_archive(archive_url, filename, case_id):
    PDF_CACHE.mkdir(parents=True, exist_ok=True)

    cached = PDF_CACHE / f"{case_id}-{filename}"

    if _is_pdf(cached):
        return cached

    request = Request(
        archive_url,
        headers={"User-Agent": "LegalCaseCitationAnalyzer/1.0"},
    )

    try:
        with urlopen(request, timeout=60) as remote:
            # Stream through the TAR; do not load the entire archive into RAM.
            with tarfile.open(fileobj=remote, mode="r|*") as archive:
                for member in archive:
                    if (
                        not member.isfile()
                        or PurePosixPath(member.name).name != filename
                    ):
                        continue

                    source = archive.extractfile(member)
                    if source is None:
                        break

                    fd, temporary = tempfile.mkstemp(
                        suffix=".pdf",
                        dir=str(PDF_CACHE),
                    )

                    try:
                        with os.fdopen(fd, "wb") as output, source:
                            shutil.copyfileobj(
                                source,
                                output,
                                length=1024 * 1024,
                            )

                        if not _is_pdf(temporary):
                            raise ValueError(
                                "The archive member is not a valid PDF."
                            )

                        os.replace(temporary, cached)
                        return cached

                    finally:
                        if os.path.exists(temporary):
                            os.unlink(temporary)

    except (HTTPError, URLError, TimeoutError, OSError, tarfile.TarError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Could not retrieve the judgment from its source archive.",
        ) from exc

    raise HTTPException(
        status_code=404,
        detail="The requested judgment was not found in its source archive.",
    )


@router.get("/cases/{case_id}/pdf")
def get_case_pdf(case_id: int, db=Depends(get_db)):
    row = db["case_catalog"].find_one(
        {"case_id": case_id},
        {
            "_id": 0,
            "pdf_url": 1,
            "source_pdf_s3_url": 1,
        },
    )

    if row is None:
        raise HTTPException(status_code=404, detail="Case not found.")

    archive_source = None
    filename = None

    # Prefer a real individual PDF; fall back to the TAR source.
    for raw_url in (
        row.get("pdf_url"),
        row.get("source_pdf_s3_url"),
    ):
        parsed = _parse_pdf_source(raw_url)
        if parsed is None:
            continue

        name = _member_name(parsed)
        if not name:
            continue

        
        individual_names = [name]

        if name.lower().endswith(".pdf"):
            english_name = f"{name[:-4]}_EN.pdf"
            if english_name.lower() != name.lower():
                individual_names.append(english_name)

        for individual_name in individual_names:
            individual_url = _individual_pdf_url(parsed, individual_name)

            if individual_url and _url_exists(individual_url):
                return RedirectResponse(
                    individual_url,
                    status_code=302,
                    headers={"Cache-Control": "public, max-age=3600"},
                )


        if "/data/tar/" in parsed.path and parsed.fragment:
            archive_source = _archive_url(parsed)
            filename = name
            break

    if not archive_source or not filename:
        raise HTTPException(
            status_code=404,
            detail="No supported PDF source is recorded for this case.",
        )

    pdf_path = _extract_pdf_from_archive(
        archive_source,
        filename,
        case_id,
    )

    return FileResponse(
        str(pdf_path),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Cache-Control": "public, max-age=3600",
        },
    )

@router.get("/landmark-cases")
def landmark_cases(
    limit: int = Query(default=5, ge=1, le=50),
    db=Depends(get_db),
):
    """Return most-cited cases from MongoDB citation statistics."""
    try:
        docs = list(
            db["case_window_stats"]
            .find(
                {"total_citations": {"$gt": 0}},
                {
                    "_id": 0,
                    "case_id": 1,
                    "case_name": 1,
                    "case_number": 1,
                    "judgment_date": 1,
                    "total_citations": 1,
                },
            )
            .sort([("total_citations", -1), ("case_id", 1)])
            .limit(limit)
        )

        results = []
        for doc in docs:
            date = doc.get("judgment_date")
            if hasattr(date, "isoformat"):
                date = date.isoformat()[:10]
            elif date:
                date = str(date)[:10]

            results.append({
                "case_id": doc["case_id"],
                "case_name": doc["case_name"],
                "case_number": doc.get("case_number"),
                "judgment_date": date or "",
                "citation_count": int(doc.get("total_citations", 0)),
            })

        return {"results": results}
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve landmark cases.",
        ) from exc

