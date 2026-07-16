# nb_model.py
import pandas as pd
import time
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import json

# ----- Step 1: Load Dataset -----
df = pd.read_excel("TrainingDataset.xlsx")

# ----- Step 2: Features & Target -----
X = df.drop(columns=["Match_Suitability"])
y = df["Match_Suitability"]

# Identify categorical and numeric columns
categorical_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()
numeric_cols = X.select_dtypes(include=["int64", "float64"]).columns.tolist()

# ----- Step 3: Preprocessing -----
# Encode categoricals with OneHotEncoder, scale numerics
preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), numeric_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols)
    ]
)

# ----- Step 4: Pipeline with Naive Bayes -----
nb_pipeline = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("classifier", GaussianNB())
])

# ----- Step 5: Train-Test Split -----
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ----- Step 6: Training -----
start_time = time.time()
nb_pipeline.fit(X_train, y_train)
train_time = time.time() - start_time

# ----- Step 7: Evaluation -----
start_time = time.time()
y_pred = nb_pipeline.predict(X_test)
test_time = time.time() - start_time

print("Naive Bayes Accuracy:", accuracy_score(y_test, y_pred))
print("Training Time:", round(train_time, 4), "seconds")
print("Testing Time:", round(test_time, 4), "seconds")
print("\nClassification Report:\n", classification_report(y_test, y_pred))
print("\nConfusion Matrix:\n", confusion_matrix(y_test, y_pred))

accuracy = accuracy_score(y_test, y_pred)
conf_matrix = confusion_matrix(y_test, y_pred).tolist()
report = classification_report(y_test, y_pred, output_dict=True)

# Save Results into JSON
results = {
    "accuracy": round(accuracy, 4),  # e.g. 0.9792
    "confusion_matrix": conf_matrix,
    "classification_report": report,
    
    "time_efficiency": {
        "training_time_sec": round(train_time, 4),
        "prediction_time_sec": round(test_time, 6)
    }
}

# ----- Step 8: Save Model -----
with open("nb_results.json", "w") as f:
    json.dump(results, f, indent=4)

print("✅ Naive Bayes results saved to rf_results.json")
