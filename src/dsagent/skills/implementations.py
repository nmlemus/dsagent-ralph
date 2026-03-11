"""Skills for DSAgent - Executable data science tasks"""
import json
from typing import Dict, Any, List
from dsagent.skills.base import BaseSkill, SkillInput, SkillOutput, SkillRegistry


@SkillRegistry.register
class InspectDataSkill(BaseSkill):
    """Load and profile a dataset"""
    
    name = "inspect-data"
    description = "Load and profile columns of a dataset"
    category = "eda"
    
    async def execute(self, input_data: SkillInput) -> SkillOutput:
        code = f"""
import pandas as pd
import json

# Find data file
import glob
data_files = glob.glob('{input_data.data_path or '/projects/*/data/raw/*.csv'}')
if data_files:
    df = pd.read_csv(data_files[0])
else:
    raise FileNotFoundError('No data file found')

# Basic info
info = {{
    'shape': {{'rows': len(df), 'columns': len(df.columns)}},
    'columns': list(df.columns),
    'dtypes': {{col: str(dtype) for col, dtype in df.dtypes.items()}},
    'missing': {{col: int(count) for col, count in df.isnull().sum().items()}},
    'numeric_cols': list(df.select_dtypes(include=['number']).columns),
    'categorical_cols': list(df.select_dtypes(include=['object']).columns)
}}

# Numeric summary
numeric_summary = df.describe().to_dict()

# Categorical summary
categorical_summary = {{}}
for col in df.select_dtypes(include=['object']).columns:
    categorical_summary[col] = {{
        'unique': int(df[col].nunique()),
        'top': str(df[col].mode()[0]) if len(df[col].mode()) > 0 else None,
        'value_counts': df[col].value_counts().head(5).to_dict()
    }}

result = {{
    'info': info,
    'numeric_summary': numeric_summary,
    'categorical_summary': categorical_summary
}}

print(json.dumps(result, indent=2, default=str))
"""
        return SkillOutput(
            success=True,
            message="Data inspection complete",
            data={"code": code},
            charts=[]
        )


@SkillRegistry.register
class GenerateEDASkill(BaseSkill):
    """Generate EDA visualizations"""
    
    name = "generate-eda"
    description = "Generate EDA visualizations and report"
    category = "eda"
    
    async def execute(self, input_data: SkillInput) -> SkillOutput:
        code = f"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os

