from agents.project.gemini_client import client
from pydantic import BaseModel
from typing import List
from google.genai import types


class OtherFinding(BaseModel):
    category: str
    finding: str
    status: str
    simple_explanation: str


class OtherMedicalReport(BaseModel):
    document_type: str
    purpose: str | None
    findings: list[OtherFinding]
    important_results: list[str]
    impression: str | None
    overall_summary: str





def analyse(file, doc_type, level, language):

    prompt = f"""
You are a medical report simplification assistant.

The uploaded document is a medical document whose exact type is
not specifically supported by the application.

Explain the document in {language}.

The requested explanation level is: {level}

Your primary goal is to make the document understandable to an
ordinary person using extremely simple language.

IMPORTANT:
You are NOT a doctor and must NOT independently diagnose the patient.

Do not:
- invent information
- invent measurements
- invent diagnoses
- recommend medicines
- recommend treatment
- change the doctor's or medical professional's instructions
- assume that an abnormal finding automatically means a disease

First identify what kind of medical document it appears to be.

Then extract the important information.

1. DOCUMENT TYPE

Identify the type of medical document if it can be determined.

For example:
- Blood test
- Urine test
- Pathology report
- Biopsy report
- ECG report
- Echocardiogram
- Endoscopy report
- Medical certificate
- Specialist report
- Other

If the exact type cannot be determined, use "Unknown medical document".

2. PURPOSE

Explain why the document appears to have been created or
what examination/test it represents, if this can be determined.

If this information is not available, return null.

3. FINDINGS

Extract the important findings from the document.

For every finding:

- Identify the category or body part involved.
- State what the document actually says.
- Classify it as:
  "Normal", "Abnormal", or "Uncertain"
  based only on the document.
- Explain what it means in very simple language.

Do not make assumptions beyond what is written.

4. IMPORTANT RESULTS

List the important test results, observations, measurements,
or conclusions that a normal person should pay attention to.

Do not include unnecessary technical details.

5. IMPRESSION

If the document contains a doctor's, radiologist's, pathologist's,
or specialist's impression/conclusion, extract it.

Explain it in simple language without changing its meaning.

If there is no impression, return null.

6. OVERALL SUMMARY

Give a short, very simple explanation of the entire document.

Imagine explaining the document to someone who has never studied
medicine.

Use everyday language.

If a medical term is necessary, immediately explain what it means.

If something is not mentioned in the document, do not guess.

MOST IMPORTANTLY:

The goal is NOT to sound medically sophisticated.

The goal is:

"What does this document actually say, and what does that mean
in simple everyday language?"

Prioritize accuracy over adding information.
"""

    mime_type = file.type or "application/pdf"
    file_part = types.Part.from_bytes(
        data=file.getvalue(),
        mime_type=mime_type
    )

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=[
            prompt,
            file_part
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": OtherMedicalReport        }
    )
    return response.parsed    