"""Train and serve an explicitly NEED-trained property-only benchmark.

This is a separate, opt-in research model. It is never silently substituted for
TREE's original synthetic-demo model. All fields use official NEED categories.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from ml.need_challenger import FEATURES, TARGETS, model

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'ml' / 'models' / 'need_2026'


def train(csv: Path):
    data = pd.read_csv(csv, dtype=str, low_memory=False)
    OUT.mkdir(parents=True, exist_ok=True)
    results = {}
    for fuel, (target, flag, _prior, _priorflag) in TARGETS.items():
        actual = pd.to_numeric(data[target], errors='coerce')
        eligible = data[flag].fillna('').eq('V') & actual.notna() & actual.ge(0)
        frame = data.loc[eligible, FEATURES].fillna('Unknown')
        y = actual.loc[eligible].astype(float)
        # Hold out 20% untouched: this saved model is trained ONLY on the
        # 80% training+validation portion of the published evaluation split.
        train_idx, test_idx = train_test_split(np.arange(len(frame)), test_size=.2, random_state=42)
        selected = 'hist_gradient_boosting'  # selected on validation in challenger report
        fitted = model(selected, FEATURES, []).fit(frame.iloc[train_idx], y.iloc[train_idx])
        joblib.dump(fitted, OUT / f'{fuel}.joblib')
        results[fuel] = {'model': selected, 'training_records': len(train_idx),
                         'held_out_records': len(test_idx)}
    allowed_values={field: sorted(set(data[field].fillna('Unknown').astype(str)) | {'Unknown'}) for field in FEATURES}
    manifest = {'dataset': 'UK NEED 2026 anonymised sample', 'mode': 'property_only',
                'features': FEATURES, 'allowed_values': allowed_values, 'training': results,
                'disclaimer': 'Research benchmark on official categorical fields. Not a validated EPC lookup or retrofit-savings model.'}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    return manifest


def predict(official_fields: dict):
    missing = [field for field in FEATURES if field not in official_fields]
    if missing:
        raise ValueError('Missing official NEED fields: ' + ', '.join(missing))
    manifest_path = OUT / 'manifest.json'
    if not manifest_path.exists():
        raise FileNotFoundError('NEED models not trained. Run python -m ml.serve_need --csv path/to/anon2026_50k.csv')
    values = {field: str(official_fields[field]) if official_fields[field] is not None else 'Unknown' for field in FEATURES}
    manifest=json.loads(manifest_path.read_text())
    allowed=manifest.get('allowed_values', {})
    unfamiliar=[field for field in FEATURES if field in allowed and values[field] not in allowed[field]]
    if unfamiliar:
        raise ValueError('Unknown official NEED category values in: '+', '.join(unfamiliar)+'. Use recorded category codes or Unknown, not invented consumer mappings.')
    frame = pd.DataFrame([values], columns=FEATURES)
    outputs = {}
    for fuel in TARGETS:
        fitted = joblib.load(OUT / f'{fuel}.joblib')
        outputs[f'{fuel}_kwh_per_year'] = round(float(np.maximum(0, fitted.predict(frame)[0])), 2)
    return {'predictions': outputs, 'input_mode': 'official_NEED_categories',
            'model_origin': 'real_UK_NEED_trained',
            'warning': 'Estimates only. Research model on anonymised 2026 NEED data; not an EPC address lookup, household bill, or verified retrofit savings.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--csv', type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(train(args.csv.expanduser()), indent=2))
