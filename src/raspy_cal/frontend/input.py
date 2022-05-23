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

def iterate(project = None, flow = None, stage = None, river = None, reach = None, rs = None, nct = None,
            rand = None, outf = None, model = None, plot = None, metrics = None, correctDatum = None, si=False):
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
    correctDatum = input("Enter Y to correct datum (default: no correction): ") in ["Y", "y"] if correctDatum is None else correctDatum
    cont = True
    while cont:
        nmin = float(input("Enter minimum n: "))
        nmax = float(input("Enter maximum n: "))
        best = nstageIteration(model, river, reach, rs, stage, nct, rand, nmin, nmax, metrics, correctDatum)
        # Show plot (if specified) but don't save anything
        nDisplay(best, flow, stage, None, None, plot, correctDatum, si)
        cont = input("Continue?  Q or q to quit and write results: ") not in ["q", "Q"]
        if not cont:
            # Save the plot and CSV
            nDisplay(best, flow, stage, plotpath, outf, False, correctDatum, si)

def autoIterate(model, river, reach, rs, flow, stage, nct, plot, outf, metrics, correctDatum, evals = None, si=False):
    """
    Automatically iterate with NSGA-II
    """
    keys = metrics  # ensure same order
    evalf = evaluator(stage, useTests = keys, correctDatum = correctDatum)
    evals = int(input("How many evaluations to run? ")) if evals is None else evals
    plotpath = ".".join(outf.split(".")[:-1]) + ".png"
    count = 1
    print("Running automatic calibration")
    def manningEval(vars):
        n = vars[0]
        metrics = minimized(
            nstageSingleRun(model, river, reach, rs, stage, n, keys, correctDatum)
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
    nDisplay(metrics, flow, stage, plotpath, outf, plot, correctDatum, si)
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







