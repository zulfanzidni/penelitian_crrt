import streamlit as st
import pandas as pd
from datetime import datetime
from google.cloud import firestore

def main():
    # Establish the connection
    # authenticate with Firebase service account
    db = firestore.Client.from_service_account_json("dev-crrt-firestore-key.json")

    st.title("Pediatric CRRT Calculator for Survival Prediction (PCCSP)")
    
    Patient_Name = st.text_input("Patient Name", key="Patient_Name")
    Patient_ID = st.text_input("Patient ID", key="Patient_ID")
    date = datetime.now()

    # Define variables and their upper limits with labels
    variables = {
        "Sex": {"label": "Sex", "default": "Male", "tag": "Sex"},
        "Age": {"label": "Age (years)", "default": 5.7, "tag": "Age"},
        "Weight": {"label": "Weight (kg)", "default": 16.0, "tag": "Weight"},
        "PRISM_III_Score": {"label": "PRISM III Score *", "default": 14.0, "tag": "PRISM III Score (Significant)"},
        "Vasoactive_Inotropic_Score": {"label": "Vasoactive-Inotropic Score *", "default": 9.36, "tag": "Vasoactive-Inotropic Score (Significant)"},
        "PICU_Stay": {"label": "PICU Stay (days)", "default": 13.0, "tag": "PICU Stay"},
        "Ventilator_Usage": {"label": "Ventilator Usage *", "default": "No", "tag": "Ventilator Usage (Significant)"},
        "Interval_from_Admission": {"label": "Interval from Admission (hours)", "default": 18.17, "tag": "Interval from Admission"},
        "Duration_of_CRRT": {"label": "Duration of CRRT (days)", "default": 4.23, "tag": "Duration of CRRT"},
        "Fluid_Overload": {"label": "Fluid Overload *", "default": "No", "tag": "Fluid Overload (Significant)"},
        "FO_at_CRRT_Initiation": {"label": "% FO at CRRT Initiation *", "default": 8.12, "tag": "% FO at CRRT Initiation (Significant)"},
        "pH": {"label": "pH Level *", "default": 7.33, "tag": "pH Level (Significant)"},
        "Lactic_Acid": {"label": "Lactic Acid (mmol/L) *", "default": 2.24, "tag": "Lactic Acid (Significant)"},
        "Hb": {"label": "Hemoglobin (g/dL)", "default": 9.45, "tag": "Hemoglobin"},
        "Platelet": {"label": "Platelet (10³/µL)", "default": 109.54, "tag": "Platelet"},
        "Urin": {"label": "Urine Volume (mL/Kg/h) *", "default": 0.9, "tag": "Urine Volume"},
        "Sepsis": {"label": "Sepsis", "default": "No", "tag": "Sepsis"},
        "Acute_Liver_Failure": {"label": "Acute Liver Failure", "default": "No", "tag": "Acute Liver Failure"},
        "Respiratory_Disease": {"label": "Respiratory System Disease *", "default": "No", "tag": "Respiratory System Disease (Significant)"},
        "Albumin": {"label": "Albumin (g/dL) *", "default": 3.05, "tag": "Albumin (Significant)"},
        "Creatinin": {"label": "Creatinine (mg/dL)", "default": 1.5, "tag": "Creatinine"},
        "PELOD": {"label": "PELOD Score *", "default": 12.22, "tag": "PELOD Score (Significant)"},
        "pSOFA": {"label": "pSOFA Score *", "default": 9.56, "tag": "pSOFA Score (Significant)"},
        "Bicarbonate": {"label": "Bicarbonate (mmEq/L)", "default": 21.7, "tag": "Bicarbonate"},
        "Sodium": {"label": "Sodium (mmol/L)", "default": 138.72, "tag": "Sodium"},
        "Potassium": {"label": "Potassium (mmol/L)", "default": 3.61, "tag": "Potassium"},
        "Tumor_Lysis_Syndrome": {"label": "Tumor Lysis Syndrome", "default": "Yes", "tag": "Tumor Lysis Syndrome"},
        "Hiperammonemia": {"label": "Hyperammonemia", "default": "Yes", "tag": "Hyperammonemia"}
    }

    # Define correct categorical options
    categorical_options = {
        "Sex": ["Male", "Female"],
        "Ventilator_Usage": ["Yes", "No"],
        "Fluid_Overload": ["Yes", "No"],
        "Sepsis": ["Yes", "No"],
        "Acute_Liver_Failure": ["Yes", "No"],
        "Respiratory_Disease": ["Yes", "No"],
        "Tumor_Lysis_Syndrome": ["Yes", "No"],
        "Hiperammonemia": ["Yes", "No"]
    }

    # Mark significant variables
    significant_variables = ["PRISM_III_Score", "Vasoactive_Inotropic_Score", "Ventilator_Usage", "Fluid_Overload", "FO_at_CRRT_Initiation", "pH", "Lactic_Acid", "Urin", "Respiratory_Disease", "Albumin", "PELOD", "pSOFA"]

    # Variables that are correct if higher or same than upper limits
    higher_or_equal_variables = ["pH", "Platelet", "Urin", "Albumin", "Bicarbonate", "Potassium"]

    # Split view into two columns
    col1, col2 = st.columns(2)

    # Input fields for user data
    user_data = {}
    with col1:
        user_data["Sex"] = st.selectbox("Sex", ["Male", "Female"], index=None)
        user_data["Weight"] = st.number_input("Weight (kg)", value=None, step=0.1, format="%.2f")
        user_data["Vasoactive_Inotropic_Score"] = st.number_input("Vasoactive-Inotropic Score *", value=None, step=0.1, format="%.2f")
        user_data["Ventilator_Usage"] = st.selectbox("Ventilator Usage *", ["Yes", "No"], index=None)
        user_data["Duration_of_CRRT"] = st.number_input("Duration of CRRT (days)", value=None, step=0.1, format="%.2f")
        user_data["FO_at_CRRT_Initiation"] = st.number_input("% FO at CRRT Initiation *", value=None, step=0.1, format="%.2f")
        user_data["Lactic_Acid"] = st.number_input("Lactic Acid (mmol/L) *", value=None, step=0.1, format="%.2f")
        user_data["Platelet"] = st.number_input("Platelet (10³/µL)", value=None, step=0.1, format="%.2f")
        user_data["Sepsis"] = st.selectbox("Sepsis", ["Yes", "No"], index=None)
        user_data["Respiratory_Disease"] = st.selectbox("Respiratory System Disease *", ["Yes", "No"], index=None)
        user_data["Creatinin"] = st.number_input("Creatinine (mg/dL)", value=None, step=0.1, format="%.2f")
        user_data["pSOFA"] = st.number_input("pSOFA Score *", value=None, step=0.1, format="%.2f")
        user_data["Sodium"] = st.number_input("Sodium (mmol/L)", value=None, step=0.1, format="%.2f")
        user_data["Tumor_Lysis_Syndrome"] = st.selectbox("Tumor Lysis Syndrome", ["Yes", "No"], index=None)

    with col2:
        user_data["Age"] = st.number_input("Age (years)", value=None, step=0.1, format="%.2f")
        user_data["PRISM_III_Score"] = st.number_input("PRISM III Score *", value=None, step=0.1, format="%.2f")
        user_data["PICU_Stay"] = st.number_input("PICU Stay (days)", value=None, step=0.1, format="%.2f")
        user_data["Interval_from_Admission"] = st.number_input("Interval from Admission (hours)", value=None, step=0.1, format="%.2f")
        user_data["Fluid_Overload"] = st.selectbox("Fluid Overload *", ["Yes", "No"], index=None)
        user_data["pH"] = st.number_input("pH Level *", value=None, step=0.1, format="%.2f")
        user_data["Hb"] = st.number_input("Hemoglobin (g/dL)", value=None, step=0.1, format="%.2f")
        user_data["Urin"] = st.number_input("Urine Volume (mL/Kg/h) *", value=None, step=0.1, format="%.2f")
        user_data["Acute_Liver_Failure"] = st.selectbox("Acute Liver Failure", ["Yes", "No"], index=None)
        user_data["Albumin"] = st.number_input("Albumin (g/dL) *", value=None, step=0.1, format="%.2f")
        user_data["PELOD"] = st.number_input("PELOD Score *", value=None, step=0.1, format="%.2f")
        user_data["Bicarbonate"] = st.number_input("Bicarbonate (mmEq/L)", value=None, step=0.1, format="%.2f")
        user_data["Potassium"] = st.number_input("Potassium (mmol/L)", value=None, step=0.1, format="%.2f")
        user_data["Hiperammonemia"] = st.selectbox("Hyperammonemia", ["Yes", "No"], index=None)

    # Calculate score
    if st.button("Calculate"):
        total_variables = 0
        within_limit = 0
        within_limit_vars = []

        for var, props in variables.items():
            value = user_data[var]
            upper_limit = props['default']
            if value is not None:  # Exclude variables with None values
                if var in categorical_options:
                    total_variables += 1
                    if var in significant_variables:
                        total_variables += 1  # Count significant variables twice
                    if value == upper_limit:  # Check if categorical value matches the correct option
                        within_limit += 1
                        within_limit_vars.append(props['tag'])
                        if var in significant_variables:
                            within_limit += 1  # Count significant variables twice
                            # within_limit_vars.append(f"(Significant) {props['tag']}")
                else:
                    total_variables += 1
                    if var in significant_variables:
                        total_variables += 1  # Count significant variables twice
                    if var in higher_or_equal_variables:
                        if value >= upper_limit:
                            within_limit += 1
                            within_limit_vars.append(props['tag'])
                            if var in significant_variables:
                                within_limit += 1
                                # within_limit_vars.append(f"(Significant) {props['tag']}")
                    else:
                        if value <= upper_limit:
                            within_limit += 1
                            within_limit_vars.append(props['tag'])
                            if var in significant_variables:
                                within_limit += 1
                                # within_limit_vars.append(f"(Significant) {props['tag']}")

        if total_variables > 0:
            final_score = (within_limit / total_variables) * 100
            
            # save the result to Firestore
            doc_ref = db.collection("Patients").document(Patient_Name)
            doc_ref.set({
                "Patient_Name": Patient_Name,
                "Patient_ID": Patient_ID,
                "Date": date,
                "Age": user_data["Age"],
                "Sex": user_data["Sex"],
                "Weight": user_data["Weight"],
                "Vasoactive_Inotropic_Score": user_data["Vasoactive_Inotropic_Score"],
                "Ventilator_Usage": user_data["Ventilator_Usage"],
                "Duration_of_CRRT": user_data["Duration_of_CRRT"],
                "FO_at_CRRT_Initiation": user_data["FO_at_CRRT_Initiation"],
                "Lactic_Acid": user_data["Lactic_Acid"],
                "Platelet": user_data["Platelet"],
                "Sepsis": user_data["Sepsis"],
                "Respiratory_Disease": user_data["Respiratory_Disease"],
                "Creatinin": user_data["Creatinin"],
                "pSOFA": user_data["pSOFA"],
                "Sodium": user_data["Sodium"],
                "Tumor_Lysis_Syndrome": user_data["Tumor_Lysis_Syndrome"],
                "PRISM_III_Score": user_data["PRISM_III_Score"],
                "PICU_Stay": user_data["PICU_Stay"],
                "Interval_from_Admission": user_data["Interval_from_Admission"],
                "Fluid_Overload": user_data["Fluid_Overload"],
                "pH": user_data["pH"],
                "Hb": user_data["Hb"],
                "Urin": user_data["Urin"],
                "Acute_Liver_Failure": user_data["Acute_Liver_Failure"],
                "Albumin": user_data["Albumin"],
                "PELOD": user_data["PELOD"],
                "Bicarbonate": user_data["Bicarbonate"],
                "Potassium": user_data["Potassium"],
                "Hiperammonemia": user_data["Hiperammonemia"],
                "Prediction_Score": final_score
                })
            
            if final_score >= 50:
                st.success(f"The survival probability score is: {final_score:.2f}%")
            else:
                st.error(f"The survival probability score is: {final_score:.2f}%")
            st.info(f"Variables within the survivor criteria: ({', '.join(within_limit_vars)})")
            st.cache_data.clear()
            # st.info(f"Variables within limit: {', '.join(within_limit_vars)}")
            # st.info(f"Total variables considered: {total_variables}")
        else:
            st.warning("No variables included in the calculation.")

if __name__ == "__main__":
    main()