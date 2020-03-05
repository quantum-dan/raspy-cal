"""
Non-interactive components of calibration functions.

Copyright (C) 2020 Daniel Philippus.
Full copyright notice located in main.py.
"""

from midlevel.params import paramSpec, genParams
from midlevel.eval import evaluate
from lowlevel import runSims

def nstageIteration(model, river, reach, rs, stage, nct, rand, nmin, nmax, metrics):
    """
    Run one test.
    :param model: HEC-RAS model
    :param river: river name
    :param reach: reach name
    :param rs: river station
    :param stage: list of stages
    :param nct: number of ns to test
    :param rand: whether to use random ns
    :param nmin: minimum n
    :param nmax: maximum n
    :param metrics: list of metrics to use
    :return: [(n, metrics, sim)]
    """
    return runner(model,
                  nstageRunspec(river, reach, rs, len(stage)),
                  paramSpec("n", nmin, nmax, nct, rand),
                  nstageEvaluator(stage, metrics))

def nstageRunspec(river, reach, rs, pcount):
    """
    Generates runspec function for roughness coefficient and stage.
    :param pcount: number of flow profiles
    :return: runspec function which returns [(n, simulated stage)]
    """
    def runspec(model, pspec):
        ns = [round(n, 3) for n in genParams([pspec], dicts=False)]
        results = runSims(model, ns, river, reach, pcount, range=[rs])
        return [(ns[ix], [results[ix][rs][jx] for jx in range(1, pcount + 1)]) for ix in range(len(ns))]
    return runspec

def nstageEvaluator(stage, metrics):
    """
    Generates evaluator function for roughness coefficient and stage.
    :param stage: observed stage
    :param metrics: list of metrics to use
    :return: evaluator function which returns [(n, metrics, sim)]
    """
    def evtr(result):
        return evaluate(stage, result, metrics=metrics, n=len(result)//3)
    return evtr


def runner(model, runspec, pspec, evaluator):
    """
    Generic iteration function independent of the internal details of runspec, pspec, and evaluator.
    :param model: model as required by runspec
    :param runspec: function accepting arguments model and pspec to run tests as specified
    :param pspec: parameter specification required by runspec, returned by paramSpec
    :param evaluator: evaluator function that takes runspec results and returns a list of the best results:
        [(result, metrics dictionary, ...)] (further results [...] optional, e.g. stage timeseries)
    :return: results from evaluator
    """
    results = runspec(model, pspec)
    return evaluator(results)



