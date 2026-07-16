# knn_model.py
import pandas as pd
import time
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# ----- Step 1: Load Dataset -----
df = pd.read_excel("TrainingDataset.xlsx")

# ----- Step 2: Features & Target -----
X = df.drop(columns=["Match_Suitability"])
y = df["Match_Suitability"]

# Identify categorical and numeric columns
categorical_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()
numeric_cols = X.select_dtypes(include=["int64", "float64"]).columns.tolist()

# ----- Step 3: Preprocessing -----
preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), numeric_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols)
    ]
)

# ----- Step 4: Pipeline with KNN -----
knn_pipeline = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("classifier", KNeighborsClassifier(n_neighbors=5, metric="minkowski", p=2))
])

# ----- Step 5: Train-Test Split -----
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ----- Step 6: Training -----
start_time = time.time()
knn_pipeline.fit(X_train, y_train)
train_time = time.time() - start_time

# ----- Step 7: Evaluation -----
start_time = time.time()
y_pred = knn_pipeline.predict(X_test)
test_time = time.time() - start_time

print("KNN Accuracy:", accuracy_score(y_test, y_pred))
print("Training Time:", round(train_time, 4), "seconds")
print("Testing Time:", round(test_time, 4), "seconds")
print("\nClassification Report:\n", classification_report(y_test, y_pred))
print("\nConfusion Matrix:\n", confusion_matrix(y_test, y_pred))

# ----- Step 8: Save Model -----
joblib.dump(knn_pipeline, "knn_model.pkl")
