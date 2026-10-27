"""Honest, reproducible NEED challenger evaluation.

Two prediction tasks: (1) property descriptors available without bills,
(2) optional prior-year consumption, which is NOT a cold-start model.
Selection uses validation only; test is touched once. No test-label leakage.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ['PROP_TYPE','PROP_AGE_BAND','FLOOR_AREA_BAND','REGION','MAIN_HEAT_FUEL',
            'CONSERVATORY_FLAG','COUNCIL_TAX_BAND','EPC','LI_FLAG','CWI_FLAG','PV_FLAG']
TARGETS = {'electricity':('Econs2024','ElecValFlag2024','Econs2023','ElecValFlag2023'),
           'gas':('Gcons2024','GasValFlag2024','Gcons2023','GasValFlag2023')}

def stats(y, p):
    return {'mae_kwh':round(float(mean_absolute_error(y,p)),2),
            'rmse_kwh':round(float(np.sqrt(mean_squared_error(y,p))),2),
            'r2':round(float(r2_score(y,p)),4)}

def model(name, features, numeric):
    categorical = [c for c in features if c not in numeric]
    transformer = ColumnTransformer([
        ('categorical',Pipeline([('missing',SimpleImputer(strategy='constant',fill_value='Unknown')),
                                 ('onehot',OneHotEncoder(handle_unknown='ignore',sparse_output=False))]),categorical),
        ('numeric',SimpleImputer(strategy='median'),numeric)
    ])
    if name=='ridge': estimator=Ridge(alpha=200)
    elif name=='extra_trees': estimator=ExtraTreesRegressor(n_estimators=90,min_samples_leaf=12,max_features=0.9,random_state=42,n_jobs=-1)
    else: estimator=HistGradientBoostingRegressor(max_iter=120,max_leaf_nodes=15,l2_regularization=100,learning_rate=.06,random_state=42)
    return Pipeline([('prep',transformer),('model',estimator)])

def run(csv:Path, out:Path):
    raw=pd.read_csv(csv,dtype=str,low_memory=False)
    report={'source':'UK Government NEED 2026 anonymised 50k sample','raw_rows':len(raw),
            'design':'train 60%, validation 20%, untouched test 20%; seed 42; best validation MAE',
            'warning':'Separate NEED-trained models, not external validation of TREE synthetic-trained model. No retrofit causal effects tested.',
            'experiments':{}}
    predictions=[]
    for fuel,(target,flag,prior,priorflag) in TARGETS.items():
        y=pd.to_numeric(raw[target],errors='coerce')
        valid=raw[flag].fillna('').eq('V') & y.notna() & y.ge(0)
        for mode in ('property_only','with_prior_year_bill'):
            ok=valid.copy()
            feats=FEATURES.copy()
            nums=[]
            if mode=='with_prior_year_bill':
                previous=pd.to_numeric(raw[prior],errors='coerce')
                ok &= raw[priorflag].fillna('').eq('V') & previous.notna() & previous.ge(0)
                feats.append('prior_year_kwh');nums=['prior_year_kwh']
            frame=raw.loc[ok,FEATURES].copy().fillna('Unknown')
            if nums:frame['prior_year_kwh']=previous.loc[ok].astype(float)
            target_values=y.loc[ok].astype(float)
            idx_trainval,idx_test=train_test_split(np.arange(len(frame)),test_size=.2,random_state=42)
            idx_train,idx_val=train_test_split(idx_trainval,test_size=.25,random_state=42)
            xtr,xval,xt=frame.iloc[idx_train],frame.iloc[idx_val],frame.iloc[idx_test]
            ytr,yval,yt=target_values.iloc[idx_train],target_values.iloc[idx_val],target_values.iloc[idx_test]
            validation={}
            for candidate in ('ridge','extra_trees','hist_gradient_boosting'):
                candidate_model=model(candidate,feats,nums)
                candidate_model.fit(xtr,ytr)
                validation[candidate]=stats(yval,np.maximum(0,candidate_model.predict(xval)))
            winner=min(validation,key=lambda name:validation[name]['mae_kwh'])
            final=model(winner,feats,nums)
            final.fit(frame.iloc[idx_trainval],target_values.iloc[idx_trainval])
            pred=np.maximum(0,final.predict(xt))
            median=DummyRegressor(strategy='median').fit(frame.iloc[idx_trainval],target_values.iloc[idx_trainval])
            result={'rows':len(frame),'train_validation_rows':len(idx_trainval),'test_rows':len(idx_test),
                    'features':feats,'chosen_on_validation':winner,'validation_candidates':validation,
                    'test':stats(yt,pred),'test_median_baseline':stats(yt,median.predict(xt))}
            if nums:
                result['test_prior_year_copy_baseline']=stats(yt,xt['prior_year_kwh'].to_numpy())
            report['experiments'][f'{fuel}_{mode}']=result
            evidence=pd.DataFrame({'fuel':fuel,'mode':mode,'actual_kwh':yt.to_numpy(),
                                   'predicted_kwh':np.round(pred,2),
                                   'abs_error_kwh':np.round(np.abs(yt.to_numpy()-pred),2)})
            predictions.append(evidence)
            print(f'{fuel} / {mode}: {winner}, test MAE {result["test"]["mae_kwh"]}, median MAE {result["test_median_baseline"]["mae_kwh"]}')
    out.mkdir(parents=True,exist_ok=True)
    (out/'need_challenger_report.json').write_text(json.dumps(report,indent=2))
    pd.concat(predictions,ignore_index=True).to_csv(out/'need_challenger_predictions.csv',index=False)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--csv',type=Path,required=True)
    p.add_argument('--out',type=Path,default=ROOT/'evaluation')
    args=p.parse_args()
    run(args.csv.expanduser(),args.out)
