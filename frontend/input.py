"""
Accept relevant inputs and put them into a useful format.

Copyright (C) 2020 Daniel Philippus
Full copyright notice located in main.py.
"""

from default import Model
from lowlevel import runSims
from midlevel.eval import evaluate, minimized, fullEval, tests, evaluator
from midlevel.params import paramSpec, genParams
from frontend.display import evalTable, compareAllRatingCurves, nDisplay
from midlevel.data import getUSGSData, prepareUSGSData, singleStageFile
from midlevel.calibrators import nstageIteration, nstageSingleRun

from platypus import NSGAII, Problem, Real, nondominated # https://platypus.readthedocs.io/en/latest/getting-started.html#defining-constrained-problems
from urllib.request import urlopen

def parseConfigText(text, parsers):
    """
    Parse the text of a config file.  Format is Keyword: Value one per line.  Lines starting with # are
    ignored.
    :param text: the text of the config file.
    :param parsers: a dictionary of {keyword: function}, where function takes the string and returns
        the relevant value.  Lowercase keywords.
    :return: a dictionary of {keyword: value}
    """
    lines = [(line, line.index(":")) for line in text.split("\n") if not line.startswith("#")
             and not line == ""]
    # Before colon : after colon
    stringvals = { line[0][:line[1]].strip().lower() : line[0][line[1]+1:].strip() for line in lines }
    # So that values will be None if they aren't present in the file
    result = {k: None for k in parsers}
    for v in stringvals:
        if stringvals[v] != "":
            result[v] = parsers[v](stringvals[v])
    return result

def configSpecify(confPath, run = True):
    """
    Parse all of the arguments for specify and run it.
    :param confPath: path to the config file, or None to return example config file format
    :return: config values or example file format
    """
    id = lambda x: x
    toBool = lambda x: x in ["True", "true", "t", "T"]
    parsers = {
        "project": id,
        "stagef": id,
        "river": id,
        "reach": id,
        "rs": id,
        "nct": int,
        "outf": id,
        "plot": toBool,
        "auto": toBool,
        "evals": int,
        "metrics": lambda x: [i.strip() for i in x.split(",")],  # format: r2,rmse,pbias
        "filen": id,
        "slope": float,
        "usgs": id,
        "flowcount": int,
        "enddate": id,
        "startdate": id,
        "period": int
    }
    if confPath is not None:
        with open(confPath) as f:
            data = f.read()
        vals = parseConfigText(data, parsers)
        if run:
            specify(
                project=vals["project"], stagef=vals["stagef"], river=vals["river"], reach=vals["reach"],
                rs=vals["rs"], nct=vals["nct"], outf=vals["outf"], plot=vals["plot"], auto=vals["auto"],
                evals=vals["evals"], metrics=vals["metrics"], fileN=vals["filen"], slope=vals["slope"],
                usgs=vals["usgs"], flowcount=vals["flowcount"], enddate=vals["enddate"], startdate=vals["startdate"],
                period=vals["period"]
            )
        return vals
    else:
        return """
# Example configuration file.  Fill out the values below to use and run with `python main.py <path>` or
# `raspy-cal.exe <path>` to use this config file.  Comment out lines you don't want to specify with `#`
# at the start of the line; information not provided will be requested when running as needed.  Not all
# information is required, e.g. if usgs is specified stagef will be ignored.
project: C:\\PathToHECRASProject\\project.prj
stagef: C:\\PathToStagefileIfUsed\\stagefile.csv
river: South Platte River
reach: Above Confluence Park
rs: 12345.0*
nct: 10
outf: C:\\PathToOutputFile\\outfile.csv
plot: True
auto: True
evals: 100
metrics: r2,rmse,pbias
filen: 04
slope: 0.025
usgs: 09429100
flowcount: 100
enddate: 2020-02-26
startdate: 2019-02-28
period: 500
"""

