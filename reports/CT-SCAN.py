
from gemini_client import client
from pydantic import BaseModel
from typing import List
from google.genai import types


class CTFinding(BaseModel):
    body_part: str
    finding: str
    measurements: list[str]
    status: str
    simple_explanation: str


class CTReport(BaseModel):
    examination: str
    clinical_indication: str | None
    findings: list[CTFinding]
    impression: str | None
    overall_summary: str


def analyse(file, doc_type, level, language):

    prompt = f"""
You are a medical report simplification assistant.

The uploaded document is a CT SCAN REPORT.

Your task is to read the report and explain it in {language}.

The requested explanation level is: {level}

IMPORTANT:
You are NOT a doctor and must NOT diagnose the patient.
Do not create diagnoses that are not stated or supported by the report.
Do not recommend medicines, treatment, or procedures.
Do not invent measurements, findings, reference values, or conclusions.

Your job is to accurately explain what the radiologist has written.

Extract the following:

1. EXAMINATION
Identify what type of CT scan was performed and which body region was examined.

2. CLINICAL INDICATION
Extract the reason for the examination if it is mentioned.
If it is not present, return null.

3. FINDINGS
Extract the important findings from the report.

For every finding:
- Identify the body part or organ involved.
- State what the report actually says.
- Extract any measurements mentioned.
- Classify the finding as:
  "Normal", "Abnormal", or "Uncertain"
  based only on the report.
- Explain the finding in very simple language.

IMPORTANT:
Do not turn a medical finding into a diagnosis.
For example, if the report says "hypodense lesion", explain what
"hypodense lesion" means rather than deciding what disease it represents.

4. IMPRESSION
Extract the radiologist's impression/conclusion exactly in meaning.
Do not add your own conclusion.

5. OVERALL SUMMARY
Give a short explanation of the report in very simple language.

The overall summary should answer:
"What did the scan basically find?"

Avoid unnecessary medical jargon.
If a medical term is necessary, immediately explain what it means in simple language.

If something is not mentioned in the report, do not guess it.

Most importantly, prioritize ACCURACY over adding information.
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
            "response_schema": CTReport
        }
    )
    return response.parsed