# Find data
import glob
data_files = glob.glob('{input_data.data_path or '/projects/*/data/raw/*.csv'}')
df = pd.read_csv(data_files[0])

# Create output directory
os.makedirs('/artifacts', exist_ok=True)

# 1. Distributions
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
numeric_cols = df.select_dtypes(include=['number']).columns[:6]

for i, col in enumerate(numeric_cols):
    ax = axes[i // 3, i % 3]
    ax.hist(df[col].dropna(), bins=30, edgecolor='black', alpha=0.7)
    ax.set_title(f'Distribution of {{col}}')
    ax.set_xlabel(col)
    ax.set_ylabel('Frequency')

plt.tight_layout()
plt.savefig('/artifacts/numeric_distributions.png', dpi=100)
plt.close()

# 2. Correlations
numeric_df = df.select_dtypes(include=['number'])
if len(numeric_df.columns) > 1:
    corr = numeric_df.corr()
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm', center=0)
    plt.title('Correlation Matrix')
    plt.tight_layout()
    plt.savefig('/artifacts/correlation_matrix.png', dpi=100)
    plt.close()

# 3. Categorical distributions
cat_cols = df.select_dtypes(include=['object']).columns[:3]
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

for i, col in enumerate(cat_cols):
    top_vals = df[col].value_counts().head(10)
    axes[i].barh(top_vals.index, top_vals.values)
    axes[i].set_title(f'Top {{col}}')
    axes[i].set_xlabel('Count')

plt.tight_layout()
plt.savefig('/artifacts/categorical_distributions.png', dpi=100)
plt.close()

print("EDA visualizations saved to /artifacts/")
print("- numeric_distributions.png")
print("- correlation_matrix.png") 
print("- categorical_distributions.png")
"""
        return SkillOutput(
            success=True,
            message="EDA visualizations generated",
            data={"code": code},
            charts=["numeric_distributions.png", "correlation_matrix.png", "categorical_distributions.png"]
        )


@SkillRegistry.register
class TrainBaselinesSkill(BaseSkill):
    """Train baseline machine learning models"""
    
    name = "train-baselines"
    description = "Train multiple baseline ML models"
    category = "modeling"
    
    async def execute(self, input_data: SkillInput) -> SkillOutput:
        models = input_data.params.get("models", ["LogisticRegression", "RandomForest", "XGBoost"])
        target = input_data.params.get("target", "target")
        
        code = f"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import roc_auc_score, accuracy_score, classification_report
import joblib
import json
import warnings
warnings.filterwarnings('ignore')

# Load data
import glob
data_files = glob.glob('{input_data.data_path or '/projects/*/data/raw/*.csv'}')
df = pd.read_csv(data_files[0])

# Prepare data
if '{target}' not in df.columns:
    # Try to find target column
    for col in df.columns:
        if 'target' in col.lower() or 'label' in col.lower() or 'class' in col.lower():
            target = col
            break

X = df.drop(columns=[target], errors='ignore')
y = df[target]

# Handle missing values
for col in X.columns:
    if X[col].dtype in ['float64', 'int64']:
        X[col].fillna(X[col].median(), inplace=True)
    else:
        X[col].fillna(X[col].mode()[0] if len(X[col].mode()) > 0 else 'unknown', inplace=True)

# Encode categoricals
for col in X.select_dtypes(include=['object']).columns:
    le = LabelEncoder()
    X[col] = le.fit_transform(X[col].astype(str))

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Scale
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

results = {{}}

# Models to train
models_to_train = {json.dumps(models)}

for model_name in models_to_train:
    print(f"Training {{model_name}}...")
    
    if model_name == 'LogisticRegression':
        model = LogisticRegression(max_iter=1000, random_state=42)
        model.fit(X_train_scaled, y_train)
        y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
    elif model_name == 'RandomForest':
        model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
    elif model_name == 'XGBoost':
        from xgboost import XGBClassifier
        model = XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)
        model.fit(X_train, y_train)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
    else:
        continue
    
    # Evaluate
    auc = roc_auc_score(y_test, y_pred_proba)
    acc = accuracy_score(y_test, model.predict(X_test))
    
    results[model_name] = {{
        'roc_auc': round(auc, 4),
        'accuracy': round(acc, 4),
        'n_features': X.shape[1]
    }}
    
    # Save model
    joblib.dump(model, f'/artifacts/{{model_name.lower()}}.joblib')
    print(f"  {{model_name}}: ROC-AUC = {{auc:.4f}}")

# Find best
best_model = max(results.items(), key=lambda x: x[1].get('roc_auc', 0))
print(f"\\nBest model: {{best_model[0]}} with ROC-AUC: {{best_model[1]['roc_auc']:.4f}}")

# Save results
with open('/artifacts/model_results.json', 'w') as f:
    json.dump(results, f, indent=2)

# Save scaler
joblib.dump(scaler, '/artifacts/scaler.joblib')

print("\\nResults saved to /artifacts/model_results.json")
"""
        return SkillOutput(
            success=True,
            message=f"Trained {len(models)} models",
            data={"code": code},
            charts=[]
        )


@SkillRegistry.register
class EvaluateModelsSkill(BaseSkill):
    """Evaluate and compare trained models"""
    
    name = "evaluate-models"
    description = "Compare model metrics and generate visualizations"
    category = "evaluation"
    
    async def execute(self, input_data: SkillInput) -> SkillOutput:
        code = """
import pandas as pd
import json
import matplotlib.pyplot as plt
import numpy as np

# Load results
with open('/artifacts/model_results.json') as f:
    results = json.load(f)

# Create comparison table
print("=== MODEL COMPARISON ===")
print(f"{'Model':<25} {'ROC-AUC':<12} {'Accuracy':<12}")
print("-" * 50)

for model, metrics in results.items():
    print(f"{model:<25} {metrics.get('roc_auc', 'N/A'):<12} {metrics.get('accuracy', 'N/A'):<12}")

# Best model
best = max(results.items(), key=lambda x: x[1].get('roc_auc', 0))
print(f"\\nBest Model: {best[0]}")
print(f"ROC-AUC: {best[1].get('roc_auc', 'N/A')}")

# Create comparison chart
models = list(results.keys())
aucs = [results[m].get('roc_auc', 0) for m in models]
accs = [results[m].get('accuracy', 0) for m in models]

x = np.arange(len(models))
width = 0.35

fig, ax = plt.subplots(figsize=(10, 6))
bars1 = ax.bar(x - width/2, aucs, width, label='ROC-AUC', color='steelblue')
bars2 = ax.bar(x + width/2, accs, width, label='Accuracy', color='coral')

ax.set_xlabel('Model')
ax.set_ylabel('Score')
ax.set_title('Model Comparison')
ax.set_xticks(x)
ax.set_xticklabels(models, rotation=45, ha='right')
ax.legend()
ax.set_ylim(0, 1)

plt.tight_layout()
plt.savefig('/artifacts/model_comparison.png', dpi=100)
plt.close()

print("\\nComparison chart saved to /artifacts/model_comparison.png")
"""
        return SkillOutput(
            success=True,
            message="Model evaluation complete",
            data={"code": code},
            charts=["model_comparison.png"]
        )


@SkillRegistry.register
class WriteReportSkill(BaseSkill):
    """Generate final report"""
    
    name = "write-report"
    description = "Generate final markdown/HTML report"
    category = "reporting"
    
    async def execute(self, input_data: SkillInput) -> SkillOutput:
        code = """
import json
from datetime import datetime
import os

# Load results
try:
    with open('/artifacts/model_results.json') as f:
        results = json.load(f)
except:
    results = {}

# Determine best model
best_model = "N/A"
best_auc = 0
if results:
    best = max(results.items(), key=lambda x: x[1].get('roc_auc', 0))
    best_model = best[0]
    best_auc = best[1].get('roc_auc', 0)

# Build report
report = f"""# Data Science Task Report

**Date**: {datetime.now().strftime('%Y-%m-%d')}
**Status**: Complete

---

## Executive Summary

Analysis completed successfully. The best performing model is **{best_model}** with a ROC-AUC score of **{best_auc:.4f}**.

## Results

### Model Performance

| Model | ROC-AUC | Accuracy |
|-------|---------|----------|
"""

for model, metrics in results.items():
    report += f"| {model} | {metrics.get('roc_auc', 'N/A')} | {metrics.get('accuracy', 'N/A')} |\\n"

report += f"""
### Best Model: {best_model}

- ROC-AUC: {best_auc:.4f}

## Artifacts

- Model files: `/artifacts/*.joblib`
- Visualizations: `/artifacts/*.png`
- Metrics: `/artifacts/model_results.json`

## Next Steps

1. Review feature importance for insights
2. Consider hyperparameter tuning
3. Validate on test set before deployment

---

*Generated by DSAgent Ralph*
"""

# Save report
os.makedirs('/projects/*/workspace', exist_ok=True)
with open('/projects/*/workspace/final_report.md', 'w') as f:
    f.write(report)

# Also save to artifacts
with open('/artifacts/final_report.md', 'w') as f:
    f.write(report)

print("Report saved to:")
print("- /projects/*/workspace/final_report.md")
print("- /artifacts/final_report.md")
"""
        return SkillOutput(
            success=True,
            message="Report generated",
            data={"code": code},
            charts=[]
        )


@SkillRegistry.register
class DataCleaningSkill(BaseSkill):
    """Clean and preprocess data"""
    
    name = "data-cleaning"
    description = "Handle missing values, outliers, and encoding"
    category = "processing"
    
    async def execute(self, input_data: SkillInput) -> SkillOutput:
        code = """
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
import os

# Load data
import glob
data_files = glob.glob('/projects/*/data/raw/*.csv')
df = pd.read_csv(data_files[0])

original_shape = df.shape

# 1. Handle missing values
print("=== Handling Missing Values ===")
for col in df.columns:
    missing = df[col].isnull().sum()
    if missing > 0:
        print(f"{col}: {missing} missing values")
        if df[col].dtype in ['float64', 'int64']:
            df[col].fillna(df[col].median(), inplace=True)
        else:
            df[col].fillna(df[col].mode()[0] if len(df[col].mode()) > 0 else 'unknown', inplace=True)

# 2. Remove duplicates
duplicates = df.duplicated().sum()
if duplicates > 0:
    print(f"\\nRemoving {duplicates} duplicate rows")
    df.drop_duplicates(inplace=True)

# 3. Handle outliers (simple IQR method for numeric)
for col in df.select_dtypes(include=['number']).columns:
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    # Cap outliers instead of removing
    df[col] = df[col].clip(lower, upper)

# 4. Encode categoricals
label_encoders = {}
for col in df.select_dtypes(include=['object']).columns:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col].astype(str))
    label_encoders[col] = le

