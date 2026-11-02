"""Metrics: the pilot's set (s09_train.scores), per feature, and fast weighted versions for the bootstrap.

The bootstrap draws row counts w (np.bincount of n draws with replacement) and evaluates the metrics with weights w.
ROC-AUC and PR-AUC (average precision) are computed on the scores sorted once, grouping tied scores, which gives the
same values as sklearn's roc_auc_score/average_precision_score with sample_weight (checked in check_env.py).
"""
import numpy as np
from sklearn.metrics import (accuracy_score, average_precision_score, confusion_matrix, f1_score,
                             matthews_corrcoef, roc_auc_score)

MAIN = ['PR AUC (AP)', 'ROC AUC score', 'MCC', 'F1(class1)', 'precision', 'Sensitivity']


def scores(y, pred, score):
    """Same keys as the pilot (s09_train.py)."""
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    f1_none = f1_score(y, pred, average=None, labels=[0, 1], zero_division=0)
    both = len(set(np.unique(y))) > 1
    return {
        'F1-Score(micro)': f1_score(y, pred, average='micro'),
        'F1-Score(macro)': f1_score(y, pred, average='macro'),
        'F1-Score(weighted)': f1_score(y, pred, average='weighted'),
        'F1(class0)': f1_none[0], 'F1(class1)': f1_none[1],
        'Accuracy': accuracy_score(y, pred),
        'precision': tp / (tp + fp) if tp + fp else 0.0,
        'Sensitivity': tp / (tp + fn) if tp + fn else 0.0,
        'Specificity': tn / (tn + fp) if tn + fp else 0.0,
        'ROC AUC score': roc_auc_score(y, score) if both else np.nan,
        'PR AUC (AP)': average_precision_score(y, score) if both else np.nan,
        'MCC': matthews_corrcoef(y, pred),
        'tn': int(tn), 'fp': int(fp), 'fn': int(fn), 'tp': int(tp),
        'positivos': int(tp + fn), 'linhas': int(len(y)),
    }


def per_feature(y, pred, score, feat_codes, feat_names):
    rows = []
    for code in np.unique(feat_codes):
        m = feat_codes == code
        s = scores(y[m], pred[m], score[m])
        rows.append({'feature': feat_names[int(code)], **{k: s[k] for k in
                     ('linhas', 'positivos', 'PR AUC (AP)', 'ROC AUC score', 'MCC', 'F1(class1)', 'precision',
                      'Sensitivity', 'Specificity', 'tn', 'fp', 'fn', 'tp')}})
    return rows


def feature_release(y, pred, score, feat_codes, releases, feat_names, tops=(1, 5, 10)):
    """Aggregates the method predictions per feature x release (feature-level change proneness, PLANO seção 6.2).
    topoK = methods of the feature among the K% highest scores of ALL methods of that release (whole SPL).
    score_medio is the mean predicted probability (mean decision function for LinearSVC: usable only for ranking)."""
    rows = []
    for r in np.unique(releases):
        m = releases == r
        s, f = score[m], feat_codes[m]
        order = np.argsort(-s, kind='mergesort')
        flags = {}
        for k in tops:
            top = np.zeros(len(s), bool)
            top[order[:int(np.ceil(len(s) * k / 100))]] = True
            flags[k] = top
        for code in np.unique(f):
            g = f == code
            rows.append({'feature': feat_names[int(code)], 'release': int(r), 'metodos': int(g.sum()),
                         'mudancas_reais': int(y[m][g].sum()), 'score_medio': float(s[g].mean()),
                         'mudancas_previstas': int(pred[m][g].sum()),
                         **{f'topo{k}': int(flags[k][g].sum()) for k in tops}})
    return rows


class Sorted:
    """Scores sorted once (descending) with the boundaries of the tied groups."""

    def __init__(self, y, score, pred=None):
        self.order = np.argsort(-score, kind='mergesort')
        s = score[self.order]
        self.y = y[self.order].astype(np.float64)
        self.ends = np.r_[np.nonzero(np.diff(s))[0], len(s) - 1]
        self.y_raw = y
        self.pred = pred

    def metrics(self, w):
        """w: weight per row in the ORIGINAL order."""
        ws = w[self.order]
        tps = np.cumsum(ws * self.y)[self.ends]
        fps = np.cumsum(ws * (1 - self.y))[self.ends]
        P, N = tps[-1], fps[-1]
        out = {}
        if P > 0 and N > 0:
            tpr = np.r_[0, tps / P]
            fpr = np.r_[0, fps / N]
            out['ROC AUC score'] = float(np.trapezoid(tpr, fpr))
            prec = np.where(tps + fps > 0, tps / np.maximum(tps + fps, 1e-300), 1.0)
            out['PR AUC (AP)'] = float(np.sum(np.diff(np.r_[0, tps / P]) * prec))
        else:
            out['ROC AUC score'] = out['PR AUC (AP)'] = np.nan
        if self.pred is not None:
            yy, pp = self.y_raw, self.pred
            tp = float(np.sum(w * (yy == 1) * (pp == 1)))
            fp = float(np.sum(w * (yy == 0) * (pp == 1)))
            fn = float(np.sum(w * (yy == 1) * (pp == 0)))
            tn = float(np.sum(w * (yy == 0) * (pp == 0)))
            den = np.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
            out['MCC'] = float((tp * tn - fp * fn) / den) if den > 0 else 0.0
        return out


def bootstrap(models, n, n_boot, seed):
    """models: dict name -> Sorted over the SAME n rows. The same resamples are used for every model (paired), so
    differences between models can be read from the returned draws. Returns {name: {metric: array(n_boot)}}."""
    rng = np.random.default_rng(seed)
    out = {k: {} for k in models}
    for b in range(n_boot):
        w = np.bincount(rng.integers(0, n, n), minlength=n).astype(np.float64)
        for k, srt in models.items():
            for met, v in srt.metrics(w).items():
                out[k].setdefault(met, np.empty(n_boot))[b] = v
    return out


def ci(draws, alpha=0.05):
    d = np.asarray(draws)
    d = d[~np.isnan(d)]
    if not len(d):
        return np.nan, np.nan
    return float(np.quantile(d, alpha / 2)), float(np.quantile(d, 1 - alpha / 2))
