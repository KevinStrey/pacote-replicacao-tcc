"""Step 8 - Feature importance (cpmp/7.preprocessing: mdi.py and information_gain.py).

MDI: ExtraTreesClassifier(n_estimators=50), 10-fold stratified, mean importance
     over the folds (as in mdi.py); random_state fixed for reproducibility.
IG : mutual_info_classif(discrete_features=True) over model2 (as in
     information_gain.py; the LeaveOneOutEncoder in the original does not change
     numeric columns).
Outputs: results/mdi_egit.csv, results/information_gain_egit.csv
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.feature_selection import mutual_info_classif
from sklearn.model_selection import StratifiedKFold

from config import DATA, RESULTS
from s09_train import MODELS

if __name__ == '__main__':
    RESULTS.mkdir(exist_ok=True)
    cols = MODELS['model2']
    df = pd.read_csv(DATA / 'egit-all-releases.csv', low_memory=False)
    X = df[cols].apply(pd.to_numeric, errors='coerce').fillna(0).values
    y = df['will_change'].astype(int).values

    imp = []
    for tr, _ in StratifiedKFold(n_splits=10, shuffle=True, random_state=42).split(X, y):
        clf = ExtraTreesClassifier(n_estimators=50, random_state=42, n_jobs=-1).fit(X[tr], y[tr])
        imp.append(clf.feature_importances_)
    imp = np.array(imp)
    mdi = pd.DataFrame({'metric': cols, 'importance_mean': imp.mean(0), 'importance_std': imp.std(0)})
    mdi['group'] = ['evolutionary' if c in MODELS['model3'] else 'structural' for c in cols]
    mdi = mdi.sort_values('importance_mean', ascending=False)
    mdi['rank'] = range(1, len(mdi) + 1)
    mdi.to_csv(RESULTS / 'mdi_egit.csv', index=False)
    print(mdi.head(15).to_string(index=False))

    ig = mutual_info_classif(X, y, discrete_features=True, random_state=42)
    igdf = pd.DataFrame({'metric': cols, 'information_gain': ig,
                         'total_occurences': (X > 0).sum(0)})
    igdf['group'] = mdi.set_index('metric').loc[cols, 'group'].values
    igdf = igdf.sort_values('information_gain', ascending=False)
    igdf['rank'] = igdf['information_gain'].rank(method='dense', ascending=False).astype(int)
    igdf.to_csv(RESULTS / 'information_gain_egit.csv', index=False)
    print(igdf.head(15).to_string(index=False))
