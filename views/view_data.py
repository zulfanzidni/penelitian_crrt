import streamlit as st
import pandas as pd
import json
from google.cloud import firestore
from google.oauth2 import service_account

st.subheader("📁 Rule Based History")

# Establish the database connection
# authenticate with Firebase service account
key_dict = json.loads(st.secrets["textkey"])
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds)

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
    "Respiratory_Disease", "Creatinine", "pSOFA",
    "Sodium", "Tumor_Lysis_Syndrome", "PRISM_III_Score",
    "PICU_Stay", "Interval_from_Admission",
    "Fluid_Overload", "pH", "Hb", "Urin",
    "Acute_Liver_Failure", "Albumin", "PELOD",
    "Bicarbonate", "Potassium", "Hyperammonemia",
    "Prediction_Score"
]]
st.write(patient_df)


st.subheader("📁 KNN History")

knn_ref = db.collection("Hasil_KNN")
knn_snap = knn_ref.get()
knn_data = []

for doc in knn_snap:
    data = doc.to_dict()
    data["Patient_Name"] = doc.id
    knn_data.append(data)

if knn_data:
    knn_df = pd.DataFrame(knn_data)
    knn_df = knn_df[[
        "Patient_ID", "Patient_Name", 
        "Date", "RuleBased_Score", 
        "KNN_Probability", "KNN_Prediction"
    ]]
    st.write(knn_df)
else:
    st.info("⚠️ No KNN history found in the database")