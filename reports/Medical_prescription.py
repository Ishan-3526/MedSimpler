from agents.project.gemini_client import client
from pydantic import BaseModel
from typing import List
from google.genai import types

class parameter(BaseModel):
    name: str
    Dosage: str
    instructions: str | None
    when_to_take: str | None
    cures_what :str |None
    simple_explaination: str | None


class prescription(BaseModel):
    list_of_parameters: List[parameter]
    overall_summery: str
    doctor_suggestion: str | None


def analyse(file, doc_type, level, language):

    prompt = f"""
    You are a Prescription specialist, focusing on
    Extracting data from Prescriptions.

    But this report is for {doc_type}.

    Response should be in language {language}.

    The level of explanation should be {level}.

    Make sure you answer all values:
    - Which medicine it is
    - For what perpose it is used.
    - What Dosage is suggested by the doctor.
    - When Should that dosage be taken
    - Any instruction like , after few huors of lunch or before lunch 

    There will be three level 
    Ekadam Basic :- simplest langugae you can provide 
    intermidiate :- few medical terms which are common
    advance:- proper technical , medical representation of DATA , always remember 

    MOST IMPORTANTLY, don't be a doctor.
    Be a Medical Expert.

    Don't give medical advice.
    Just explain the report according to level {level}.
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
            "response_schema": prescription
        }
    )
    return response.parsed