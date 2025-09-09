import streamlit as st
import pandas as pd
from google.cloud import firestore

st.subheader("Data Pasien CRRT")

# Establish the database connection
# authenticate with Firebase service account
db = firestore.Client.from_service_account_json("dev-crrt-firestore-key.json")

# Display the patient data from firestore with arranged columns
patients_ref = db.collection("Patients")
patients_snap = patients_ref.get()
patient_data = []
for doc in patients_snap:
    data = doc.to_dict()
    data["Patient_Name"] = doc.id
    patient_data.append(data)
patient_df = pd.DataFrame(patient_data)
patient_df = patient_df[[
    "Patient_ID", "Patient_Name", 
    "Date", "Age", "Sex", "Weight",
    "Vasoactive_Inotropic_Score", "Ventilator_Usage",
    "Duration_of_CRRT", "FO_at_CRRT_Initiation",
    "Lactic_Acid", "Platelet", "Sepsis",
    "Respiratory_Disease", "Creatinin", "pSOFA",
    "Sodium", "Tumor_Lysis_Syndrome", "PRISM_III_Score",
    "PICU_Stay", "Interval_from_Admission",
    "Fluid_Overload", "pH", "Hb", "Urin",
    "Acute_Liver_Failure", "Albumin", "PELOD",
    "Bicarbonate", "Potassium", "Hiperammonemia",
    "Prediction_Score"
]]
st.write(patient_df)