"""
Accept relevant inputs and put them into a useful format.
"""

from default import Model
from lowlevel import runSims
from midlevel.eval import evaluate, minimized, fullEval, tests, evaluator
from midlevel.params import paramSpec, genParams
from frontend.display import evalTable, compareAllRatingCurves, compareRatingCurve
from platypus import NSGAII, Problem, Real, nondominated # https://platypus.readthedocs.io/en/latest/getting-started.html#defining-constrained-problems
# Note: above uses local clone of Platypus because the pip version doesn't seem to work.  This is not a long-term
# solution.

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
            plot = None, auto = None, metrics = None):
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
    """
    project = input("Enter project path (including .prj file): ") if project is None else project
    (flow, stage) = singleStageFile(input("Enter path to stage file: ")) if stagef is None else singleStageFile(stagef)
    outf = input("Enter output file path or nothing to not have one: ") if outf is None else outf
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
    model = Model(project)

    if not auto:
        iterate(project = project, stage = stagef, river = river, reach = reach, rs = rs, nct = nct,
                outf = outf, model = model, plot = plot, metrics = metrics)
    if auto:
        autoIterate(model = model, river = river, reach = reach, rs = rs, flow = flow, stage = stage, nct = nct,
                    plot = plot, outf = outf, metrics = metrics)

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
    best = evaluate(stage, resultPts, metrics=metrics)  # [(parameters, metrics, sim)]
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
                f.write(evalTable([b[0] for b in best], [b[1] for b in best], string = False))

def autoIterate(model, river, reach, rs, flow, stage, nct, plot, outf, metrics):
    """
    Automatically iterate with NSGA-II
    """
    keys = metrics  # ensure same order
    evalf = evaluator(stage, useTests = keys)
    evals = int(input("How many evaluations to run? "))
    count = 1
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
    # Minimized is the inverse of minimized
    results = runSims(model, nondomNs, river, reach, len(stage), range = [rs])
    resultPts = [(nondomNs[ix], [results[ix][rs][jx] for jx in range(1, len(stage) + 1)]) for ix in range(len(nondomNs))]
    metrics = [(res[0], evalf(res[1])) for res in resultPts]
    table = evalTable([m[0] for m in metrics], [m[1] for m in metrics])
    print(table)
    if plot:
        compareAllRatingCurves(flow, stage, resultPts)
    if outf != "":
        with open(outf, "w") as f:
            f.write(table)
        print("Results written to file %s" % outf)
    return metrics


def testrun():
    specify(
        project = "V:\\LosAngelesProjectsData\\HEC-RAS\\raspy\\DemoProject\\project.prj",
        stagef = "V:\\LosAngelesProjectsData\\HEC-RAS\\raspy_cal\\DemoStage.csv",
        river = "river1",
        reach = "reach1",
        rs = "200",
    #     nct = 10,
    #     rand = False,
        outf = "V:\\LosAngelesProjectsData\\HEC-RAS\\raspy_cal\\DemoOut.txt",
        plot = True
    )

if __name__ == "__main__":
    testrun()







