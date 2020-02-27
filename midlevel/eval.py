"""
Evaluation of parameter sets, i.e. goodness of fit.

Copyright (C) 2020 Daniel Philippus
Full copyright notice located in main.py.
"""

import HydroErr as he
import scipy.stats as sp

def pbias(sim, obs):
    length = len(sim) if len(sim) <= len(obs) else len(obs)
    return 100 * sum([sim[i] - obs[i] for i in range(length)]) / sum(obs[:length])

# Just to have a list of potentially useful tests
# Values are functions taking (simulated, observed) lists (this convention taken from HydroErr) and returning
# the statistic
tests = {
    "r2": he.r_squared,
    "pbias": pbias,
    "rmse": he.rmse,
    "ks_pval": lambda sim, obs: sp.ks_2samp(sim, obs)[1],  # p-value for the null hypothesis (higher is better)
    "ks_stat": lambda sim, obs: sp.ks_2samp(sim, obs)[0],  # ks statistic (smaller is better)
    "paired": lambda sim, obs: sp.ttest_rel(sim, obs)[1],  # p-value (higher is better)
    "mae": he.mae,
    "nse": he.nse
}

# Functions to adjust the above test results so that smaller is better
minimizers = {
    "r2": lambda r2: -r2,
    "pbias": lambda pb: abs(pb),
    "rmse": lambda rmse: rmse,
    "ks_pval": lambda p: -p,
    "ks_stat": lambda ks: ks,
    "paired": lambda p: -p,
    "mae": lambda mae: mae,
    "nse": lambda nse: -nse
}

def minimized(metrics):
    """
    Adjust the given metrics so that smaller is better.
    :param metrics: dictionary of {test: result} from tests
    """
    return {
        test: minimizers[test](metrics[test]) for test in metrics
    }

def fullEval(sim, obs):
    """
    Return all comparison stats
    """
    return {
        test: tests[test](sim, obs) for test in tests
    }

def evaluator(obs, useTests = None, correctDatum = True):
    """
    Return a function which will return either all (if tests is None) or selected comparison
    stats for a set of simulated values, given the set of observed values.
    :param useTests: list of strings (test names) or None
    :param correctDatum: whether to adjust the datum between obs and sim
    """

    def adjustDatum(sim):
        if not correctDatum:
            return sim
        obs_s = sorted(obs)
        sim_s = sorted(sim)
        count = len(obs) // 20 + 1  # Bottom 5%, +1 in case len(obs) < 20
        adj = (sum(obs_s[:count]) - sum(sim_s[:count])) / count  # Average difference
        return [s + adj for s in sim]

    if useTests is None:
        return lambda sim: fullEval(adjustDatum(sim), obs)
    else:
        return lambda sim: {test: tests[test](adjustDatum(sim), obs) for test in useTests}

def nonDominated(points):
    """
    Return the entries which are not dominated, i.e. there is no entry which is better than them in every metric.
    For NSGA-II, this is part of the algorithm which will presumably be provided by a library.  However, it may
    also be useful to look at non-dominated solutions in semi-manual mode, in which case it is necessary to provide
    a non-domination function.
    :param points: a list of tuples of (value, metrics), metrics should be a list in the same order for all.
        Metrics must all be "lower is better"
    :return: the same format as points, but only those which are non-dominated
    """

    nondom = []
    metrics = [point[1] for point in points]

    for (ix, metric) in enumerate(metrics):
        dominated = False
        for (jx, metric2) in enumerate(metrics):
            if jx != ix:  # Not the same point
                # Dominated if there are no values for which metric is not greater than metric 2
                dominated = False not in [metric[zx] > metric2[zx] for zx in range(len(metric))]
                if dominated:
                    break
        if not dominated:
            nondom.append(points[ix])
    return nondom

def best(points):
    """
    Return the entry which is the best (has the lowest metric).
    :param points: A list of tuples of (value, metric).  Metric must be lower is better
    :return: The best point
    """
    best = None if len(points) == 0 else points[0]
    for point in points:
        if point[1] < best[1]:
            best = point
    return best

def bestN(points, n):
    """
    Return the best n entries (lowest metric), sorted from best to worst
    :param points: A list of tuples of (value, metric).  Metric must be lower is better
    :param n: How many points to return
    :return: A list of the best n points
    """
    if (n == 1):
        return [best(points)]
    else:
        n = n if n <= len(points) else len(points)
        return sorted(points, key = lambda p: p[1])[:n]

def evaluate(obs, sims, metrics = None, useBest = None, usePareto = True, n = 10):
    """
    Evaluate the simulations against obs using the given tests (all if None).  If useBest is specified, get the best
    n based on whatever useBest is.  If usePareto and there are multiple metrics, get the non-dominated results.  If
    usePareto is True and useBest is specified, and there are multiple metrics, then the non-dominated results will
    be passed into the best evaluation.  If there is more than one metric, then either usePareto must be True or useBest
    must be specified.  If there is only one metric, then both usePareto and useBest are ignored and the best n results
    based on the one metric are returned.  Note that the metrics returned are the minimized versions.
    :param obs: observed list
    :param sims: list of (parameters, simulated result).  Simulated result must correspond to obs
    :param metrics: list of metric names to use as specified in the tests dictionary, or None to use all of them
    :param useBest: which metric to sort by, or None not to sort further if usePareto is True
    :param usePareto: whether to only return non-dominated results (including for sorting, if useBest is specified)
    :param n: how many results to return if useBest is specified or if there is only one metric
    :return: list of (parameters, metrics, sim), sorted if useBest is specified, or just one (parameters, metrics)
        if n == 1
    """
    evtr = evaluator(obs, metrics)
    evalf = lambda sim: (sim[0], minimized(evtr(sim[1])), sim[1])
    evaled = [evalf(sim) for sim in sims]
    if (metrics is not None) and (len(metrics) == 1):
        working = bestN([(pt[0], pt[1][metrics[0]], pt[2]) for pt in evaled], n)
        return [(pt[0], evtr(pt[2]), pt[2]) for pt in working]
    else:
        keys = metrics if metrics is not None else list(tests.keys())  # So that the metrics will be in the same order
        working = [(pt[0], [pt[1][key] for key in keys], pt[2]) for pt in evaled]
        if usePareto:
            working = nonDominated(working)
        if useBest is not None:
            keyx = keys.index(useBest)
            working = [(pt[0], pt[1][keyx], pt[2]) for pt in working]  # Only use the one metric
            working = bestN(working, n)
        return [(pt[0], evtr(pt[2]), pt[2]) for pt in working]


if __name__ == "__main__":
    obs = [1,2,4,8,16]
    sims = [
        (1, [1,2,3,4,5]),
        (2, [1,3,6,7,20]),
        (3, [16, 8, 4, 2, 1])
    ]
    print(evaluate(obs, sims))
    print(evaluate(obs, sims, useBest = "pbias", n = 1))
    print(evaluate(obs, sims, metrics = ["r2", "pbias"]))


