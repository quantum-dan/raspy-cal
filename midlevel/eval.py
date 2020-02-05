"""
Evaluation of parameter sets, i.e. goodness of fit.
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

def minimizeEval(sim, obs):
    """
    Return the full set of tests, but adjusted so that smaller is always better.
    """
    return {
        test: minimizers[test](tests[test](sim, obs)) for test in tests
    }

def fullEval(sim, obs):
    """
    Return all comparison stats
    """
    return {
        test: tests[test](sim, obs) for test in tests
    }

def evaluator(obs, useTests = None):
    """
    Return a function which will return either all (if tests is None) or selected comparison
    stats for a set of simulated values, given the set of observed values.
    :param useTests: list of strings (test names) or None
    """
    if useTests is None:
        return lambda sim: fullEval(sim, obs)
    else:
        return lambda sim: {test: tests[test](sim, obs) for test in useTests}

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
    n = n if n <= len(points) else len(points)
    return sorted(points, key = lambda p: p[1])[:n]

