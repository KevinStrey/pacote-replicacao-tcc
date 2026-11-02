"""Consolidates the job results into tables and a report (run after each phase; cheap to repeat).

Outputs in resultados/:
  resultados_teste.csv   one row per configuration evaluated on the test set (all phases/variants); for the random
                         protocol, mean/std of the CV folds of the same configuration (cv_*)
  cv_partes.csv          one row per CV fold
  por_feature.csv        test metrics per feature (same global model)
  importancias.csv       feature importances / coefficients
  bootstrap_ic.csv       95% bootstrap intervals (PR-AUC, ROC-AUC, MCC) of the best configuration of each
                         protocol x algorithm (principal) and of the configurations used in phase 3
  sensibilidade.csv      phase 3: main model on the full test set, main model restricted to the variant's test rows,
                         variant model, and the paired difference (variant - main, same rows, same resamples)
  nivel_feature_resumo.csv       feature-level change proneness (temporal protocol; nivel_feature.py): Spearman and
                                 top-3 hit per configuration and measure, naive baselines, difference to persistence
  nivel_feature_por_release.csv  feature x release: real and predicted rate/volume per configuration
  nivel_feature_ranking.csv      features ordered by real mean rate vs predicted (best configuration)
  erros.csv, RELATORIO.md
Bootstrap results are cached in resultados/bootstrap/ (recomputed only when missing).
Usage: python collect_results.py --execucao principal
"""
import argparse
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
import psutil

from common import Log, Run, load_config, read_json, write_json
from metrics import Sorted, bootstrap, ci, scores
from nivel_feature import analyse as feature_level

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--execucao', default='principal', choices=['principal', 'teste_rapido'])
args = ap.parse_args()
cfg = load_config()
run = Run(args.execucao)
log = Log(run.logs / 'collect_results.log')
N_BOOT = cfg['teste_rapido']['reamostras_bootstrap'] if run.sample else cfg['bootstrap']['reamostras']
SEED = cfg['semente']
KEYS = ['fase', 'protocolo', 'variante', 'conjunto', 'reamostragem', 'algoritmo']
BOOT_DIR = run.results / 'bootstrap'
BOOT_DIR.mkdir(exist_ok=True)


def load_rows():
    tests, cvs, feats, imps = [], [], [], []
    for p in sorted(run.jobs.glob('*.json')):
        r = read_json(p)
        base = {k: r[k] for k in ['id'] + KEYS + ['parte']}
        extra = {k: r.get(k) for k in ('segundos', 'segundos_treino', 'pico_ram_gb', 'linhas_treino',
                                       'positivos_treino', 'linhas_treino_reamostrado', 'iteracoes', 'convergiu',
                                       'origem')}
        row = {**base, **r['metricas'], **extra}
        if r['parte'] == 'teste':
            tests.append(row)
            feats += [{**base, **f} for f in r.get('por_feature', [])]
            imps += [{**base, 'coluna': c, 'valor': v} for c, v in (r.get('importancias') or {}).items()]
        else:
            cvs.append(row)
    return pd.DataFrame(tests), pd.DataFrame(cvs), pd.DataFrame(feats), pd.DataFrame(imps)


def boot_task(key, items, n_boot, seed):
    """items: list of (name, y, score, pred) over the same rows."""
    models = {name: Sorted(y, s, p) for name, y, s, p in items}
    draws = bootstrap(models, len(items[0][1]), n_boot, seed)
    out = {}
    for name, d in draws.items():
        for met, v in d.items():
            out[f'{name}|{met}'] = ci(v)
    names = [n for n, *_ in items]
    if len(names) == 2:
        for met in draws[names[0]]:
            diff = draws[names[1]][met] - draws[names[0]][met]
            out[f'diferenca|{met}'] = ci(diff)
    return key, out


def preds(jid):
    z = np.load(run.preds / f'{jid}.npz')
    return z['score'], z['pred']


