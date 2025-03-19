import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Title
st.title("Aluminum Rod Health Classification App 🚀")

# Upload dataset
uploaded_file = st.file_uploader("Upload Aluminum Dataset (CSV)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Define feature columns
    feature_columns = [
        "chemical_composition", "casting_temperature", "cooling_water_temperature",
        "casting_speed", "entry_temperature", "emulsion_temperature",
        "emulsion_pressure", "emulsion_concentration", "quench_water_pressure"
    ]

    # Classify health
    def classify_health(row):
        if (
            0.9 <= row['chemical_composition'] <= 1.1 and
            680 <= row['casting_temperature'] <= 720 and
            25 <= row['cooling_water_temperature'] <= 35 and
            1.0 <= row['casting_speed'] <= 2.0 and
            320 <= row['entry_temperature'] <= 380 and
            55 <= row['emulsion_temperature'] <= 65 and
            2.0 <= row['emulsion_pressure'] <= 3.0 and
            0.07 <= row['emulsion_concentration'] <= 0.12 and
            1.5 <= row['quench_water_pressure'] <= 2.5
        ):
            return "Healthy"
        elif (
            row['chemical_composition'] < 0.9 or row['chemical_composition'] > 1.1 or
            row['casting_temperature'] < 680 or row['casting_temperature'] > 720
        ):
            return "Defective"
        else:
            return "Moderate"

    df["health_status"] = df.apply(classify_health, axis=1)

    # Sidebar for filtering
    status_filter = st.sidebar.selectbox("Select Health Status", ["All", "Healthy", "Moderate", "Defective"])
    
    if status_filter != "All":
        df = df[df["health_status"] == status_filter]

    # Display data
    st.subheader("Filtered Rods Data")
    st.write(df)

    # Download button
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(label="Download Filtered Data", data=csv, file_name="filtered_data.csv", mime="text/csv")

    # Train Model
    X = df[feature_columns]
    y = df["health_status"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Model Accuracy
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    st.subheader(f"Model Accuracy: {accuracy * 100:.2f}%")

    # Input for Prediction
    st.subheader("🔮 Predict New Rod Health")
    input_values = []
    for col in feature_columns:
        val = st.number_input(f"Enter {col}", float(df[col].min()), float(df[col].max()), float(df[col].mean()))
        input_values.append(val)

    if st.button("Predict Health Status"):
        input_df = pd.DataFrame([input_values], columns=feature_columns)
        prediction = model.predict(input_df)
        st.success(f"Predicted Health Status: **{prediction[0]}**")

    # Data Analytics & Visualizations
    st.subheader("📊 Data Analytics & Graphs")

    # Health Status Distribution
    fig, ax = plt.subplots()
    sns.countplot(x="health_status", data=df, palette="coolwarm", ax=ax)
    ax.set_title("Health Status Distribution")
    st.pyplot(fig)

    # Correlation Heatmap
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(df[feature_columns].corr(), annot=True, cmap="coolwarm", ax=ax)
    ax.set_title("Feature Correlation Heatmap")
    st.pyplot(fig)

    # Boxplot of Casting Temperature by Health
    fig, ax = plt.subplots()
    sns.boxplot(x="health_status", y="casting_temperature", data=df, palette="coolwarm", ax=ax)
    ax.set_title("Casting Temperature vs. Health Status")
    st.pyplot(fig)

    # Scatter Plot: Casting Speed vs Entry Temperature
    fig, ax = plt.subplots()
    sns.scatterplot(x="casting_speed", y="entry_temperature", hue="health_status", data=df, palette="coolwarm", ax=ax)
    ax.set_title("Casting Speed vs Entry Temperature")
    st.pyplot(fig)
