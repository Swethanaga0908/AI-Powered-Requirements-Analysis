from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import re
import json
import uuid


# ============================================================
# PATHS
# ============================================================

BASE = Path(__file__).resolve().parent.parent

FRONTEND = BASE / "frontend"
STATIC = FRONTEND / "static"
UPLOADS = BASE / "uploads"
REPORTS = BASE / "reports"

UPLOADS.mkdir(exist_ok=True)
REPORTS.mkdir(exist_ok=True)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="AI Requirement Gap Detector",
    version="2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


# Serve CSS and JavaScript
app.mount(
    "/static",
    StaticFiles(directory=STATIC),
    name="static"
)


# ============================================================
# REQUEST MODEL
# ============================================================

class AnalyzeRequest(BaseModel):
    title: str = "Untitled Project"
    requirements: str


# ============================================================
# SECTION HEADINGS
# ============================================================

SECTION_HEADINGS = {
    "functional requirements",
    "functional requirement",
    "technical requirements",
    "technical requirement",
    "non-functional requirements",
    "non functional requirements",
    "non-functional requirement",
    "non functional requirement",
    "optional requirements",
    "optional features",
    "optional advanced features",
    "advanced features",
    "system requirements",
    "software requirements",
    "business requirements",
    "functional",
    "technical",
    "non-functional",
    "optional"
}


# ============================================================
# REQUIREMENT PARSER
# ============================================================

def split_requirements(text: str):

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    items = []

    for line in lines:

        # Remove Markdown headings
        clean = re.sub(
            r"^#+\s*",
            "",
            line
        ).strip()

        # Remove bullets and numbering
        clean = re.sub(
            r"^(?:[-*•]|\d+[.)])\s*",
            "",
            clean
        ).strip()

        if not clean:
            continue

        normalized = clean.lower().rstrip(":")

        # Ignore section headings
        if normalized in SECTION_HEADINGS:
            continue

        # Ignore short category headings
        if clean.endswith(":") and len(clean.split()) <= 6:
            continue

        # Ignore very short text
        if len(clean) < 12:
            continue

        # Ignore technology-only/category-only lines
        technology_only_patterns = [
            r"^english[,/& ]+telugu",
            r"^gemini[,/& ]+openai",
            r"^whisper",
            r"^google[,/& ]+azure",
            r"^firebase[,/& ]+supabase",
            r"^vercel[,/& ]+render",
            r"^html[,/& ]+css[,/& ]+javascript",
            r"^react[,/& ]+",
        ]

        if any(
            re.search(
                pattern,
                clean.lower()
            )
            for pattern in technology_only_patterns
        ):
            continue

        items.append(clean)

    # Fallback for paragraph-style requirements
    if not items:

        sentences = re.split(
            r"(?<=[.!?])\s+",
            text
        )

        items = [
            sentence.strip()
            for sentence in sentences
            if len(sentence.strip()) >= 12
        ]

    return items


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def has_any(text, words):
    return any(word in text for word in words)


def is_actionable(text):

    action_words = [
        "shall",
        "must",
        "should",
        "can",
        "allow",
        "enable",
        "provide",
        "support",
        "detect",
        "capture",
        "analyze",
        "display",
        "store",
        "send",
        "create",
        "validate",
        "maintain",
        "generate",
        "translate",
        "convert",
        "record",
        "return",
        "handle",
        "adapt",
        "process",
        "restrict",
        "prevent",
        "authenticate",
        "authorize",
        "manage",
        "update",
        "remove",
        "search",
        "use",
        "include",
        "minimize",
        "protect",
        "switch",
        "recognize",
        "respond",
        "personalize",
        "deploy"
    ]

    return has_any(text, action_words)


def has_measurable_condition(text):

    measurable_words = [
        "within",
        "less than",
        "greater than",
        "at least",
        "maximum",
        "minimum",
        "%",
        "percent",
        "seconds",
        "second",
        "ms",
        "milliseconds",
        "accuracy",
        "response time",
        "latency",
        "limit",
        "threshold",
        "number of",
        "up to",
        "shall not exceed",
        "target",
        "rate",
        "capacity"
    ]

    return has_any(
        text,
        measurable_words
    )


