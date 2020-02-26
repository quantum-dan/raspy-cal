"""
Accept relevant inputs and put them into a useful format.
"""

from default import Model
from lowlevel import runSims
from midlevel.eval import evaluate, minimized, fullEval, tests, evaluator
from midlevel.params import paramSpec, genParams
from frontend.display import evalTable, compareAllRatingCurves, compareRatingCurve
from platypus import NSGAII, Problem, Real, nondominated # https://platypus.readthedocs.io/en/latest/getting-started.html#defining-constrained-problems
from urllib.request import urlopen

def csv(list):
    return "\n".join([",".join(row) for row in list])

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
    stringvals = { line[0][:line[1]].strip().lower() : line[0][line[1]:].strip() for line in lines }
    # So that values will be None if they aren't present in the file
    result = {k: None for k in parsers}
    for v in stringvals:
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


def usgsURL(gage, end = None, start=None, period=None):
    """
    Generate USGS gage data url.
    :param gage: gage number
    :param start: start date (yyyy-mm-dd)
    :param end: end date
    :param period: number of days to retrieve (int)
    :return: the URL
    """
    # Period: https://nwis.waterdata.usgs.gov/ca/nwis/uv/?cb_00060=on&cb_00065=on&format=rdb&site_no=09429100&period=500&begin_date=2020-02-17&end_date=2020-02-24
    # Date range: https://waterdata.usgs.gov/ca/nwis/uv?cb_00060=on&cb_00065=on&format=rdb&site_no=09423350&period=&begin_date=2020-02-17&end_date=2020-02-24
    # format order: site_no, period, begin_date, end_date - all strings
    # Period, begin_date can each be left empty if the other is specified
    base = "https://nwis.waterdata.usgs.gov/ca/nwis/uv/?cb_00060=on&cb_00065=on&format=rdb&site_no=%s&period=%s&begin_date=%s&end_date=%s"
    start = "" if start is None else start
    period = "" if period is None else str(period)
    end = "" if end is None else end
    return base % (gage, period, start, end)

def getUSGSData(gage, end = None, start = None, period = None, urlFunc = usgsURL):
    """
    Retrieve USGS gage data for the given gage.
    :param gage: gage number
    :param end: end date (yyyy-mm-dd)
    :param start: start date
    :param period: number of days to retrieve data for
    :param urlFunc: url generator function (usually should be left as default) (arguments gage, start, end, period)
    :return: [(flow, stage)]
    """
    # identify flow and stage
    flown = "00060"
    stagen = "00065"
    url = urlFunc(gage=gage, start=start, end=end, period=period)
    with urlopen(url) as res:
        usgsBytes = res.read()
    usgs = usgsBytes.decode("utf-8")
    lines = usgs.split("\n")
    dataIx = 0
    while dataIx < len(lines):
        if lines[dataIx][0] != "#":  # Find first data line (not commented)
            break
        dataIx += 1
    rows = [l.split("\t") for l in lines[dataIx:]]
    flowcol = 0
    stagecol = 0
    for (ix, item) in enumerate(rows[0]):
        if item.endswith(flown):
            flowcol = ix
        if item.endswith(stagen):
            stagecol = ix
    return [
        # skip first 2 rows which are headers, not data, and make sure each row is long enough
        (row[flowcol], row[stagecol]) for row in rows[2:] if len(row) > stagecol
    ]

def prepareUSGSData(usgsData, flowcount = 100, log = True):
    """
    Prepare flow and stage for use.  Returns a roughly evenly distributed set of flows across the relevant
    range.
    :param usgsData: usgs data as returned by getUSGSData - [(flow, stage)]
    :param flowcount: how many flows to return
    :param log: whether to evenly distribute logarithmically (alternative: linearly)
    :return: (flows, stages)
    """
    sortedData = sorted(usgsData, key=lambda d: d[0])  # sort by flow rate
    # Range: either largest / smallest or largest * smallest
    rng = sortedData[-1][0] / sortedData[0][0] if log else sortedData[-1][0] - sortedData[0][0]
    # flowcount - 1 steps
    step = rng ** (1/(flowcount - 1)) if log else rng / (flowcount - 1)
    flow = [sortedData[0][0]]
    stage = [sortedData[0][1]]
    first = sortedData[0][0]
    vals = [first * step ** ix if log else first + step + ix for ix in range(1, flowcount)]
    ixv = 0
    for (fl, st) in sortedData:
        if fl >= vals[ixv]:
            flow.append(fl)
            stage.append(st)
            ixv += 1
        if ixv >= len(vals):
            break
    return (flow, stage)



