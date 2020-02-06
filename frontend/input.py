"""
Accept relevant inputs and put them into a useful format.
"""

from default import Model
from lowlevel import runSims
from midlevel.eval import evaluate
from midlevel.params import paramSpec, genParams
from frontend.display import evalTable, compareAllRatingCurves, compareRatingCurve

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

def iterate(project = None, stage = None, river = None, reach = None, rs = None, nct = None,
            rand = None, outf = None, model = None, plot = None):
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
        pspec = paramSpec("n", nmin, nmax, nct, rand)
        ns = genParams([pspec], dicts = False)
        ns = [round(n, 3) for n in ns] # 3 decimal places should be sufficient, since ns < 0.001 seem to not have much effect anyway
        print("Using ns: %s" % ns)
        results = runSims(model, ns, river, reach, len(stage), range = [rs])
        # Complication below: results is a dictionary of {rs: {profile number: stage}}
        resultPts = [(ns[ix], [results[ix][rs][jx] for jx in range(1, len(stage) + 1)]) for ix in range(len(ns))]
        best = evaluate(stage, resultPts) # [(parameters, metrics, sim)]
        table = evalTable([b[0] for b in best], [b[1] for b in best])
        print(table)
        if plot:
            compareAllRatingCurves(flow, stage, [(i[0], i[2]) for i in best])
        cont = input("Continue?  Q or q to quit and write results: ") not in ["q", "Q"]
        if (not cont) and (outf != ""):
            with open(outf, "w") as f:
                f.write(table)

def testrun():
    iterate(
        project = "V:\\LosAngelesProjectsData\\HEC-RAS\\raspy\\DemoProject\\project.prj",
        stage = "V:\\LosAngelesProjectsData\\HEC-RAS\\raspy_cal\\DemoStage.csv",
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