# Save cleaned data
os.makedirs('/artifacts', exist_ok=True)
df.to_csv('/artifacts/cleaned_data.csv', index=False)

print(f"\\n=== Cleaning Complete ===")
print(f"Original shape: {original_shape}")
print(f"Cleaned shape: {df.shape}")
print(f"Saved to: /artifacts/cleaned_data.csv")
"""
        return SkillOutput(
            success=True,
            message="Data cleaned successfully",
            data={"code": code},
            charts=[]
        )


@SkillRegistry.register
class FeatureEngineeringSkill(BaseSkill):
    """Create new features"""
    
    name = "feature-engineering"
    description = "Create new features from existing data"
    category = "processing"
    
    async def execute(self, input_data: SkillInput) -> SkillOutput:
        code = """
import pandas as pd
import numpy as np

# Load cleaned data
df = pd.read_csv('/artifacts/cleaned_data.csv')

original_cols = len(df.columns)
print(f"Original features: {original_cols}")

# 1. Interaction features (numeric columns)
numeric_cols = df.select_dtypes(include=['number']).columns[:5]
for i, col1 in enumerate(numeric_cols):
    for col2 in numeric_cols[i+1:]:
        df[f'{col1}_x_{col2}'] = df[col1] * df[col2]

# 2. Aggregation features
for col in numeric_cols[:3]:
    df[f'{col}_squared'] = df[col] ** 2
    df[f'{col}_sqrt'] = np.sqrt(np.abs(df[col]))
    df[f'{col}_log'] = np.log1p(np.abs(df[col]))

# 3. Ratio features
if len(numeric_cols) >= 2:
    df[f'{numeric_cols[0]}_div_{numeric_cols[1]}'] = df[numeric_cols[0]] / (df[numeric_cols[1]] + 1e-10)

# 4. Binning for some columns
for col in numeric_cols[:2]:
    df[f'{col}_bin'] = pd.qcut(df[col], q=5, labels=False, duplicates='drop')

print(f"Features after engineering: {len(df.columns)}")
print(f"New features added: {len(df.columns) - original_cols}")

# Save
df.to_csv('/artifacts/engineered_data.csv', index=False)
print(f"Saved to: /artifacts/engineered_data.csv")
"""
        return SkillOutput(
            success=True,
            message="Feature engineering complete",
            data={"code": code},
            charts=[]
        )


# Export all skills
__all__ = [
    "InspectDataSkill",
    "GenerateEDASkill", 
    "TrainBaselinesSkill",
    "EvaluateModelsSkill",
    "WriteReportSkill",
    "DataCleaningSkill",
    "FeatureEngineeringSkill",
    "SkillRegistry"
]
