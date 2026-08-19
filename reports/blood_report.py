from gemini_client import client
from pydantic import BaseModel
from typing import List
from google.genai import types

class parameter(BaseModel):
    name: str
    value: str
    refrence_range: str | None
    status: str
    simple_explaination: str


class report(BaseModel):
    list_of_parameters: List[parameter]
    overall_summery: str
    doctor_suggestion: str | None


def analyse(file, doc_type, level, language):

    prompt = f"""
    You are a Lab specialist, focusing on Blood tests like CBC, HBA1C,
    thyroid tests etc.

    But this report is for {doc_type}.

    Response should be in language {language}.

    The level of explanation should be {level}.

    Make sure you answer all values:
    - what they are
    - what they actually do in the body
    - their reference range shown in the report
    - whether they are lower, higher or within limit
    - what the result means
    
    There will be three level 
    Ekadam Basic :- simplest langugae you can provide 
    intermidiate :- few medical terms which are common
    advance:- proper technical , medical representation of DATA , always remember 

    MOST IMPORTANTLY, don't be a doctor.
    Be a report explainer.

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
            "response_schema": report
        }
    )
    return response.parsed
