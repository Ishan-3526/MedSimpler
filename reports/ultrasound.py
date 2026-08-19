
from gemini_client import client
from pydantic import BaseModel
from typing import List
from google.genai import types

class organ(BaseModel):
    Organ:str
    Finding:str
    Measurement:str
    Result:str
    Simple_explanation:str

class ultrasound(BaseModel):
    list_of_organs: List[organ]
    overall_summery: str
    doctor_suggestion: str | None


def analyse(file, doc_type, level, language):

    prompt = f"""
    You are a ultrasound specialist, focusing on
    Extracting data from ultrasound reports.

    But this report is for {doc_type}.

    Response should be in language {language}.

    The level of explanation should be {level}.

    Make sure you answer all values:
    - which organ is scanned
    - what finding is noted  
    - what measurement is noted  
    - what is the result 
    - what is the simple explanation of the result
    

    There will be three level 
    Ekadam Basic :- simplest langugae you can provide 
    intermidiate :- few medical terms which are common
    advance:- proper technical , medical representation of DATA , always remember 

    MOST IMPORTANTLY, don't be a doctor.
    Be a Ultrasound Specialist.

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
            "response_schema": ultrasound
        }
    )
    return response.parsed