def specify(project = None, stagef = None, river = None, reach = None, rs = None, nct = None, outf = None,
            plot = None, auto = None, evals = None, metrics = None, fileN = None, slope = None, usgs = None,
            flowcount = None, enddate = None, startdate = None, period = None):
    """
    Select options and decide what to do.  All arguments are requested interactively if not specified.
    :param project: project path
    :param stagef: stage file path
    :param river: river name
    :param reach: reach name
    :param rs: river station for data collection
    :param nct: how many ns to test (per generation, if auto)
    :param outf: output file path or "" not to write one
    :param plot: to plot results
    :param auto: whether to use automatic optimization with NSGAII
    :param metrics: list of metrics to use
    :param fileN: flow file number to write to
    :param slope: slope for normal depth boundary condition
    :param usgs: USGS gage to use or "" not to use
    :param flowcount: how many flows to select if using USGS data
    :param enddate: end date for USGS
    :param startdate: start date for USGS
    :param period: period for USGS
    """
    def getUSGS(usgs, flowcount, enddate, startdate, period):
        flowcount = int(input("Approx. how many flows to retrieve: ")) if flowcount is None else flowcount
        enddate = input("End date or leave blank for today: ") if enddate is None else enddate
        startdate = input("Start date or leave blank for 1 week ago or period: ") if startdate is None and\
                                                                                    (period is None or period == "")\
                                                                                    else startdate
        period = input("Period or leave blank for 1 week or start date: ") if period is None else period
        return prepareUSGSData(
            getUSGSData(usgs, enddate, startdate, period),
            flowcount
        )


    project = input("Enter project path (including .prj file): ") if project is None else project
    usgs = "" if stagef is not None else usgs
    usgs = input("USGS gage number or leave blank to use a stage file: ") if usgs is None else usgs
    if usgs == "":
        stagef = input("Enter path to stage file: ") if stagef is None else stagef
    (flow, stage) = singleStageFile(stagef) if usgs == "" else getUSGS(usgs, flowcount, enddate, startdate, period)
    outf = input("Enter output file path or nothing to not have one: ") if outf is None else outf
    fileN = input("Enter flow file number to write (default 01): ") if fileN is None else fileN
    fileN = "01" if fileN == "" else fileN
    slope = input("Enter slope for normal depth (default 0.001): ") if slope is None else slope
    slope = float(0.001) if slope == "" else float(slope)
    if metrics is None:
        metrics = [] if input("Enter Y to specify metrics: ") in ["Y", "y"] else None
        keys = list(tests.keys())
        if metrics == []:
            inp = ""
            while inp not in ["D", "d"]:
                print("Available metrics: %s" % keys)
                print("Selected metrics: %s" % metrics)
                inp = input("Enter a metric to add it or D if done: ")
                if inp in keys:
                    metrics.append(inp)
                elif inp not in ["D", "d"]:
                    print("Warning: entered metric is not an option.")
        if metrics == []:
            metrics = None
    river = input("River name: ") if river is None else river
    reach = input("Reach name: ") if reach is None else reach
    rs = input("River station: ") if rs is None else rs
    auto = input("Enter Y to use automatic calibration (default: interactive): ") in ["Y", "y"] if auto is None else auto
    plot = input("Enter N to not plot results (default: plot): ") not in ["N", "n"] if plot is None else plot
    nct = int(input("Number of n to test each iteration: ")) if nct is None else nct
    evals = int(input("How many evaluations to run? ")) if auto and evals is None else evals
    model = Model(project)
    model.params.setSteadyFlows(river, reach, rs=None, flows=flow, slope=slope, fileN=fileN)

    if not auto:
        iterate(project = project, flow=flow, stage = stage, river = river, reach = reach, rs = rs, nct = nct,
                outf = outf, model = model, plot = plot, metrics = metrics)
    if auto:
        autoIterate(model = model, river = river, reach = reach, rs = rs, flow = flow, stage = stage, nct = nct,
                    plot = plot, outf = outf, metrics = metrics, evals = evals)

