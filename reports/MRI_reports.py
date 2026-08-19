
from gemini_client import client
from pydantic import BaseModel
from typing import List
from google.genai import types

class MRIFinding(BaseModel):
    body_part: str
    finding: str
    measurements: list[str]
    status: str
    simple_explanation: str


class MRIReport(BaseModel):
    examination: str
    clinical_indication: str | None
    technique: str | None
    findings: list[MRIFinding]
    impression: str | None
    overall_summary: str


def analyse(file, doc_type, level, language):

    prompt = f"""
You are a medical report simplification assistant.

The uploaded document is an MRI REPORT.

Your task is to read the report and explain it in {language}.

The requested explanation level is: {level}

IMPORTANT:
You are NOT a doctor and must NOT independently diagnose the patient.

Do not:
- invent findings
- invent measurements
- invent diagnoses
- recommend medicines
- recommend treatment
- change or contradict the radiologist's findings
- assume that an abnormal finding automatically means a disease

Your job is to accurately explain what the MRI report says
in language that an ordinary person can understand.

Extract the following:

1. EXAMINATION

Identify:
- What type of MRI was performed
- Which body part or region was examined
- Whether contrast was used, if mentioned

2. CLINICAL INDICATION

Extract the reason for the MRI if it is mentioned.

If it is not mentioned, return null.

3. TECHNIQUE

Extract important information about how the MRI was performed,
including sequences or contrast information if mentioned.

Do not add technical details that are not present in the report.

4. FINDINGS

Extract the important findings from the MRI report.

For every finding:

- Identify the body part, organ, tissue, or anatomical structure involved.
- State what the report actually says.
- Extract any measurements mentioned.
- Classify the finding as:
  "Normal", "Abnormal", or "Uncertain"
  based only on the report.
- Explain the finding in very simple language.

When the report contains technical MRI terminology such as:
- hyperintense
- hypointense
- signal alteration
- diffusion restriction
- edema
- lesion
- degeneration
- disc bulge
- disc protrusion
- stenosis
- tear
- effusion

explain what the term means in simple language.

IMPORTANT:
Do not convert a finding into a diagnosis unless the report itself
explicitly gives that diagnosis.

For example, if the report says:
"Hyperintense lesion on T2-weighted images"

explain what that finding means rather than deciding what disease
caused the lesion.

5. IMPRESSION

Extract the radiologist's final impression/conclusion.

Explain it in simple language while preserving its original meaning.

Do not create your own medical conclusion.

6. OVERALL SUMMARY

Give a short, simple summary of what the MRI basically found.

The summary should focus on the important findings rather than
repeating every technical detail.

If the report is essentially normal, clearly explain that the report
does not describe a significant abnormality, if that is what the
radiologist states.

If something is not mentioned in the report, do not guess.

MOST IMPORTANTLY:

The goal is to make the MRI report understandable to a normal person,
not to sound like another medical report.

Prefer simple language.

If a medical term is necessary, explain it immediately.

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
            "response_schema": MRIReport        }
    )
    return response.parsed
