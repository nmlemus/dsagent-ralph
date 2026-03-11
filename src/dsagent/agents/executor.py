"""Executor Agent - Executes skills in Jupyter kernel"""
from uuid import UUID
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from dsagent.db.models import Item
from dsagent.db.repositories import ItemRepository
from dsagent.services.kernel import KernelService


class ExecutorAgent:
    """
    Executor Agent executes items using appropriate skills in Jupyter kernel.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.item_repo = ItemRepository(db)
        self.kernel_service = KernelService()
    
    async def execute(self, item: Item) -> Dict[str, Any]:
        """
        Execute a single item using the appropriate skill.
        """
        skill_name = item.skill_name
        skill_params = item.skill_params or {}
        
        # Get skill code
        skill_code = self._get_skill_code(skill_name, skill_params)
        
        # Execute in kernel
        try:
            result = await self.kernel_service.execute_code(
                project_id=str(item.project_id),
                code=skill_code
            )
            
            if result.get("success"):
                return {
                    "status": "success",
                    "output": result.get("output"),
                    "charts": result.get("charts", [])
                }
            else:
                return {
                    "status": "error",
                    "error": result.get("error"),
                    "output": result.get("output")
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _get_skill_code(self, skill_name: str, params: Dict[str, Any]) -> str:
        """
        Get executable code for a skill.
        
        In production, this would load skill modules dynamically.
        """
        skills = {
            "inspect-data": self._skill_inspect_data,
            "generate-eda": self._skill_generate_eda,
            "train-baselines": self._skill_train_baselines,
            "evaluate-models": self._skill_evaluate_models,
            "write-report": self._skill_write_report,
            "data-cleaning": self._skill_data_cleaning,
            "feature-engineering": self._skill_feature_engineering,
        }
        
        skill_func = skills.get(skill_name, self._skill_default)
        return skill_func(params)
    
    def _skill_inspect_data(self, params: Dict[str, Any]) -> str:
        profile = params.get("profile", "all")
        return f"""
import pandas as pd
import json

# Load data
df = pd.read_csv('/projects/{params.get('project_id', '')}/data/raw/*.csv')

# Profile
if "{profile}" in ["all", "numeric"]:
    print("=== NUMERIC COLUMNS ===")
    print(df.describe())

if "{profile}" in ["all", "categorical"]:
    print("\\n=== CATEGORICAL COLUMNS ===")
    for col in df.select_dtypes(include='object').columns:
        print(f"{{col}}: {{df[col].nunique()}} unique values")

print("\\n=== SHAPE ===")
print(f"Rows: {{len(df)}}, Columns: {{len(df.columns)}}")

print("\\n=== DTYPES ===")
print(df.dtypes)
"""
    
    def _skill_generate_eda(self, params: Dict[str, Any]) -> str:
        return """
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('/projects/*/data/raw/*.csv')