def iterate(project = None, flow = None, stage = None, river = None, reach = None, rs = None, nct = None,
            rand = None, outf = None, model = None, plot = None, metrics = None):
    """
    Iterate over n options until the user narrows it down to a good choice.  Note that providing an n of 0 will
    cause HEC-RAS to crash.
    :return: final ns
    """
    project = input("Enter project path (including .prj file): ") if project is None else project
    model = Model(project) if model is None else model
    river = input("River name: ") if river is None else river
    reach = input("Reach name: ") if reach is None else reach
    rs = input("River station: ") if rs is None else rs
    nct = int(input("Enter number of n to test each iteration: ")) if nct is None else nct
    rand = input("Enter Y to use random parameter generation: ") in ["y", "Y"] if rand is None else rand
    outf = input("Enter path to write output file to or nothing to not write it: ") if outf is None else outf
    plotpath = ".".join(outf.split(".")[:-1]) + ".png"
    plot = input("Plot results? Enter N to not plot: ") not in ["n", "N"] if plot is None else plot
    cont = True
    while cont:
        nmin = float(input("Enter minimum n: "))
        nmax = float(input("Enter maximum n: "))
        best = nstageIteration(model, river, reach, rs, stage, nct, rand, nmin, nmax, metrics)
        # Show plot (if specified) but don't save anything
        nDisplay(best, flow, stage, None, None, plot)
        cont = input("Continue?  Q or q to quit and write results: ") not in ["q", "Q"]
        if not cont:
            # Save the plot and CSV
            nDisplay(best, flow, stage, plotpath, outf, False)

def autoIterate(model, river, reach, rs, flow, stage, nct, plot, outf, metrics, evals = None):
    """
    Automatically iterate with NSGA-II
    """
    keys = metrics  # ensure same order
    evalf = evaluator(stage, useTests = keys)
    evals = int(input("How many evaluations to run? ")) if evals is None else evals
    plotpath = ".".join(outf.split(".")[:-1]) + ".png"
    count = 1
    print("Running automatic calibration")
    def manningEval(vars):
        n = vars[0]
        metrics = minimized(
            nstageSingleRun(model, river, reach, rs, stage, n, keys)
        )
        values = [metrics[key] for key in keys]
        constraints = [-n, n - 1]
        nonlocal count
        print("Completed %d evaluations" % count)
        count += 1
        return values, constraints
    c_type = "<0"
    problem = Problem(1, len(keys), 2)  # 1 decision variable, len(keys) objectives, and 2 constraints
    problem.types[:] = Real(0.001, 1)  # range of decision variable
    problem.constraints[:] = c_type
    problem.function = manningEval

    algorithm = NSGAII(problem, population_size = nct)
    algorithm.run(evals)
    nondom = nondominated(algorithm.result) # nondom: list of Solutions - wanted value is variables[0]
    nondomNs = [sol.variables[0] for sol in nondom]
    results = runSims(model, nondomNs, river, reach, len(stage), range = [rs])
    resultPts = [(nondomNs[ix], [results[ix][rs][jx] for jx in range(1, len(stage) + 1)]) for ix in range(len(nondomNs))]
    metrics = [(res[0], evalf(res[1]), res[1]) for res in resultPts]
    nDisplay(metrics, flow, stage, plotpath, outf, plot)
    return metrics


def testrun():
    specify(
        project = "V:\\LosAngelesProjectsData\\HEC-RAS\\raspy\\DemoProject\\project.prj",
        stagef = "V:\\LosAngelesProjectsData\\HEC-RAS\\raspy_cal\\DemoStage.csv",
        river = "river1",
        reach = "reach1",
        rs = "200",
        # nct = 10,
        # rand = False,
        outf = "V:\\LosAngelesProjectsData\\HEC-RAS\\raspy_cal\\DemoOut.txt",
        plot = True
    )

if __name__ == "__main__":
    gn = "09423350"
    print(prepareUSGSData(getUSGSData(gn, period=365*2), log=False))