# ============================================================
# ANALYSIS ENGINE
# ============================================================

def analyze(req: AnalyzeRequest):

    text = req.requirements.strip()

    if not text:

        raise HTTPException(
            status_code=400,
            detail="Requirements are empty"
        )

    items = split_requirements(text)

    if not items:

        raise HTTPException(
            status_code=400,
            detail="No valid requirements found"
        )


    # Result categories
    missing = []
    ambiguous = []
    incomplete = []
    conflicts = []
    edge_cases = []
    security = []
    acceptance = []
    improvements = []


    lower_text = text.lower()


    # ========================================================
    # AMBIGUOUS TERMS
    # ========================================================

    ambiguity_terms = [
        "fast",
        "quickly",
        "soon",
        "easy",
        "user-friendly",
        "simple",
        "appropriate",
        "reasonable",
        "large",
        "small",
        "good",
        "better",
        "efficient",
        "natural",
        "near real-time",
        "low latency",
        "high accuracy",
        "reasonably accurate"
    ]


    # ========================================================
    # ANALYZE EACH REQUIREMENT
    # ========================================================

    for index, item in enumerate(items, start=1):

        l = item.lower()


        # ----------------------------------------------------
        # AMBIGUITY
        # ----------------------------------------------------

        found_ambiguity = [
            word
            for word in ambiguity_terms
            if word in l
        ]

        if found_ambiguity:

            ambiguous.append({
                "id": index,
                "requirement": item,
                "reason": (
                    "Contains wording that may need a "
                    "measurable definition: "
                    + ", ".join(found_ambiguity)
                )
            })


        # ----------------------------------------------------
        # INCOMPLETE REQUIREMENT
        # ----------------------------------------------------

        if not is_actionable(l):

            incomplete.append({
                "id": index,
                "requirement": item,
                "reason": (
                    "The requirement does not clearly "
                    "describe an actionable system behavior."
                )
            })


        # ----------------------------------------------------
        # SECURITY / PRIVACY
        # ----------------------------------------------------

        security_sensitive = [
            "login",
            "password",
            "account",
            "authentication",
            "authorization",
            "personal data",
            "private data",
            "payment",
            "email",
            "admin",
            "role",
            "permission",
            "voice data",
            "conversation data",
            "user data"
        ]

        security_words = [
            "encrypt",
            "authentication",
            "authorization",
            "permission",
            "validate",
            "privacy",
            "secure",
            "access control",
            "retention",
            "delete",
            "protect"
        ]

        if has_any(
            l,
            security_sensitive
        ):

            if not has_any(
                l,
                security_words
            ):

                security.append({
                    "id": index,
                    "requirement": item,
                    "reason": (
                        "Security, privacy, authorization "
                        "or data-protection behavior is "
                        "not explicitly defined."
                    )
                })


        # ----------------------------------------------------
        # ACCEPTANCE / TESTABILITY
        # ----------------------------------------------------

        if not has_measurable_condition(l):

            acceptance.append({
                "id": index,
                "requirement": item,
                "reason": (
                    "No measurable acceptance condition "
                    "is explicitly specified."
                )
            })


        # ----------------------------------------------------
        # EDGE CASES
        # ----------------------------------------------------

        risk_sensitive = [
            "payment",
            "login",
            "password",
            "delete",
            "upload",
            "admin",
            "authentication",
            "voice",
            "conversation",
            "personal data",
            "database",
            "transaction"
        ]

        edge_words = [
            "if",
            "when",
            "unless",
            "error",
            "invalid",
            "failure",
            "offline",
            "timeout",
            "duplicate",
            "empty",
            "limit",
            "maximum",
            "minimum",
            "unavailable",
            "retry",
            "exception"
        ]

        # Only check edge cases for risk-sensitive operations.
        if has_any(
            l,
            risk_sensitive
        ):

            if not has_any(
                l,
                edge_words
            ):

                edge_cases.append({
                    "id": index,
                    "requirement": item,
                    "reason": (
                        "A risk-sensitive operation does "
                        "not explicitly define an error "
                        "or edge case."
                    )
                })


        # ----------------------------------------------------
        # IMPROVEMENT SUGGESTIONS
        # ----------------------------------------------------

        improved = item

        replacements = [

            (
                "quickly",
                "within a defined response-time target"
            ),

            (
                "fast",
                "within a defined response-time target"
            ),

            (
                "near real-time",
                "within a defined latency target"
            ),

            (
                "low latency",
                "with a defined maximum latency"
            ),

            (
                "reasonably accurate",
                "with a defined accuracy target"
            ),

            (
                "high accuracy",
                "with a defined accuracy target"
            ),

            (
                "user-friendly",
                "with clearly defined usability and accessibility criteria"
            ),

            (
                "simple",
                "with clearly defined usability criteria"
            )
        ]


        for old, new in replacements:

            improved = re.sub(
                re.escape(old),
                new,
                improved,
                flags=re.IGNORECASE
            )


        if improved != item:

            improvements.append({
                "id": index,
                "original": item,
                "suggestion": improved
            })


    # ========================================================
    # GLOBAL MISSING AREAS
    # ========================================================

    categories = [

        (
            "Actor",
            r"\b(user|admin|customer|manager|operator|system|assistant)\b"
        ),

        (
            "Inputs",
            r"\b(input|field|upload|request|data|speech|voice|text)\b"
        ),

        (
            "Outputs",
            r"\b(display|return|show|report|notification|response|output)\b"
        ),

        (
            "Error handling",
            r"\b(error|invalid|failure|timeout|exception|retry)\b"
        ),

        (
            "Data persistence",
            r"\b(store|save|database|record|persist|history)\b"
        )
    ]


    for name, pattern in categories:

        if not re.search(
            pattern,
            lower_text
        ):

            missing.append({
                "area": name,
                "reason": (
                    f"No clear requirement was found "
                    f"for {name.lower()}."
                )
            })


    # ========================================================
    # CONFLICT DETECTION
    # ========================================================

    for a in range(len(items)):

        for b in range(a + 1, len(items)):

            x = items[a].lower()
            y = items[b].lower()


            # Required vs optional conflict
            if (
                (
                    "must be required" in x
                    and "optional" in y
                )
                or
                (
                    "optional" in x
                    and "must be required" in y
                )
            ):

                conflicts.append({
                    "requirements": [
                        items[a],
                        items[b]
                    ],
                    "reason": (
                        "One requirement makes the behavior "
                        "mandatory while another makes it optional."
                    )
                })


            # Access scope conflict
            if (
                (
                    "only admin" in x
                    and "all users" in y
                )
                or
                (
                    "only admin" in y
                    and "all users" in x
                )
            ):

                conflicts.append({
                    "requirements": [
                        items[a],
                        items[b]
                    ],
                    "reason": (
                        "The access scope may be inconsistent."
                    )
                })


    # ========================================================
    # REALISTIC SCORING
    # ========================================================

    # Serious problems have stronger penalties.
    # Minor improvement points are capped so a large document
    # cannot automatically become 0%.

    conflict_points = min(
        len(conflicts) * 10,
        30
    )

    security_points = min(
        len(security) * 5,
        20
    )

    incomplete_points = min(
        len(incomplete) * 2,
        20
    )

    ambiguity_points = min(
        len(ambiguous) * 2,
        15
    )

    missing_points = min(
        len(missing) * 2,
        10
    )

    acceptance_points = min(
        len(acceptance),
        10
    )

    edge_points = min(
        len(edge_cases),
        5
    )


    risk_points = (
        conflict_points
        + security_points
        + incomplete_points
        + ambiguity_points
        + missing_points
        + acceptance_points
        + edge_points
    )


    score = max(
        0,
        min(
            100,
            round(100 - risk_points)
        )
    )


    # ========================================================
    # GRADE
    # ========================================================

    if score >= 80:

        grade = "Excellent"

    elif score >= 65:

        grade = "Good"

    elif score >= 50:

        grade = "Needs Improvement"

    else:

        grade = "High Risk"


    # ========================================================
    # QUESTIONS
    # ========================================================

    questions = []


    for item in ambiguous[:4]:

        questions.append(
            "Can this requirement be expressed with "
            "a measurable target: "
            f"'{item['requirement']}'?"
        )


    for item in security[:3]:

        questions.append(
            "What security or privacy rule should apply "
            f"to: '{item['requirement']}'?"
        )


    for item in incomplete[:3]:

        questions.append(
            "What exact system behavior is expected "
            f"for: '{item['requirement']}'?"
        )


    for item in acceptance[:2]:

        questions.append(
            "What measurable acceptance condition should "
            f"be used for: '{item['requirement']}'?"
        )


    questions = questions[:8]


    # ========================================================
    # FINAL RESULT
    # ========================================================

    return {

        "project": req.title,

        "score": score,

        "grade": grade,

        "requirement_count": len(items),

        "requirements": items,

        "missing": missing,

        "ambiguous": ambiguous,

        "incomplete": incomplete,

        "conflicts": conflicts,

        "edge_cases": edge_cases,

        "security_gaps": security,

        "acceptance_gaps": acceptance,

        "improvements": improvements,

        "questions": questions,

        "summary": {

            "missing": len(missing),

            "ambiguous": len(ambiguous),

            "incomplete": len(incomplete),

            "conflicts": len(conflicts),

            "edge_cases": len(edge_cases),

            "security": len(security),

            "acceptance": len(acceptance)
        }
    }