# Generate basic visualizations
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Numeric distributions
numeric_cols = df.select_dtypes(include=['number']).columns[:4]
for i, col in enumerate(numeric_cols):
    ax = axes[i // 2, i % 2]
    ax.hist(df[col].dropna(), bins=30, edgecolor='black')
    ax.set_title(col)

plt.tight_layout()
plt.savefig('/artifacts/eda_plots.png', dpi=100)
print("EDA plots saved to /artifacts/eda_plots.png")
"""
    
    def _skill_train_baselines(self, params: Dict[str, Any]) -> str:
        models = params.get("models", ["LogisticRegression", "RandomForest"])
        models_str = ", ".join([f"'{m}'" for m in models])
        return f"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
import joblib

# Load and prepare data
df = pd.read_csv('/projects/*/data/raw/*.csv')
target = '{params.get("target", "target")}'

# Simple preprocessing
X = df.drop(columns=[target], errors='ignore')
y = df[target]

# Handle missing values
X = X.fillna(X.median())

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

results = {{}}
models_to_train = [{models_str}]

for model_name in models_to_train:
    if model_name == 'LogisticRegression':
        model = LogisticRegression(max_iter=1000)
    elif model_name == 'RandomForest':
        model = RandomForestClassifier(n_estimators=100, random_state=42)
    elif model_name == 'XGBoost':
        from xgboost import XGBClassifier
        model = XGBClassifier(use_label_encoder=False, eval_metric='logloss')
    else:
        continue
    
    model.fit(X_train, y_train)
    y_pred = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_pred)
    results[model_name] = {{'roc_auc': auc}}
    
    # Save model
    joblib.dump(model, f'/artifacts/{{model_name.lower()}}.joblib')

print("=== MODEL RESULTS ===")
for name, metrics in results.items():
    print(f"{{name}}: ROC-AUC = {{metrics['roc_auc']:.4f}}")

# Save results
import json
with open('/artifacts/model_results.json', 'w') as f:
    json.dump(results, f, indent=2)
"""
    
    def _skill_evaluate_models(self, params: Dict[str, Any]) -> str:
        return """
import json
import pandas as pd

# Load results
with open('/artifacts/model_results.json') as f:
    results = json.load(f)

print("=== MODEL COMPARISON ===")
for model, metrics in results.items():
    print(f"{{model}}: {{metrics}}")

# Best model
best_model = max(results.items(), key=lambda x: x[1].get('roc_auc', 0))
print(f"\\nBest model: {{best_model[0]}} with ROC-AUC: {{best_model[1]['roc_auc']:.4f}}")

# Save comparison
comparison_df = pd.DataFrame(results).T
comparison_df.to_csv('/artifacts/model_comparison.csv')
"""
    
    def _skill_write_report(self, params: Dict[str, Any]) -> str:
        return """
import json
from datetime import datetime

# Load results
try:
    with open('/artifacts/model_results.json') as f:
        results = json.load(f)
except:
    results = {{}}

report = f\"\"\"# Data Science Task Report

**Date**: {datetime.now().strftime('%Y-%m-%d')}
**Status**: Complete

---

## Executive Summary
Analysis completed successfully.

## Results

### Model Performance
| Model | ROC-AUC |
|-------|---------|
\"\"\"

for model, metrics in results.items():
    report += f"| {{model}} | {{metrics.get('roc_auc', 'N/A')}} |\\n"

report += \"\"\"\n## Recommendations
1. Review feature importance for insights
2. Consider additional feature engineering
3. Validate on test set before deployment

## Artifacts
- Model files in /artifacts/
- EDA plots in /artifacts/eda_plots.png
\"\"\"

# Save report
with open('/projects/*/workspace/final_report.md', 'w') as f:
    f.write(report)

print("Report saved to workspace/final_report.md")
"""
    
    def _skill_data_cleaning(self, params: Dict[str, Any]) -> str:
        return """
import pandas as pd
import numpy as np

df = pd.read_csv('/projects/*/data/raw/*.csv')

# Handle missing values
for col in df.columns:
    if df[col].dtype in ['float64', 'int64']:
        df[col].fillna(df[col].median(), inplace=True)
    else:
        df[col].fillna(df[col].mode()[0] if len(df[col].mode()) > 0 else 'unknown', inplace=True)

# Remove duplicates
df.drop_duplicates(inplace=True)

# Save cleaned data
df.to_csv('/artifacts/cleaned_data.csv', index=False)
print(f"Cleaned data saved: {{len(df)}} rows, {{len(df.columns)}} columns")
"""
    
    def _skill_feature_engineering(self, params: Dict[str, Any]) -> str:
        return """
import pandas as pd
import numpy as np

df = pd.read_csv('/artifacts/cleaned_data.csv')

# Example feature engineering
# Add interaction features
numeric_cols = df.select_dtypes(include=[np.number]).columns[:5]
for i, col1 in enumerate(numeric_cols):
    for col2 in numeric_cols[i+1:]:
        df[f'{{col1}}_x_{{col2}}'] = df[col1] * df[col2]

# Save
df.to_csv('/artifacts/engineered_data.csv', index=False)
print(f"Feature engineering complete: {{len(df.columns)}} columns")
"""
    
    def _skill_default(self, params: Dict[str, Any]) -> str:
        return f"""
# Default skill - {params}
print("Executing skill...")
print(f"Parameters: {{params}}")
"""
    
    async def validate_output(self, result: Dict[str, Any]) -> bool:
        """
        Validate skill output (backpressure).
        """
        if result.get("status") == "error":
            return False
        
        # Check for required outputs based on skill
        output = result.get("output", "")
        
        # Basic validation
        if not output and not result.get("charts"):
            return False
        
        return True
