"""Real UK NEED, consumer-compatible cold-start model: property type and EPC band.

Not a retrofit outcomes model. Never force-map heating fuel codes, home address,
annual bills, area band thresholds, or precise EPC A/B and F/G separations.

Train 60%, validation 20%, held-out test 20% (fixed seed); validation selects
between Ridge and ExtraTrees; median baseline evaluated on identical test rows.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd, joblib
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.linear_model import Ridge
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor
from ml.need_challenger import TARGETS

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'ml'/'models'/'consumer_need'
TYPE_FROM_NEED={'Semi detached':'semi_detached','Flat':'flat','Mid terrace':'terraced',
                'End terrace':'terraced','Detached':'detached','Bungalow':'bungalow'}
ALLOWED_TYPES=sorted(set(TYPE_FROM_NEED.values()))
EPC_FROM_NEED={'A/B':'A_B','C':'C','D':'D','E':'E','F/G':'F_G','No EPC':'Unknown'}
COLUMNS=['home_type','epc_band']

def bands(consumer_type: str,epc: str | None) -> dict:
    if consumer_type not in ALLOWED_TYPES:raise ValueError('Unsupported property type: '+str(consumer_type))
    if epc not in (None,*'ABCDEFG'):raise ValueError('Unknown EPC rating')
    band= ('A_B' if epc in 'AB' else 'F_G' if epc in 'FG' else epc) if epc is not None else 'Unknown'
    return {'home_type':consumer_type,'epc_band':band}

def _prep():
    return ColumnTransformer([('categories',OneHotEncoder(handle_unknown='ignore',sparse_output=False),COLUMNS)])

def _model(name):
    estimator= (Ridge(alpha=150) if name=='ridge' else HistGradientBoostingRegressor(loss='absolute_error',max_iter=100,max_leaf_nodes=12,min_samples_leaf=100,random_state=42) if name=='quantile_boosting' else ExtraTreesRegressor(n_estimators=60,min_samples_leaf=50,random_state=42,n_jobs=-1))
    return Pipeline([('features',_prep()),('regressor',estimator)])

def _stats(y,p):
    return {'mae_kwh':round(float(mean_absolute_error(y,p)),2),
            'rmse_kwh':round(float(np.sqrt(mean_squared_error(y,p))),2),
            'r2':round(float(r2_score(y,p)),4)}

def train(csv:Path=ROOT/'data'/'public'/'anon2026_50k.csv',out:Path=OUT) -> dict:
    raw=pd.read_csv(csv,dtype=str,low_memory=False)
    features=pd.DataFrame({'home_type':raw['PROP_TYPE'].map(TYPE_FROM_NEED),
                           'epc_band':raw['EPC'].map(EPC_FROM_NEED)})
    report={'name':'TREE real NEED consumer-compatible cold-start benchmark',
            'source':'UK Government NEED 2026 anonymised 50,000-row sample (consumption year 2024)',
            'features':'home type and grouped EPC band only; no personal bills used',
            'training':'60% training, 20% validation, 20% test; fixed random_state 42; compare two models and a median baseline',
            'disclaimer':'This establishes accuracy only on held-out anonymised NEED homes with these coarse features, NOT this homeowner, specific EPC address, or retrofit outcomes.',
            'experiments':{}}
    out.mkdir(parents=True,exist_ok=True)
    predictions=[]
    for fuel,(target,flag,*_) in TARGETS.items():
        actual=pd.to_numeric(raw[target],errors='coerce')
        good=raw[flag].eq('V') & actual.notna() & actual.ge(0) & features.notna().all(axis=1)
        X=features.loc[good].reset_index(drop=True); y=actual.loc[good].astype(float).reset_index(drop=True)
        itr,ite=train_test_split(np.arange(len(y)),test_size=.2,random_state=42)
        itrain,ival=train_test_split(itr,test_size=.25,random_state=42)
        performances={}
        for model_name in ('ridge','extra_trees','quantile_boosting'):
            m=_model(model_name).fit(X.iloc[itrain],y.iloc[itrain]); pred=np.maximum(0,m.predict(X.iloc[ival]));
            performances[model_name]=_stats(y.iloc[ival],pred)
        median_train=float(np.median(y.iloc[itrain])); performances['training_median_baseline']=_stats(y.iloc[ival],np.full(len(ival),median_train))
        selected=min(performances,key=lambda k: performances[k]['mae_kwh'])
        fitted=(DummyRegressor(strategy='median') if selected=='training_median_baseline' else _model(selected)).fit(X.iloc[itr],y.iloc[itr]);
        pred=np.maximum(0,fitted.predict(X.iloc[ite]));
        baseline=DummyRegressor(strategy='median').fit(X.iloc[itr],y.iloc[itr]).predict(X.iloc[ite])
        report['experiments'][fuel]={'valid_rows':len(y),'test_rows':len(ite),'selected_on_validation':selected,
                                    'validation_candidates':performances,'test':_stats(y.iloc[ite],pred),
                                    'test_median_baseline':_stats(y.iloc[ite],baseline),
                                    'limitation':'Unseen homes have different tariffs, heating systems, occupants and weather. Coarse inputs are weak predictors; report MAE and R² honestly.'}
        joblib.dump(fitted,out/f'{fuel}.joblib')
        predictions.append(pd.DataFrame({'fuel':fuel,'source':'NEED_2026_held_out','actual_kwh':y.iloc[ite].to_numpy(),
                                        'predicted_kwh':np.round(pred,2), 'absolute_error_kwh':np.round(np.abs(y.iloc[ite].to_numpy()-pred),2)}))
    (out/'report.json').write_text(json.dumps(report,indent=2))
    pd.concat(predictions,ignore_index=True).to_csv(out/'held_out_predictions.csv',index=False)
    return report


def predict(consumer_type:str, epc_rating:str|None) -> dict:
    values=bands(consumer_type,epc_rating)
    pred={}
    for fuel in ('electricity','gas'):
        path=OUT/f'{fuel}.joblib'
        if not path.exists():raise FileNotFoundError('Train models using: python -m ml.consumer_need --train')
        m=joblib.load(path)
        pred[fuel+'_kwh']=round(max(0,float(m.predict(pd.DataFrame([values]))[0])),2)
    return {'predictions':pred,'model':'real_NEED_2026_consumer_coarse','input_groups':values,
            'limitations':'Population-level, coarse UK consumption prediction. No household-specific validation. EPC categories A/B and F/G are grouped; all end/mid terrace rows group into terraced. Heating, occupancy and roof are not in this estimator.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--train',action='store_true');parser.add_argument('--csv',type=Path,default=ROOT/'data/public/anon2026_50k.csv')
    args=parser.parse_args();print(json.dumps(train(args.csv),indent=2))
