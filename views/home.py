import streamlit as st
import pandas as pd
import json
import os
import pickle
from datetime import datetime, timezone
from google.cloud import firestore
from google.oauth2 import service_account

# ML imports
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.neighbors import KNeighborsClassifier

@st.cache_resource
def get_db():
    key_dict = json.loads(st.secrets["textkey"])
    return firestore.Client.from_service_account_info(key_dict)

# #def fill_with_defaults(df: pd.DataFrame, variables: dict, categorical_cols: list, numeric_cols: list) -> pd.DataFrame:
#     """Coerce dtypes then fill NaNs with defaults defined in `variables`."""
#     df = df.copy()

#     # Coerce types first
#     for col in categorical_cols:
#         if col in df.columns:
#             df[col] = df[col].astype("string")  # robust string dtype
#     for col in numeric_cols:
#         if col in df.columns:
#             df[col] = pd.to_numeric(df[col], errors="coerce")

#     # Now fill with your defaults per column
#     for col, spec in variables.items():
#         if col in df.columns:
#             default_val = spec["default"]
#             df[col] = df[col].fillna(default_val)

#     return df
def build_knn_pipeline(categorical_cols, numeric_cols, n_neighbors=7):
    """
    Returns a scikit-learn Pipeline that:
      - imputes missing numeric with median
      - imputes missing categorical with most frequent
      - one-hot encodes categoricals
      - scales numerics
      - trains KNN classifier
    """
    numeric_pipe = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])
    cat_pipe = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("ohe", OneHotEncoder(handle_unknown="ignore"))
    ])
    pre = ColumnTransformer(
        transformers=[
            ("num", numeric_pipe, numeric_cols),
            ("cat", cat_pipe, categorical_cols)
        ],
        remainder="drop",
        verbose_feature_names_out=False
    )
    model = Pipeline(steps=[
        ("preprocess", pre),
        ("knn", KNeighborsClassifier(n_neighbors=n_neighbors, weights="distance", metric="minkowski", p=2))
    ])
    return model
# #def build_knn_pipeline(categorical_cols, numeric_cols, n_neighbors=7):
#     """
#     Preprocessing assumes NaNs are already filled with defaults.
#     """
#     numeric_pipe = Pipeline(steps=[
#         ("scaler", StandardScaler())
#     ])
#     cat_pipe = Pipeline(steps=[
#         ("ohe", OneHotEncoder(handle_unknown="ignore"))
#     ])
#     pre = ColumnTransformer(
#         transformers=[
#             ("num", numeric_pipe, numeric_cols),
#             ("cat", cat_pipe, categorical_cols)
#         ],
#         remainder="drop",
#         verbose_feature_names_out=False
#     )
#     model = Pipeline(steps=[
#         ("preprocess", pre),
#         ("knn", KNeighborsClassifier(n_neighbors=n_neighbors, weights="distance", metric="minkowski", p=2))
#     ])
#     return model

def try_load_pipeline(path="model.pkl"):
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception:
        return None