def singleStageFile(path):
    """
    Parse a single rating curve file with flow vs stage, assuming the flows are in the order of
    flow profiles in HEC-RAS which the user has entered and that the file is a CSV with column headers
    Flow and Stage.
    """
    lines = []
    with open(path) as f:
        lines = [line for line in f]
    lines = [[i.strip() for i in line.split(",")] for line in lines]
    stage = lines[0].index("Stage")
    flow = lines[0].index("Flow")
    return ([float(i[flow]) for i in lines[1:]], [float(i[stage]) for i in lines[1:]])

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
        startdate = input("Start date or leave blank for 1 week ago or period: ") if startdate is None else startdate
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
        iterate(project = project, stage = stagef, river = river, reach = reach, rs = rs, nct = nct,
                outf = outf, model = model, plot = plot, metrics = metrics)
    if auto:
        autoIterate(model = model, river = river, reach = reach, rs = rs, flow = flow, stage = stage, nct = nct,
                    plot = plot, outf = outf, metrics = metrics, evals = evals)

def iteration(model, river, reach, rs, stage, flow, nct, rand, nmin, nmax, metrics, plot):
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
    if plot:
        compareAllRatingCurves(flow, stage, [(i[0], i[2]) for i in best])
    return best

def iterate(project = None, stage = None, river = None, reach = None, rs = None, nct = None,
            rand = None, outf = None, model = None, plot = None, metrics = None):
    """
    Iterate over n options until the user narrows it down to a good choice.  Note that providing an n of 0 will
    cause HEC-RAS to crash.
    :return: final ns
    """
    project = input("Enter project path (including .prj file): ") if project is None else project
    model = Model(project) if model is None else model
    (flow, stage) = singleStageFile(input("Enter path to stage file: ")) if stage is None else singleStageFile(stage)
    river = input("River name: ") if river is None else river
    reach = input("Reach name: ") if reach is None else reach
    rs = input("River station: ") if rs is None else rs
    nct = int(input("Enter number of n to test each iteration: ")) if nct is None else nct
    rand = input("Enter Y to use random parameter generation: ") in ["y", "Y"] if rand is None else rand
    outf = input("Enter path to write output file to or nothing to not write it: ") if outf is None else outf
    plot = input("Plot results? Enter N to not plot: ") not in ["n", "N"] if plot is None else plot
    cont = True
    while cont:
        nmin = float(input("Enter minimum n: "))
        nmax = float(input("Enter maximum n: "))
        best = iteration(model, river, reach, rs, stage, flow, nct, rand, nmin, nmax, metrics, plot)
        cont = input("Continue?  Q or q to quit and write results: ") not in ["q", "Q"]
        if (not cont) and (outf != ""):
            with open(outf, "w") as f:
                f.write(csv(evalTable([b[0] for b in best], [b[1] for b in best], string = False)))

def autoIterate(model, river, reach, rs, flow, stage, nct, plot, outf, metrics, evals = None):
    """
    Automatically iterate with NSGA-II
    """
    keys = metrics  # ensure same order
    evalf = evaluator(stage, useTests = keys)
    evals = int(input("How many evaluations to run? ")) if evals is None else evals
    count = 1
    print("Running automatic calibration")
    def manningEval(vars):
        n = vars[0]
        result = runSims(model, [n], river, reach, len(stage), range = [rs])[0][rs] # {profile: stage}
        result = [result[ix] for ix in range(1, len(stage) + 1)] # just stages
        metrics = minimized(evalf(result))
        values = [metrics[key] for key in keys]
        constraints = [-n, n - 1]
        nonlocal count
        print("Completed %d evaluations" % count)
        count += 1
        return values, constraints
    c_type = "<0"
    problem = Problem(1, len(keys), 2) # 1 decision variable, len(keys) objectives, and 2 constraints
    problem.types[:] = Real(0.001, 1) # range of decision variable
    problem.constraints[:] = c_type
    problem.function = manningEval

    algorithm = NSGAII(problem, population_size = nct)
    algorithm.run(evals)
    nondom = nondominated(algorithm.result) # nondom: list of Solutions - wanted value is variables[0]
    nondomNs = [sol.variables[0] for sol in nondom]
    results = runSims(model, nondomNs, river, reach, len(stage), range = [rs])
    resultPts = [(nondomNs[ix], [results[ix][rs][jx] for jx in range(1, len(stage) + 1)]) for ix in range(len(nondomNs))]
    metrics = [(res[0], evalf(res[1])) for res in resultPts]
    table = evalTable([m[0] for m in metrics], [m[1] for m in metrics])
    print(table)
    if outf != "":
        with open(outf, "w") as f:
            f.write(csv(evalTable([m[0] for m in metrics], [m[1] for m in metrics], string = False)))
        print("Results written to file %s" % outf)
    if plot:
        compareAllRatingCurves(flow, stage, resultPts)
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
    print(getUSGSData(gn)[:100])