# ============================================================
# HOME PAGE
# ============================================================

@app.get("/")
def home():

    return FileResponse(
        FRONTEND / "index.html"
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "ok"
    }


# ============================================================
# ANALYZE API
# ============================================================

@app.post("/api/analyze")
def api_analyze(
    req: AnalyzeRequest
):

    return analyze(req)


# ============================================================
# FILE UPLOAD API
# ============================================================

@app.post("/api/upload")
async def upload(
    file: UploadFile = File(...)
):

    filename = file.filename or ""

    extension = Path(
        filename
    ).suffix.lower()


    allowed_extensions = {
        ".txt",
        ".pdf",
        ".docx"
    }


    if extension not in allowed_extensions:

        raise HTTPException(
            status_code=400,
            detail=(
                "Only TXT, PDF and DOCX files are supported."
            )
        )


    data = await file.read()


    saved_filename = (
        uuid.uuid4().hex
        + extension
    )


    path = UPLOADS / saved_filename

    path.write_bytes(data)


    extracted_text = ""


    # --------------------------------------------------------
    # TXT
    # --------------------------------------------------------

    if extension == ".txt":

        extracted_text = data.decode(
            "utf-8",
            errors="ignore"
        )


    # --------------------------------------------------------
    # PDF
    # --------------------------------------------------------

    elif extension == ".pdf":

        try:

            from pypdf import PdfReader

            reader = PdfReader(
                str(path)
            )

            extracted_text = "\n".join(
                page.extract_text() or ""
                for page in reader.pages
            )

        except Exception as error:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Could not read PDF: {error}"
                )
            )


    # --------------------------------------------------------
    # DOCX
    # --------------------------------------------------------

    elif extension == ".docx":

        try:

            from docx import Document

            document = Document(
                str(path)
            )

            extracted_text = "\n".join(
                paragraph.text
                for paragraph in document.paragraphs
            )

        except Exception as error:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Could not read DOCX: {error}"
                )
            )


    return {

        "filename": filename,

        "text": extracted_text
    }


# ============================================================
# REPORT API
# ============================================================

@app.post("/api/report")
def report(
    result: dict
):

    report_id = uuid.uuid4().hex[:10]

    filename = (
        f"requirement-report-{report_id}.json"
    )

    path = REPORTS / filename


    path.write_text(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )


    return {

        "id": report_id,

        "filename": filename
    }