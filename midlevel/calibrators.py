"""
Non-interactive components of calibration functions.

Copyright (C) 2020 Daniel Philippus.
Full copyright notice located in main.py.
"""

from midlevel.params import paramSpec, genParams
from midlevel.eval import evaluate
from frontend.display import evalTable, compareAllRatingCurves
from lowlevel import runSims

def nstageIteration(model, river, reach, rs, stage, flow, nct, rand, nmin, nmax, metrics, plot):
    """
    Run one test.
    :param model: HEC-RAS model
    :param river: river name
    :param reach: reach name
    :param rs: river station
    :param stage: list of stages
    :param flow: list of flows
    :param nct: number of ns to test
    :param rand: whether to use random ns
    :param nmin: minimum n
    :param nmax: maximum n
    :param metrics: list of metrics to use
    :param plot: whether to plot results
    :return: [(n, metrics, sim)]
    """
    pspec = paramSpec("n", nmin, nmax, nct, rand)
    ns = genParams([pspec], dicts=False)
    ns = [round(n, 3) for n in ns]  # 3 decimal places should be sufficient, since ns < 0.001 seem to not have much effect anyway
    print("Using ns: %s" % ns)
    results = runSims(model, ns, river, reach, len(stage), range=[rs])
    # Complication below: results is a dictionary of {rs: {profile number: stage}}
    resultPts = [(ns[ix], [results[ix][rs][jx] for jx in range(1, len(stage) + 1)]) for ix in range(len(ns))]
    best = evaluate(stage, resultPts, metrics=metrics, n=len(ns)//5)  # [(parameters, metrics, sim)]
    table = evalTable([b[0] for b in best], [b[1] for b in best])
    print(table)
    compareAllRatingCurves(flow, stage, [(i[0], i[2]) for i in best], plot)
    return best


