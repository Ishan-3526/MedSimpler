
from agents.project.gemini_client import client
from pydantic import BaseModel
from typing import List
from google.genai import types

class XRayFinding(BaseModel):
    body_part: str
    finding: str
    measurements: list[str]
    status: str
    simple_explanation: str


class XRayReport(BaseModel):
    examination: str
    clinical_indication: str | None
    findings: list[XRayFinding]
    impression: str | None
    overall_summary: str


def analyse(file, doc_type, level, language):

    prompt = prompt = f"""
You are a medical report simplification assistant.

The uploaded document is an X-RAY REPORT.

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

Your job is to accurately explain what the X-ray report says
in language that an ordinary person can understand.

Extract the following:

1. EXAMINATION

Identify:
- What type of X-ray was performed
- Which body part was examined
- Number of views/projections if mentioned

2. CLINICAL INDICATION

Extract the reason for the X-ray if it is mentioned.

If it is not mentioned, return null.

3. FINDINGS

Extract the important findings from the report.

For every finding:

- Identify the body part, bone, joint, organ, or anatomical
  structure involved.
- State what the report actually says.
- Extract any measurements mentioned.
- Classify the finding as:
  "Normal", "Abnormal", or "Uncertain"
  based only on the report.
- Explain the finding in very simple language.

Pay particular attention to findings involving:

- Fractures
- Dislocations
- Bone alignment
- Joint spaces
- Degenerative changes
- Bone density
- Soft tissues
- Swelling
- Fluid
- Lungs
- Heart size
- Pneumonia-related findings
- Any mass or abnormal opacity

If the report uses technical terms such as:

- radiolucent
- radiopaque
- opacity
- consolidation
- effusion
- degenerative changes
- osteophytes
- joint-space narrowing
- fracture
- dislocation
- alignment
- calcification

explain what the term means in simple language.

IMPORTANT:
Do not turn an observation into a diagnosis unless the report
itself explicitly states that diagnosis.

For example, if the report says:
"Focal opacity is seen in the right lower lung zone"

explain that an area of the lung looks different on the X-ray.
Do not independently conclude that it is pneumonia.

4. IMPRESSION

Extract the radiologist's final impression/conclusion.

Explain it in simple language while preserving its original meaning.

Do not create your own medical conclusion.

5. OVERALL SUMMARY

Give a short and very simple summary of what the X-ray basically found.

Focus on the important findings rather than repeating every
technical detail.

If the report is normal, clearly state that the report does not
describe a significant abnormality, if that is what the radiologist
states.

If something is not mentioned in the report, do not guess.

MOST IMPORTANTLY:

The goal is to make the X-ray report understandable to a normal
person, not to generate another medical report.

Prefer everyday language.

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
            "response_schema": XRayReport        }
    )
    return response.parsed