def main():
    db = get_db()

    st.title("Pediatric CRRT Calculator for Survival Prediction (PCCSP)")

    # --- Patient meta ---
    Patient_Name = st.text_input("Patient Name", key="Patient_Name")
    Patient_ID = st.text_input("Patient ID", key="Patient_ID")
    date = datetime.now(timezone.utc)

    # --- Feature schema (your existing defaults & tags) ---
    variables = {
        "Sex": {"label": "Sex", "default": "Male", "tag": "Sex"},
        "Age": {"label": "Age (years)", "default": 5.7, "tag": "Age (Significant)"},
        "Weight": {"label": "Weight (kg)", "default": 16.8, "tag": "Weight (Significant)"},
        "PRISM_III_Score": {"label": "PRISM III Score *", "default": 14.02, "tag": "PRISM III Score (Significant)"},
        "Vasoactive_Inotropic_Score": {"label": "Vasoactive-Inotropic Score *", "default": 9.36, "tag": "Vasoactive-Inotropic Score (Significant)"},
        "PICU_Stay": {"label": "PICU Stay (days)", "default": 13.5, "tag": "PICU Stay"},
        "Ventilator_Usage": {"label": "Ventilator Usage *", "default": "No", "tag": "Ventilator Usage (Significant)"},
        "Interval_from_Admission": {"label": "Interval from Admission (hours)", "default": 18.17, "tag": "Interval from Admission"},
        "Duration_of_CRRT": {"label": "Duration of CRRT (days)", "default": 4.23, "tag": "Duration of CRRT (Significant)"},
        "Fluid_Overload": {"label": "Fluid Overload *", "default": "No", "tag": "Fluid Overload (Significant)"},
        "FO_at_CRRT_Initiation": {"label": "% FO at CRRT Initiation *", "default": 8.12, "tag": "% FO at CRRT Initiation (Significant)"},
        "pH": {"label": "pH Level *", "default": 7.33, "tag": "pH Level (Significant)"},
        "Lactic_Acid": {"label": "Lactic Acid (mmol/L) *", "default": 2.24, "tag": "Lactic Acid"},
        "Hb": {"label": "Hemoglobin (g/dL)", "default": 9.45, "tag": "Hemoglobin"},
        "Platelet": {"label": "Platelet (10³/µL)", "default": 109.54, "tag": "Platelet"},
        "Urine_Volume": {"label": "Urine Volume (mL/Kg/h) *", "default": 0.9, "tag": "Urine Volume"},
        "Sepsis": {"label": "Sepsis", "default": "No", "tag": "Sepsis (Significant)"},
        "Acute_Liver_Failure": {"label": "Acute Liver Failure", "default": "No", "tag": "Acute Liver Failure (Significant)"},
        "Respiratory_Disease": {"label": "Respiratory System Disease *", "default": "No", "tag": "Respiratory System Disease (Significant)"},
        "Albumin": {"label": "Albumin (g/dL) *", "default": 3.05, "tag": "Albumin (Significant)"},
        "Creatinine": {"label": "Creatinine (mg/dL)", "default": 1.5, "tag": "Creatinine (Significant)"},
        "PELOD": {"label": "PELOD Score *", "default": 12.22, "tag": "PELOD Score (Significant)"},
        "pSOFA": {"label": "pSOFA Score *", "default": 9.56, "tag": "pSOFA Score (Significant)"},
        "Bicarbonate": {"label": "Bicarbonate (mmEq/L)", "default": 21.7, "tag": "Bicarbonate"},
        "Sodium": {"label": "Sodium (mmol/L)", "default": 138.72, "tag": "Sodium (Significant)"},
        "Potassium": {"label": "Potassium (mmol/L)", "default": 3.61, "tag": "Potassium"},
        "Tumor_Lysis_Syndrome": {"label": "Tumor Lysis Syndrome", "default": "Yes", "tag": "Tumor Lysis Syndrome"},
        "Hyperammonemia": {"label": "Hyperammonemia", "default": "Yes", "tag": "Hyperammonemia"}
    }

    categorical_options = {
        "Sex": ["Male", "Female"],
        "Ventilator_Usage": ["Yes", "No"],
        "Fluid_Overload": ["Yes", "No"],
        "Sepsis": ["Yes", "No"],
        "Acute_Liver_Failure": ["Yes", "No"],
        "Respiratory_Disease": ["Yes", "No"],
        "Tumor_Lysis_Syndrome": ["Yes", "No"],
        "Hyperammonemia": ["Yes", "No"]
    }

    significant_variables = ["Age","Weight","PRISM_III_Score","Vasoactive_Inotropic_Score","Ventilator_Usage","Duration_of_CRRT",
                             "Fluid_Overload","FO_at_CRRT_Initiation","pH","Sepsis","Acute_Liver_Failure",
                             "Respiratory_Disease","Albumin","Creatinine","PELOD","pSOFA","Sodium"]

    higher_or_equal_variables = ["pH","Platelet","Urine_Volume","Albumin","Bicarbonate","Potassium"]

    # --- UI layout ---
    col1, col2 = st.columns(2)

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
        user_data["Creatinine"] = st.number_input("Creatinine (mg/dL)", value=None, step=0.1, format="%.2f")
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
        user_data["Urine_Volume"] = st.number_input("Urine Volume (mL/Kg/h) *", value=None, step=0.1, format="%.2f")
        user_data["Acute_Liver_Failure"] = st.selectbox("Acute Liver Failure", ["Yes", "No"], index=None)
        user_data["Albumin"] = st.number_input("Albumin (g/dL) *", value=None, step=0.1, format="%.2f")
        user_data["PELOD"] = st.number_input("PELOD Score *", value=None, step=0.1, format="%.2f")
        user_data["Bicarbonate"] = st.number_input("Bicarbonate (mmEq/L)", value=None, step=0.1, format="%.2f")
        user_data["Potassium"] = st.number_input("Potassium (mmol/L)", value=None, step=0.1, format="%.2f")
        user_data["Hyperammonemia"] = st.selectbox("Hyperammonemia", ["Yes", "No"], index=None)

    # --- KNN Training/Loading controls ---
    st.subheader("Model")
    c1, c2 = st.columns(2)
    with c1:
        uploaded_csv = st.file_uploader("Upload training CSV (must include 'Survival' target)", type=["csv"])
    with c2:
        n_neighbors = st.slider("k (neighbors)", min_value=3, max_value=31, value=7, step=2)

    # Columns split for preprocessing
    categorical_cols = list(categorical_options.keys())
    numeric_cols = [c for c in variables.keys() if c not in categorical_cols]

    # Try to load pre-trained pipeline first; if CSV is uploaded, we’ll train & override.
    knn_pipeline = try_load_pipeline("model.pkl")

    # Train from uploaded CSV (cached by file content)
    if uploaded_csv is not None:
        df = pd.read_csv(uploaded_csv)
        missing_cols = [c for c in variables.keys() if c not in df.columns]
        if missing_cols:
            st.error(f"Training CSV is missing columns: {', '.join(missing_cols)}")
        elif "Survival" not in df.columns:
            st.error("Training CSV must include target column 'Survival' (0/1).")
        else:
            # Cast category cols to string, numerics to float where possible
            for col in categorical_cols:
                if col in df.columns:
                    df[col] = df[col].astype(str)
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            X = df[variables.keys()]
            y = df["Survival"].astype(int)

            knn_pipeline = build_knn_pipeline(categorical_cols, numeric_cols, n_neighbors=n_neighbors)
            knn_pipeline.fit(X, y)
            st.success("KNN pipeline trained from uploaded CSV.")
            # Optionally persist
            try:
                with open("model.pkl", "wb") as f:
                    pickle.dump(knn_pipeline, f)
                st.caption("Saved trained pipeline to model.pkl")
            except Exception:
                pass
    # if uploaded_csv is not None:
    #     df = pd.read_csv(uploaded_csv)
    #     missing_cols = [c for c in variables.keys() if c not in df.columns]
    #     if missing_cols:
    #         st.error(f"Training CSV is missing columns: {', '.join(missing_cols)}")
    #     elif "Survival" not in df.columns:
    #         st.error("Training CSV must include target column 'Survival' (0/1).")
    #     else:
    #         # Columns split once (same as below)
    #         categorical_cols = list(categorical_options.keys())
    #         numeric_cols = [c for c in variables.keys() if c not in categorical_cols]

    #         # 1) Coerce types + 2) Fill NaNs with defaults from `variables`
    #         df = fill_with_defaults(df, variables, categorical_cols, numeric_cols)

    #         # Build X/y with guaranteed no NaNs
    #         X = df[list(variables.keys())]
    #         y = df["Survival"].astype(int)

    #         knn_pipeline = build_knn_pipeline(categorical_cols, numeric_cols, n_neighbors=n_neighbors)
    #         knn_pipeline.fit(X, y)
    #         st.success("KNN pipeline trained from uploaded CSV with default-value imputation.")
    #         try:
    #             with open("model.pkl", "wb") as f:
    #                 pickle.dump(knn_pipeline, f)
    #             st.caption("Saved trained pipeline to model.pkl")
    #         except Exception:
    #             pass
                
    # --- Calculate button (keeps your original logic) ---
    if st.button("Calculate"):
        # ===== 1) Your rule-based score =====
        expected_categorical = {
            "Sex": "Male",
            "Ventilator_Usage": "No",
            "Fluid_Overload": "No",
            "Respiratory_Disease": "No",
            "Sepsis": "No",
            "Acute_Liver_Failure": "No",
            "Tumor_Lysis_Syndrome": "No",
            "Hyperammonemia": "No"
        }

        total_variables = 0
        within_limit = 0
        within_limit_vars = []

        for var, props in variables.items():
            value = user_data.get(var, None)
            upper_limit = props["default"]
            if value is not None:
                if var in categorical_options:
                    total_variables += 1
                    if var in significant_variables:
                        total_variables += 1
                    if var in expected_categorical:
                        if value == expected_categorical[var]:
                            within_limit += 1
                            within_limit_vars.append(props["tag"])
                            if var in significant_variables:
                                within_limit += 1
                    else:
                        # Neutral categoricals (e.g., Sex) do not affect score
                        pass
                else:
                    total_variables += 1
                    if var in significant_variables:
                        total_variables += 1
                    if var in higher_or_equal_variables:
                        if value >= upper_limit:
                            within_limit += 1
                            within_limit_vars.append(props["tag"])
                            if var in significant_variables:
                                within_limit += 1
                    else:
                        if value <= upper_limit:
                            within_limit += 1
                            within_limit_vars.append(props["tag"])
                            if var in significant_variables:
                                within_limit += 1

        final_score = (within_limit / total_variables) * 100 if total_variables > 0 else None

        # ===== 2) KNN prediction =====
        # Build a single-row DataFrame in the exact training column order.
        row = {}
        for key in variables.keys():
            v = user_data.get(key, None)
            # If user left it empty, fall back to your "default"
            if v is None:
                v = variables[key]["default"]
            row[key] = v

        X_user = pd.DataFrame([row])

        # Ensure dtypes are consistent: categorical as str, numerics as float
        for col in categorical_cols:
            if col in X_user.columns:
                X_user[col] = X_user[col].astype(str)
        for col in numeric_cols:
            if col in X_user.columns:
                X_user[col] = pd.to_numeric(X_user[col], errors="coerce")

        knn_pred = None
        knn_prob = None

        if knn_pipeline is not None:
            try:
                knn_pred = int(knn_pipeline.predict(X_user)[0])
                # Assume class 1 = survivor probability
                proba = knn_pipeline.predict_proba(X_user)[0]
                # Find index for class 1 safely
                class_index = list(knn_pipeline.classes_).index(1) if hasattr(knn_pipeline, "classes_") else 1
                knn_prob = float(proba[class_index]) * 100.0
            except Exception as e:
                st.error(f"KNN prediction error: {e}")
        else:
            st.warning("No model available. Upload training CSV or provide model.pkl to enable KNN.")

        # ===== 3) Persist to Firestore =====
        if not Patient_Name or not Patient_ID:
            st.warning("Please fill Patient Name and Patient ID.")
        else:
            doc_ref = db.collection("Hasil_KNN").document(f"{Patient_Name}_{datetime.now(timezone.utc).strftime('%Y%m%d')}")
            payload = {
                "Patient_Name": Patient_Name,
                "Patient_ID": Patient_ID,
                "Date": date,
                **{k: user_data.get(k, None) for k in variables.keys()},
                "RuleBased_Score": final_score,
                "KNN_Prediction": knn_pred,
                "KNN_Probability": knn_prob
            }
            doc_ref.set(payload)

        # ===== 4) UI feedback =====
        if final_score is None:
            st.warning("No variables included in the rule-based calculation.")
        else:
            if final_score >= 50:
                st.success(f"Rule-based survival score: {final_score:.2f}%")
            else:
                st.error(f"Rule-based survival score: {final_score:.2f}%")

        if knn_prob is not None:
            label = "Survivor" if knn_pred == 1 else "Non-survivor"
            st.success(f"KNN predicted: {label}  •  Probability of survival: {knn_prob:.2f}%")
        elif knn_pipeline is None:
            st.info("Train or load a KNN model to see ML predictions.")

        if within_limit_vars:
            st.info("Variables within the survivor criteria: " + ", ".join(within_limit_vars))
        else:
            st.info("No variables met the survivor criteria based on current inputs.")


if __name__ == "__main__":
    main()