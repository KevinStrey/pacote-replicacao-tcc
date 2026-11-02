"""Step 9 - Model training (cpmp/8.traditional_ml/trad_ml.py), two protocols.

Kept from the original: feature sets model1 (structural), model2 (structural +
evolutionary), model3 (evolutionary); algorithms RF, DT, LR, MLP with the same
hyperparameters; resampling NONE/ROS/SMOTE/ADA; 70/30 with random_state=42;
10-fold stratified CV on the training set; MinMaxScaler; fillna(0).

Methodological fixes (approved by the author):
 - scaler fitted only on the training set (the original refitted it on the test set);
 - resampling only on the training data, inside each CV fold;
 - final model trained on the whole training set (the original evaluated the
   model of the last fold);
 - ROC AUC from predicted probabilities (the original used hard labels);
 - stratified split (positives ~1-2%);
 - extra metrics: PR-AUC (average precision) and MCC, suited to imbalance;
 - LogisticRegression max_iter=1000 (the default 100 does not converge).

Protocols:
 A 'random'   : random 70/30, as in cpmp.
 B 'temporal' : train on releases <= T, test on releases > T; T is the release
                where the cumulative number of rows reaches 70%.

Usage: python s09_train.py [--protocols random temporal] [--no-cv]
"""
import argparse
import time
import warnings

import numpy as np
import pandas as pd
from imblearn.over_sampling import ADASYN, SMOTE, RandomOverSampler
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score, confusion_matrix, f1_score,
                             matthews_corrcoef, roc_auc_score)
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import MinMaxScaler
from sklearn.tree import DecisionTreeClassifier

from config import DATA, RESULTS

warnings.filterwarnings('ignore')

# 'line' (CK: start line of the method in the file) removed by decision of the
# author: it has no metric meaning and acts as a method identifier.
STRUCTURAL = ['cbo', 'cboModified', 'fanin', 'fanout', 'wmc',
              'rfc', 'loc', 'returnsQty', 'variablesQty', 'parametersQty', 'methodsInvokedQty',
              'methodsInvokedLocalQty', 'methodsInvokedIndirectLocalQty', 'loopQty', 'comparisonsQty',
              'tryCatchQty', 'parenthesizedExpsQty', 'stringLiteralsQty', 'numbersQty', 'assignmentsQty',
              'mathOperationsQty', 'maxNestedBlocksQty', 'anonymousClassesQty', 'innerClassesQty',
              'lambdasQty', 'uniqueWordsQty', 'modifiers', 'logStatementsQty', 'hasJavaDoc',
              "AvgCyclomatic", "AvgCyclomaticModified", "AvgCyclomaticStrict",
              "AvgEssential", "AvgLine", "AvgLineBlank", "AvgLineCode", "AvgLineComment", "CountClassBase",
              "CountClassCoupled", "CountClassDerived", "CountDeclClass", "CountDeclClassMethod",
              "CountDeclClassVariable", "CountDeclFile", "CountDeclFunction", "CountDeclInstanceMethod",
              "CountDeclInstanceVariable", "CountDeclMethod", "CountDeclMethodAll",
              "CountDeclMethodDefault", "CountDeclMethodPrivate", "CountDeclMethodProtected",
              "CountDeclMethodPublic", "CountInput", "CountLine", "CountLineBlank", "CountLineCode",
              "CountLineCodeDecl", "CountLineCodeExe", "CountLineComment", "CountOutput", "CountPath",
              "CountSemicolon", "CountStmt", "CountStmtDecl", "CountStmtExe", "Cyclomatic",
              "CyclomaticModified", "CyclomaticStrict", "Essential", "MaxCyclomatic", "MaxCyclomaticModified",
              "MaxCyclomaticStrict", "MaxEssential", "MaxInheritanceTree", "MaxNesting",
              "PercentLackOfCohesion", "RatioCommentToCode", "SumCyclomatic", "SumCyclomaticModified",
              "SumCyclomaticStrict", "SumEssential"]
EVOLUTIONARY = ['BOM', 'TACH', 'FCH', 'LCH', 'CHO', 'FRCH', 'CHD', 'WCH', 'WCD', 'WFR', 'ATAF', 'LCA', 'LCD',
                'CSB', 'CSBS', 'ACDF']
MODELS = {'model1': STRUCTURAL, 'model2': STRUCTURAL + EVOLUTIONARY, 'model3': EVOLUTIONARY}

ALGORITHMS = {
    'RandomForest': RandomForestClassifier(random_state=42, class_weight='balanced', n_estimators=100, n_jobs=-1),
    'DT': DecisionTreeClassifier(random_state=42, class_weight='balanced'),
    'LogisticRegression': LogisticRegression(solver='lbfgs', random_state=42, class_weight='balanced',
                                             max_iter=1000),
    'MLP': MLPClassifier(random_state=42),
}
RESAMPLERS = {
    'NONE': None,
    'ROS': RandomOverSampler(random_state=42),
    'SMOTE': SMOTE(random_state=42),
    'ADA': ADASYN(random_state=42),
}


def resample(rs, X, y):
    if RESAMPLERS[rs] is None:
        return X, y
    return clone(RESAMPLERS[rs]).fit_resample(X, y)


