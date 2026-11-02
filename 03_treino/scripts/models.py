"""Algorithms, resampling and fit/predict (pilot 4-Coleta_egit/scripts/s09_train.py, with its approved fixes).

Kept from cpmp/pilot: RF, DT, LR, MLP with the same hyperparameters; NONE/ROS/SMOTE/ADA; MinMaxScaler fitted on the
training data only; test values clipped to [-1, 2]; resampling only on the training data; random_state = seed.
Added (PLANO_TREINO.md, seção 6): XGBoost, LightGBM and linear SVM with library defaults and class balancing equivalent
to class_weight='balanced' (XGBoost: scale_pos_weight = negatives/positives of the resampled training data).
Everything in float64, as in the pilot (storage, scaling, resampling, fitting): float32 at any of these steps changed
tree splits and kNN neighbours (e.g. DT/ADASYN, AUC +-0.03); see validacao/EQUIVALENCIA_PILOTO.md.
"""
import numpy as np
from imblearn.over_sampling import ADASYN, SMOTE, RandomOverSampler
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import MinMaxScaler
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier


def make_model(alg, seed, threads, ytr):
    if alg == 'RandomForest':
        return RandomForestClassifier(random_state=seed, class_weight='balanced', n_estimators=100, n_jobs=threads)
    if alg == 'DT':
        return DecisionTreeClassifier(random_state=seed, class_weight='balanced')
    if alg == 'LogisticRegression':
        return LogisticRegression(solver='lbfgs', random_state=seed, class_weight='balanced', max_iter=1000)
    if alg == 'MLP':
        return MLPClassifier(random_state=seed)
    if alg == 'LinearSVC':
        return LinearSVC(random_state=seed, class_weight='balanced')
    if alg == 'XGBoost':
        from xgboost import XGBClassifier
        pos = int(ytr.sum())
        return XGBClassifier(n_estimators=100, tree_method='hist', random_state=seed, n_jobs=threads,
                             scale_pos_weight=(len(ytr) - pos) / max(pos, 1), eval_metric='logloss')
    if alg == 'LightGBM':
        from lightgbm import LGBMClassifier
        return LGBMClassifier(random_state=seed, class_weight='balanced', n_jobs=threads, deterministic=True,
                              force_col_wise=True, verbose=-1)
    raise ValueError(f'algoritmo desconhecido: {alg}')


def resample(rs, X, y, seed):
    if rs == 'NONE':
        return X, y
    sampler = {'ROS': RandomOverSampler, 'SMOTE': SMOTE, 'ADA': ADASYN}[rs](random_state=seed)
    return sampler.fit_resample(X, y)


def fit_predict(alg, rs, Xtr, ytr, Xte, seed, threads, log=print):
    """Returns (hard predictions, continuous score, fitted model, info). The score is predict_proba[:, 1], or the
    decision function for LinearSVC (ranking metrics only need an order)."""
    Xtr = np.asarray(Xtr, dtype=np.float64)
    scaler = MinMaxScaler().fit(Xtr)
    Xtr_s = scaler.transform(Xtr)
    del Xtr
    Xte_s = np.clip(scaler.transform(np.asarray(Xte, dtype=np.float64)), -1, 2)
    Xr, yr = resample(rs, Xtr_s, ytr, seed)
    info = {'linhas_treino_reamostrado': int(len(yr)), 'positivos_treino_reamostrado': int(yr.sum())}
    log(f'  treino reamostrado: {len(yr)} linhas, {int(yr.sum())} positivos')
    del Xtr_s
    model = make_model(alg, seed, threads, yr)
    model.fit(Xr, yr)
    del Xr, yr
    pred = model.predict(Xte_s)
    score = model.decision_function(Xte_s) if alg == 'LinearSVC' else model.predict_proba(Xte_s)[:, 1]
    if alg in ('LogisticRegression', 'MLP', 'LinearSVC') and hasattr(model, 'n_iter_'):
        it = model.n_iter_
        info['iteracoes'] = int(np.max(it))
        max_iter = model.get_params().get('max_iter')
        info['convergiu'] = bool(np.max(it) < max_iter) if max_iter else None
    return np.asarray(pred).astype(np.int8), np.asarray(score, dtype=np.float32), model, info


def importances(model, columns):
    if hasattr(model, 'feature_importances_'):
        v = np.asarray(model.feature_importances_, dtype=float)
    elif hasattr(model, 'coef_'):
        v = np.asarray(model.coef_, dtype=float).ravel()
    else:
        return None
    return dict(zip(columns, v.tolist()))