def main():
    t0 = time.time()
    meta = read_json(run.prep / 'meta.json')
    y_all = np.load(run.prep / 'y.npy')
    split = lambda proto, var: np.load(run.prep / 'splits' / f'{proto}__{var}__test.npy')  # noqa: E731
    tests, cvs, feats, imps = load_rows()
    if tests.empty:
        log('nenhum resultado de teste ainda')
        return
    if not cvs.empty:
        agg = cvs.groupby(KEYS).agg(cv_partes=('id', 'size'), cv_ap_media=('PR AUC (AP)', 'mean'),
                                    cv_ap_dp=('PR AUC (AP)', 'std'), cv_auc_media=('ROC AUC score', 'mean'),
                                    cv_auc_dp=('ROC AUC score', 'std'), cv_mcc_media=('MCC', 'mean'),
                                    cv_mcc_dp=('MCC', 'std'), cv_segundos=('segundos', 'sum')).reset_index()
        tests = tests.merge(agg, on=KEYS, how='left')
        cvs.to_csv(run.results / 'cv_partes.csv', index=False)
    tests = tests.sort_values(['protocolo', 'variante', 'PR AUC (AP)'], ascending=[True, True, False])
    tests.to_csv(run.results / 'resultados_teste.csv', index=False)
    feats.to_csv(run.results / 'por_feature.csv', index=False)
    imps.to_csv(run.results / 'importancias.csv', index=False)
    log(f'{len(tests)} configurações avaliadas no teste, {len(cvs)} partes de CV')

    # ---- bootstrap tasks ----
    main_rows = tests[tests.variante == 'principal']
    best = main_rows.sort_values('PR AUC (AP)', ascending=False).groupby(['protocolo', 'algoritmo']).head(1)
    tasks = {}
    for r in best.itertuples():
        te = split(r.protocolo, 'principal')
        s, p = preds(r.id)
        tasks[f'ic__{r.id}'] = [('modelo', y_all[te], s, p)]
    f3 = tests[tests.fase == 'fase3']
    for r in f3.itertuples():
        te_main, te_var = split(r.protocolo, 'principal'), split(r.protocolo, r.variante)
        s0, p0 = preds(r.origem)
        if f'ic__{r.origem}' not in tasks:
            tasks[f'ic__{r.origem}'] = [('modelo', y_all[te_main], s0, p0)]
        pos = np.searchsorted(te_main, te_var)
        assert np.array_equal(te_main[pos], te_var), 'teste da variante não é subconjunto do principal'
        s1, p1 = preds(r.id)
        tasks[f'par__{r.id}'] = [('principal_restrito', y_all[te_var], s0[pos], p0[pos]),
                                 ('variante', y_all[te_var], s1, p1)]
    results = {}
    todo = {}
    for k, items in tasks.items():
        cache = BOOT_DIR / f'{k}__B{N_BOOT}.json'
        if cache.exists():
            results[k] = read_json(cache)
        else:
            todo[k] = items
    if todo:
        workers = max(1, min(len(todo), (psutil.cpu_count() or 2) // 2, 16))
        log(f'bootstrap: {len(todo)} tarefas, {N_BOOT} reamostras, {workers} processos')
        with ProcessPoolExecutor(workers) as ex:
            futs = [ex.submit(boot_task, k, v, N_BOOT, SEED) for k, v in todo.items()]
            for f in futs:
                k, out = f.result()
                write_json(BOOT_DIR / f'{k}__B{N_BOOT}.json', out)
                results[k] = out
                log('bootstrap ok:', k)
    ic_rows = []
    for k, out in results.items():
        if not k.startswith('ic__'):
            continue
        jid = k[4:]
        r = tests[tests.id == jid].iloc[0]
        row = {**{c: r[c] for c in ['id'] + KEYS}}
        for met in ('PR AUC (AP)', 'ROC AUC score', 'MCC'):
            lo, hi = out[f'modelo|{met}']
            row.update({met: r[met], f'{met} IC95 inf': lo, f'{met} IC95 sup': hi})
        ic_rows.append(row)
    ic = pd.DataFrame(ic_rows)
    if not ic.empty:
        ic = ic.sort_values(['protocolo', 'PR AUC (AP)'], ascending=[True, False])
    ic.to_csv(run.results / 'bootstrap_ic.csv', index=False)

    sens_rows = []
    for r in f3.itertuples():
        out = results[f'par__{r.id}']
        orig = tests[tests.id == r.origem].iloc[0]
        te_var = split(r.protocolo, r.variante)
        s0, p0 = preds(r.origem)
        pos = np.searchsorted(split(r.protocolo, 'principal'), te_var)
        restr = scores(y_all[te_var].astype(int), p0[pos], s0[pos])
        for met in ('PR AUC (AP)', 'ROC AUC score', 'MCC'):
            full_ci = results.get(f'ic__{r.origem}', {}).get(f'modelo|{met}', (np.nan, np.nan))
            sens_rows.append({
                'protocolo': r.protocolo, 'configuracao': f'{r.conjunto} {r.reamostragem} {r.algoritmo}',
                'metrica': met, 'principal_teste_completo': orig[met], 'principal_IC95': f'{full_ci[0]:.4f}–{full_ci[1]:.4f}',
                'principal_restrito': restr[met],
                'principal_restrito_IC95': '{:.4f}–{:.4f}'.format(*out[f'principal_restrito|{met}']),
                'variante': tests[tests.id == r.id].iloc[0][met],
                'variante_IC95': '{:.4f}–{:.4f}'.format(*out[f'variante|{met}']),
                'diferenca_variante_menos_restrito_IC95': '{:.4f}–{:.4f}'.format(*out[f'diferenca|{met}']),
                'diferenca_inclui_zero': out[f'diferenca|{met}'][0] <= 0 <= out[f'diferenca|{met}'][1],
                'origem': r.origem, 'variante_id': r.id})
    sens = pd.DataFrame(sens_rows)
    sens.to_csv(run.results / 'sensibilidade.csv', index=False)

    # ---- feature-level change proneness (temporal, principal) ----
    fl_jobs = [r for r in (read_json(run.jobs / f'{i}.json') for i in
                           tests[(tests.protocolo == 'temporal') & (tests.variante == 'principal')].id)
               if r.get('por_feature_release')]
    fl_sum = fl_rank = pd.DataFrame()
    if fl_jobs:
        fl_sum, fl_det, fl_rank = feature_level(fl_jobs, y_all, np.load(run.prep / 'feature.npy'),
                                                np.load(run.prep / 'release.npy'), meta['features'],
                                                meta['corte_temporal'], SEED, N_BOOT)
        fl_sum.to_csv(run.results / 'nivel_feature_resumo.csv', index=False)
        fl_det.to_csv(run.results / 'nivel_feature_por_release.csv', index=False)
        fl_rank.to_csv(run.results / 'nivel_feature_ranking.csv', index=False)
        log(f'nível de feature: {len(fl_jobs)} configurações temporais analisadas')

    # ---- errors ----
    err_rows = []
    for p in sorted(run.errors.glob('*.log')):
        heads = [l for l in p.read_text(encoding='utf-8', errors='replace').splitlines() if l.startswith('##### ERRO')]
        err_rows.append({'job': p.stem, 'ocorrencias': len(heads),
                         'ultima': heads[-1].replace('##### ERRO ', '').strip(' =') if heads else ''})
    errs = pd.DataFrame(err_rows, columns=['job', 'ocorrencias', 'ultima'])
    errs.to_csv(run.results / 'erros.csv', index=False)
    status = {p.stem: read_json(p) for p in run.status.glob('fase*.json')}
    report(meta, tests, cvs, ic, sens, errs, status, fl_sum, fl_rank)
    log(f'coleta concluída em {time.time() - t0:.0f} s')


def md(df, cols, fmt=4):
    if df.empty:
        return '_(vazio)_'
    out = ['| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)]
    for _, r in df.iterrows():
        out.append('| ' + ' | '.join(f'{r[c]:.{fmt}f}' if isinstance(r[c], float) else str(r[c]) for c in cols)
                   + ' |')
    return '\n'.join(out)


def report(meta, tests, cvs, ic, sens, errs, status, fl_sum=None, fl_rank=None):
    L = [f'# Relatório do treino ({run.name})', '', f'Gerado em {time.strftime("%Y-%m-%d %H:%M:%S")} por '
         '`scripts/collect_results.py`. Plano: `PLANO_TREINO.md`.', '',
         f'- Dados: {meta["linhas"]} linhas, {meta["positivos"]} positivos; corte temporal T = {meta["corte_temporal"]}'
         + (f' (amostra {meta["amostra"]})' if meta.get('amostra') else ''),
         f'- Configurações avaliadas no teste: {len(tests)}; partes de CV: {len(cvs)}; jobs com erro registrado: '
         f'{len(errs)}', '']
    L += ['## Situação das fases', '']
    for fase, s in sorted(status.items()):
        L.append(f'- {fase}: total {s["total"]}, concluídos antes {s["ja_concluidos_antes"]}, concluídos agora '
                 f'{s["concluidos_agora"]}, pendentes {s["pendentes"]}, falhas {len(s["falhas"])} '
                 f'(atualizado {s["atualizado"]})')
    cols = ['conjunto', 'reamostragem', 'algoritmo', 'PR AUC (AP)', 'ROC AUC score', 'MCC', 'F1(class1)',
            'precision', 'Sensitivity', 'segundos']
    for proto in sorted(tests.protocolo.unique()):
        t = tests[(tests.protocolo == proto) & (tests.variante == 'principal')]
        c = cols + (['cv_ap_media', 'cv_auc_media'] if 'cv_ap_media' in t and t.cv_ap_media.notna().any() else [])
        L += ['', f'## Protocolo {proto}: 15 melhores por PR-AUC (teste)', '', md(t.head(15), c)]
    if not ic.empty:
        L += ['', '## Melhor configuração por protocolo e algoritmo (IC 95% por bootstrap)', '',
              md(ic, ['protocolo', 'algoritmo', 'conjunto', 'reamostragem', 'PR AUC (AP)', 'PR AUC (AP) IC95 inf',
                      'PR AUC (AP) IC95 sup', 'ROC AUC score', 'MCC'])]
    if not sens.empty:
        L += ['', '## Análise de sensibilidade (sem PTP, Scout e Mylyn)', '',
              md(sens, ['protocolo', 'configuracao', 'metrica', 'principal_teste_completo', 'principal_restrito',
                        'variante', 'diferenca_variante_menos_restrito_IC95', 'diferenca_inclui_zero'])]
    if fl_sum is not None and not fl_sum.empty:
        cols = ['medida', 'releases', 'spearman_medio', 'spearman_IC95_inf', 'spearman_IC95_sup', 'acerto_top3_medio']
        b = fl_sum[fl_sum.id == 'BASELINE']
        m = fl_sum[(fl_sum.id != 'BASELINE') & (fl_sum.medida == 'taxa (score_medio)')]
        m = m.sort_values('spearman_medio', ascending=False).head(10)
        L += ['', '## Nível de feature: propensão a mudança (protocolo temporal)', '',
              'Ordem das features por release de teste: previsto (agregação do modelo de métodos) x real. Detalhes em '
              '`nivel_feature_*.csv` e `scripts/nivel_feature.py`.', '', '### Previsões ingênuas (sem aprendizado)', '',
              md(b, cols), '', '### 10 melhores configurações (taxa prevista = probabilidade média)', '',
              md(m, ['conjunto', 'reamostragem', 'algoritmo'] + cols[1:] + ['dif_vs_persistencia', 'dif_IC95_inf',
                                                                            'dif_IC95_sup'])]
        if fl_rank is not None and not fl_rank.empty:
            L += ['', f'### Features: ordem real x prevista (melhor configuração: `{fl_rank.id_modelo.iloc[0]}`)', '',
                  md(fl_rank, ['feature', 'posicao_real', 'posicao_prevista', 'taxa_real_media', 'score_medio',
                               'mudancas_reais', 'mudancas_previstas', 'releases'], 5)]
    if not errs.empty:
        L += ['', '## Erros registrados (detalhes em erros/)', '', md(errs, ['job', 'ocorrencias', 'ultima'])]
    if run.sample and not tests.empty:
        allj = pd.concat([tests, cvs]) if not cvs.empty else tests
        t = allj.groupby(['algoritmo', 'reamostragem']).segundos.agg(['mean', 'max']).reset_index()
        L += ['', '## Tempos na amostra (s por job)', '',
              'Na matriz completa o tempo cresce pelo menos 1/fração (×100); para RF, SMOTE e ADASYN, mais que isso.',
              '', md(t, ['algoritmo', 'reamostragem', 'mean', 'max'], 1)]
    (run.results / 'RELATORIO.md').write_text('\n'.join(L) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
