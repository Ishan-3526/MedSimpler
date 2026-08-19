import streamlit as st
import importlib

import reports.blood_report as blood_report
import reports.medical_prescription as prescription
import reports.ultrasound as ultrasound
import reports.xray_report as x_ray_report
import reports.ct_scan as ct_scan
import reports.mri_report as mri_report
import reports.other as other

importlib.reload(blood_report)
importlib.reload(prescription)
importlib.reload(X_ray_report)
importlib.reload(CT_SCAN)
importlib.reload(MRI_reports)
importlib.reload(other)

st.title("Medical Report Explainer", text_alignment='center')

file = st.file_uploader(
    "Upload 1 File Only (BETA MODE 🙃)",
    type=["pdf", "png", "jpg", "jpeg", "webp"]
)
doc_type = st.selectbox("Which Medical Report IS Uploaded. ", ["Medicine Prescription", "Blood Report", "Lab Report", "Ultrasound Report", "X-Ray Report", "CT Scan Report", "MRI Report","Other"], index=0)
difficulty = st.selectbox("Which Difficulty You Preffer. ", ["Ekdam Basic", "Intermidiate", "Advance"], index=0)
language = st.selectbox("Preffered Language ", ("English", "Marathi", "Hindi"), index=0)


button=st.button("Analyse",type="primary")

if button:
    if file is None:
        st.warning("File Upload Kar NAAAAAA ")
    else:
        with st.spinner("Gemini is processing your file......."):
            if doc_type == 'Blood Report':
                result = blood_report.analyse(file, doc_type, difficulty, language)
                st.write(result)    
            elif doc_type == 'Medicine Prescription':
                result = prescription.analyse(file, doc_type, difficulty, language)
                st.write(result)    
            elif doc_type == 'Ultrasound Report':
                result = ultrasound.analyse(file, doc_type, difficulty, language)
                st.write(result)    
            elif doc_type == 'X-Ray Report':
                result = ultrasound.analyse(file, doc_type, difficulty, language)
                st.write(result) 
            elif doc_type == 'CT Scan Report':
                result = ultrasound.analyse(file, doc_type, difficulty, language)
                st.write(result) 
            elif doc_type == 'MRI Report':
                result = ultrasound.analyse(file, doc_type, difficulty, language)
                st.write(result) 
            elif doc_type == 'Other':
                result = ultrasound.analyse(file, doc_type, difficulty, language)
                st.write(result)    
            else:
                st.warning("Random File Upload Karu Nako ******")
    
