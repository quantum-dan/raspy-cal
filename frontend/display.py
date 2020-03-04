"""
Functions to display results.

Copyright (C) 2020 Daniel Philippus
Full copyright notice located in main.py.
"""

import matplotlib.pyplot as plt


def csv(list):
    return "\n".join([",".join(row) for row in list])

def space(entry, width = 9, after = False):
    """
    Add spaces to the entry so that it is the appropriate width.  Add spaces before unless after is true.
    """
    if len(entry) < width:
        if after:
            return entry + " " * (width - len(entry))
        else:
            return " " * (width - len(entry)) + entry
    else:
        return entry

def evalTable(params, metricSets, paramName = "n", string = True):
    """
    Make a table for printing to the console of params vs metrics.
    :param params: list of the param values
    :param metricSets: list of corresponding metric sets (dictionaries of name: value)
    :param paramName: what to call the parameter
    :param string: whether to return it as a string (if not, then a list)
    :return: either a list of lists (inner lists = rows) or the table as a string
    """
    keys = list(metricSets[0].keys())
    header = [space(i) for i in [paramName] + keys] if string else [paramName] + keys
    rows = [header]
    for ix in range(len(params)):
        row = ["%.3f" % params[ix]] + ["%.3f" % metricSets[ix][k] for k in keys]
        if string:
            rows.append([space(i) for i in row])
        else:
            rows.append(row)
    if string:
        return "\n".join([" ".join(row) for row in rows])
    else:
        return rows

def nDisplay(results, flow, obs, plotpath=None, csvpath=None, plot=True):
    """
    Wrapper for displayOutputs using 1-D/Manning's n defaults.
    :param results: [(parameter, metrics, stage)]
    :param flow: flow values
    :param obs: observed stage
    :param plotpath: path to save plot
    :param csvpath: path to save CSV
    :param plot: whether to plot
    :return: list version of result table
    """
    return displayOutputs("n", results, flow, obs, "Rating Curves Comparison", "Flow (cfs)",
                          "Stage (ft)", True, True, plotpath, plot, csvpath)


def displayOutputs(paramName, results, obsX, obsY, title="", xlab="", ylab="", xlog=True, ylog=True, plotpath=None,
                   plot=True, csvpath=None):
    """
    Print metric table, show plot (if specified), and save plot (if specified).
    :param paramName: name of calibration parameter
    :param results: list of [(parameter, metrics, output list)]
    :param obsX: x values (e.g. flow) for plotting
    :param obsY: observed y values
    :param title: plot title
    :param xlab: plot x label
    :param ylab: plot y label
    :param xlog: log scale for x?
    :param ylog: log scale for y?
    :param plotpath: where to save plot or None not to
    :param csvpath: where to save CSV version of metrics table or None not to
    :param plot: whether to plot
    :return: list version of result table
    """
    (params, metrics, timeseries) = ([res[0] for res in results], [res[1] for res in results],
                                     [(res[0], res[2]) for res in results])
    stringTable = evalTable(params, metrics, paramName, True)
    listTable = evalTable(params, metrics, paramName, False)
    print(stringTable)
    if csvpath is not None:
        with open(csvpath, "w") as f:
            f.write(csv(listTable))
    if (plotpath is not None) or plot:
        compareAllRatingCurves(obsX, obsY, timeseries, plot, plotpath, paramName, title, xlab, ylab, xlog, ylog)
    return listTable



def compareRatingCurve(flows, obs, sim):
    plt.plot(flows, obs, label = "Observed")
    plt.plot(flows, sim, label = "Simulated")
    plt.xlabel("Flow (cfs)")
    plt.ylabel("Depth (ft)")
    plt.legend()
    plt.show()

# see https://matplotlib.org/3.1.0/api/markers_api.html
markers = [c for c in ".ov^<>1234sP*+xXDd|_"] + ["$%s$" % (chr(c + ord("A"))) for c in range(26)]

def compareAllRatingCurves(x, obs, sims, display=True, path=None, paramName="n",
                           title="Rating Curves Comparison", xlab="Flow (cfs)",
                           ylab="Depth (ft)", xlog=True, ylog=True):
    """
    Compare all provided rating curves.  Default arguments are depth vs flow calibrating n.
    :param x: list of x variable
    :param obs: list of observed y variable
    :param sims: list of (parameter, [simulated ys])
    :param display: whether to show the plot
    :param path: where to save the plot, or None not to
    :param paramName: name of parameter (for legend)
    """
    plt.plot(x, obs, label = "Observed")
    for (ix, (par, sim)) in enumerate(sims):
        plt.plot(x, sim, label = "Simulated (%s = %.3f)" % (paramName, par), marker=markers[ix % len(markers)])
    if xlog:
        plt.xscale("log")
    if ylog:
        plt.yscale("log")
    plt.xlabel(xlab)
    plt.ylabel(ylab)
    plt.title(title)
    plt.legend()
    if path is not None:
        plt.savefig(path)
    if display:
        plt.show()

