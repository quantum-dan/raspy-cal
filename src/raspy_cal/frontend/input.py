"""
Accept relevant inputs and put them into a useful format.

Copyright (C) 2020-2022 Daniel Philippus
Full copyright notice located in main.py.
"""

from raspy_cal.default import Model
from raspy_cal.lowlevel import runSims
from raspy_cal.midlevel.eval import evaluate, minimized, fullEval, tests, evaluator
from raspy_cal.midlevel.params import paramSpec, genParams
from raspy_cal.frontend.display import evalTable, compareAllRatingCurves, nDisplay
from raspy_cal.midlevel.data import getUSGSData, prepareUSGSData, singleStageFile
from raspy_cal.midlevel.calibrators import nstageIteration, nstageSingleRun
from raspy_cal.settings import Settings

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

def configSpecify(confPath, settings, run = True):
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
        "period": int,
        "si": toBool,
        "datum": toBool
    }
    if confPath is not None:
        with open(confPath) as f:
            data = f.read()
        vals = parseConfigText(data, parsers)
        if run:
            settings.specify(
                project=vals["project"], stagef=vals["stagef"], river=vals["river"], reach=vals["reach"],
                rs=vals["rs"], nct=vals["nct"], outf=vals["outf"], plot=vals["plot"], auto=vals["auto"],
                evals=vals["evals"], metrics=vals["metrics"], fileN=vals["filen"], slope=vals["slope"],
                usgs=vals["usgs"], flowcount=vals["flowcount"], enddate=vals["enddate"], startdate=vals["startdate"],
                period=vals["period"], si=vals["si"], correctDatum=vals["datum"]
            )
            settings.interactive()
            return settings
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
si: False
"""


def run(settings):
    auto = settings.auto
    if auto:
        autoIterate(settings)
    else:
        iterate(settings)


def iterate(settings, model=None, rand=None):
    """
    Iterate over n options until the user narrows it down to a good choice.
    Note that providing an n of 0 will
    cause HEC-RAS to crash.
    :return: final ns
    """
    model = Model(settings.project) if model is None else model
    rand = input("Enter Y to use random parameter generation: ") in ["y", "Y"]\
        if rand is None else rand
    plotpath = ".".join(settings.outf.split(".")[:-1]) + ".png"
    cont = True
    while cont:
        nmin = float(input("Enter minimum n: "))
        nmax = float(input("Enter maximum n: "))
        best = nstageIteration(model,
                               settings.river,
                               settings.reach,
                               settings.rs,
                               settings.stage,
                               settings.nct,
                               rand,
                               nmin,
                               nmax,
                               settings.metrics,
                               settings.datum)
        # Show plot (if specified) but don't save anything
        nDisplay(best, settings.flow, settings.stage, None, None,
                 settings.plot, settings.datum, settings.si)
        cont = input("Continue?  Q or q to quit and write results: ")\
            not in ["q", "Q"]
        if not cont:
            # Save the plot and CSV
            nDisplay(best, settings.flow, settings.stage,
                     plotpath, settings.outf, False, settings.datum,
                     settings.si)


def autoIterate(settings, model=None):
    """
    Automatically iterate with NSGA-II
    """
    keys = settings.metrics  # ensure same order
    evalf = evaluator(settings.stage,
                      useTests=keys,
                      correctDatum=settings.datum)
    plotpath = ".".join(settings.outf.split(".")[:-1]) + ".png"
    count = 1
    print("Running automatic calibration")

    def manningEval(vars):
        n = vars[0]
        metrics = minimized(
            nstageSingleRun(model,
                            settings.river,
                            settings.reach,
                            settings.rs,
                            settings.stage,
                            n,
                            keys,
                            settings.datum)
        )
        values = [metrics[key] for key in keys]
        constraints = [-n, n - 1]
        nonlocal count
        print("Completed %d evaluations" % count)
        count += 1
        return values, constraints
    c_type = "<0"
    # 1 decision variable, len(keys) objectives, and 2 constraints
    problem = Problem(1, len(keys), 2)
    problem.types[:] = Real(0.001, 1)  # range of decision variable
    problem.constraints[:] = c_type
    problem.function = manningEval

    algorithm = NSGAII(problem, population_size=settings.nct)
    algorithm.run(settings.evals)
    # nondom: list of Solutions - wanted value is variables[0]
    nondom = nondominated(algorithm.result)
    nondomNs = [sol.variables[0] for sol in nondom]
    results = runSims(model, nondomNs, settings.river,
                      settings.reach, len(settings.stage),
                      range=[settings.rs])
    resultPts = [(nondomNs[ix], [results[ix][settings.rs][jx] for jx in range(
        1, len(settings.stage) + 1)]) for ix in range(len(nondomNs))]
    metrics = [(res[0], evalf(res[1]), res[1]) for res in resultPts]
    nDisplay(metrics, settings.flow, settings.stage, plotpath,
             settings.outf, settings.plot, settings.datum, settings.si)
    return metrics