def fit_predict(alg, rs, Xtr, ytr, Xte):
    scaler = MinMaxScaler().fit(Xtr)
    Xtr_s, Xte_s = scaler.transform(Xtr), np.clip(scaler.transform(Xte), -1, 2)
    Xr, yr = resample(rs, Xtr_s, ytr)
    model = clone(ALGORITHMS[alg]).fit(Xr, yr)
    return model.predict(Xte_s), model.predict_proba(Xte_s)[:, 1]


def scores(y, pred, proba):
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    f1_none = f1_score(y, pred, average=None, labels=[0, 1], zero_division=0)
    return {
        'F1-Score(micro)': f1_score(y, pred, average='micro'),
        'F1-Score(macro)': f1_score(y, pred, average='macro'),
        'F1-Score(weighted)': f1_score(y, pred, average='weighted'),
        'F1(class0)': f1_none[0], 'F1(class1)': f1_none[1],
        'Accuracy': accuracy_score(y, pred),
        'precision': tp / (tp + fp) if tp + fp else 0.0,
        'Sensitivity': tp / (tp + fn) if tp + fn else 0.0,
        'Specificity': tn / (tn + fp) if tn + fp else 0.0,
        'ROC AUC score': roc_auc_score(y, proba) if len(set(y)) > 1 else np.nan,
        'PR AUC (AP)': average_precision_score(y, proba) if len(set(y)) > 1 else np.nan,
        'MCC': matthews_corrcoef(y, pred),
        'tn': tn, 'fp': fp, 'fn': fn, 'tp': tp,
    }


def temporal_cut(df, frac=0.7):
    counts = df.groupby('release').size().sort_index()
    cum = counts.cumsum() / counts.sum()
    return int(cum[cum >= frac].index[0])


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--protocols', nargs='+', default=['random', 'temporal'])
    ap.add_argument('--no-cv', action='store_true')
    ap.add_argument('--algorithms', nargs='+', default=list(ALGORITHMS))
    ap.add_argument('--tag', default='')
    args = ap.parse_args()
    RESULTS.mkdir(exist_ok=True)

    df = pd.read_csv(DATA / 'egit-all-releases.csv', low_memory=False)
    feats = sorted(set(sum(MODELS.values(), [])))
    df[feats] = df[feats].apply(pd.to_numeric, errors='coerce').fillna(0)
    y_all = df['will_change'].astype(int).values
    print('dataset:', df.shape, 'positives:', y_all.sum(), f'({100 * y_all.mean():.2f}%)')

    splits = {}
    if 'random' in args.protocols:
        idx_tr, idx_te = train_test_split(np.arange(len(df)), test_size=0.30, random_state=42, stratify=y_all)
        splits['random'] = (idx_tr, idx_te, '70/30 random stratified')
    if 'temporal' in args.protocols:
        T = temporal_cut(df)
        idx_tr = np.where(df['release'] <= T)[0]
        idx_te = np.where(df['release'] > T)[0]
        splits['temporal'] = (idx_tr, idx_te, f'train releases 1..{T}, test {T + 1}..{df["release"].max()}')

    out_csv = RESULTS / f'egit-results-trad{args.tag}.csv'
    rows = []
    for proto, (idx_tr, idx_te, desc) in splits.items():
        print(f'\n=== protocol {proto}: {desc} | train={len(idx_tr)} (pos={y_all[idx_tr].sum()}) '
              f'test={len(idx_te)} (pos={y_all[idx_te].sum()})', flush=True)
        for mkey, cols in MODELS.items():
            X = df[cols].values.astype(np.float64)
            Xtr, Xte, ytr, yte = X[idx_tr], X[idx_te], y_all[idx_tr], y_all[idx_te]
            for rs in RESAMPLERS:
                for alg in args.algorithms:
                    t0 = time.time()
                    cv_auc, cv_ap = [], []
                    if not args.no_cv and proto == 'random':
                        skf = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
                        for f_tr, f_va in skf.split(Xtr, ytr):
                            _, pr = fit_predict(alg, rs, Xtr[f_tr], ytr[f_tr], Xtr[f_va])
                            cv_auc.append(roc_auc_score(ytr[f_va], pr))
                            cv_ap.append(average_precision_score(ytr[f_va], pr))
                    pred, proba = fit_predict(alg, rs, Xtr, ytr, Xte)
                    s = scores(yte, pred, proba)
                    row = {'Dataset': 'egit', 'protocol': proto, 'split': desc, 'Algoritm': alg, 'window': 0,
                           'model': mkey, 'resample': rs,
                           'cv_roc_auc_mean': np.mean(cv_auc) if cv_auc else np.nan,
                           'cv_roc_auc_std': np.std(cv_auc) if cv_auc else np.nan,
                           'cv_ap_mean': np.mean(cv_ap) if cv_ap else np.nan,
                           **s, 'seconds': round(time.time() - t0, 1)}
                    rows.append(row)
                    pd.DataFrame(rows).to_csv(out_csv, index=False)
                    print(f'{proto:8s} {mkey} {rs:5s} {alg:18s} AUC={s["ROC AUC score"]:.3f} '
                          f'AP={s["PR AUC (AP)"]:.3f} F1(1)={s["F1(class1)"]:.3f} MCC={s["MCC"]:.3f} '
                          f'cvAUC={row["cv_roc_auc_mean"]:.3f} ({row["seconds"]}s)', flush=True)
    print('results at', out_csv)
