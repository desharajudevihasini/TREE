"""Stratified error audit on the already-evaluated NEED holdout predictions.

Predictions are joined only to the original *order-preserved held-out row indices*.
This is analysis of model errors, NOT an additional model-selection step.
"""
from __future__ import annotations
from pathlib import Path
import argparse,json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from ml.need_challenger import TARGETS

ROOT=Path(__file__).resolve().parents[1]

def run(csv:Path, predictions:Path=ROOT/'evaluation/need_challenger_predictions.csv', output:Path=ROOT/'evaluation/need_slice_analysis.json'):
    data=pd.read_csv(csv,dtype=str,low_memory=False)
    pred=pd.read_csv(predictions)
    report={'source':'Official anonymised NEED 2026 50k sample','evaluation':'Existing held-out property-only models; no retraining, no cherry-picking',
            'purpose':'Detect differences in prediction error across property types and regions; these are not protected-class fairness metrics.',
            'groups':{}}
    for fuel,(target,flag,_,_) in TARGETS.items():
        y=pd.to_numeric(data[target],errors='coerce')
        valid=data[flag].fillna('').eq('V') & y.notna() & y.ge(0)
        eligible=data.loc[valid].reset_index(drop=True)
        _,test_indices=train_test_split(np.arange(len(eligible)),test_size=.2,random_state=42)
        subset=eligible.iloc[test_indices][['PROP_TYPE','REGION','EPC']].reset_index(drop=True)
        tested=pred[(pred.fuel==fuel)&(pred['mode']=='property_only')].reset_index(drop=True)
        if len(subset)!=len(tested): raise ValueError(f'Prediction count does not match reproducible {fuel} holdout')
        subset['absolute_error_kwh']=tested['abs_error_kwh'].to_numpy()
        group={}
        for field in ['PROP_TYPE','REGION','EPC']:
            grouped=[]
            for name,g in subset.groupby(field,dropna=False):
                if len(g)<50: continue
                grouped.append({'category':str(name),'homes':int(len(g)),
                                'mae_kwh':round(float(g.absolute_error_kwh.mean()),2),
                                'p90_absolute_error_kwh':round(float(g.absolute_error_kwh.quantile(.9)),2)})
            group[field]=sorted(grouped,key=lambda x:-x['homes'])
        report['groups'][fuel]={'holdout_rows':len(tested),'mae_kwh':round(float(tested.abs_error_kwh.mean()),2),
                                'p90_absolute_error_kwh':round(float(tested.abs_error_kwh.quantile(.9)),2),
                                'categories':group}
    report['warning']='NEED features are household/property proxies and groups vary in sample size. Error slices reveal performance differences but cannot establish societal fairness or individual reliability. No calibrations or models were selected from this test audit.'
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2))
    return report

if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('--csv',required=True,type=Path)
    args=a.parse_args()
    r=run(args.csv.expanduser());print(json.dumps({'fuel_mae':{f:v['mae_kwh'] for f,v in r['groups'].items()}},indent=2))
