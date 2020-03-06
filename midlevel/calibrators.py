"""
Non-interactive components of calibration functions.

Copyright (C) 2020 Daniel Philippus.
Full copyright notice located in main.py.
"""

from midlevel.params import paramSpec, genParams
from midlevel.eval import evaluate, evaluator
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
    return multiRunner(model,
                  nstageMultiRunspec(river, reach, rs, len(stage)),
                  paramSpec("n", nmin, nmax, nct, rand),
                  nstageMultiEvaluator(stage, metrics))

def nstageSingleRun(model, river, reach, rs, stage, n, metrics):
    return singleRunner(model, nstageSingleRunspec(river, reach, rs, len(stage)),
                        {"n": n}, nstageSingleEvaluator(stage, metrics))

def nstageMultiRunspec(river, reach, rs, pcount):
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

def nstageMultiEvaluator(stage, metrics):
    """
    Generates evaluator function for roughness coefficient and stage.
    :param stage: observed stage
    :param metrics: list of metrics to use
    :return: evaluator function which returns [(n, metrics, sim)]
    """
    def evtr(result):
        return evaluate(stage, result, metrics=metrics, n=len(result)//3)
    return evtr

def nstageSingleRunspec(river, reach, rs, pcount):
    """
    Generates runspec function for a single roughness coefficient and stage.
    :param pcount: number of flow profiles
    :return: runspec function which returns simulated stage
    """
    def runspec(model, pset):
        n = pset["n"]
        result = runSims(model, [n], river, reach, pcount, range=[rs])
        return [result[0][rs][ix] for ix in range(1, pcount+1)]
    return runspec

def nstageSingleEvaluator(stage, metrics):
    """
    Generates evaluator function for roughness coefficient and stage.
    :param stage: observed stage
    :param metrics: list of metrics to use
    :return: metrics dictionary
    """
    return evaluator(stage, metrics)

def multiRunner(model, runspec, pspec, evaluator):
    """
    Generic iteration function independent of the internal details of runspec, pspec, and evaluator.
    For use with interactive mode (see nstageRunspec).
    :param model: model as required by runspec
    :param runspec: function accepting arguments model and pspec to run tests as specified
    :param pspec: parameter specification required by runspec, returned by paramSpec
    :param evaluator: evaluator function that takes runspec results and returns a list of the best results:
        [(result, metrics dictionary, ...)] (further results [...] optional, e.g. stage timeseries)
    :return: results from evaluator
    """
    results = runspec(model, pspec)
    return evaluator(results)

def singleRunner(model, runspec, pset, evaluator):
    """
    Generic single-parameter-test function independent of the internal details of runspec, pspec, and evaluator.
    For use with automatic mode.
    :param model: model
    :param runspec: function accepting arguments model and pset to run a test as specified
    :param pset: parameter or set of parameters for the run (dictionary of values)
    :param evaluator: evaluator function that takes runspec results and returns a metrics dictionary
    :return: metrics from evaluator
    """
    result = runspec(model, pset)
    return evaluator(result)



