"""
Accept relevant inputs and put them into a useful format.
"""

from raspy_cal.default import Model
from raspy_cal.lowlevel import runSims
from raspy_cal.midlevel.eval import evaluate
from raspy_cal.midlevel.params import paramSpec, genParams
from raspy_cal.frontend.display import evalTable

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
    col = lines[0].index("Stage")
    return [float(i) for i in lines[col][1:]]

def iterate():
    """
    Iterate over n options until the user narrows it down to a good choice.
    :return: final ns
    """
    project = input("Enter project path (including .prj file): ")
    model = Model(project)
    stage = singleStageFile(input("Enter path to stage file: "))
    river = input("River name: ")
    reach = input("Reach name: ")
    rs = input("River station: ")
    nct = int(input("Enter number of n to test each iteration: "))
    rand = input("Enter Y or y to use random parameter generation (default: evenly spaced): ") in "yY"
    outf = input("Enter path to write output file to or nothing to not write it: ")
    cont = True
    while cont:
        nmin = float(input("Enter minimum n: "))
        nmax = float(input("Enter maximum n: "))
        pspec = paramSpec("n", nmin, nmax, nct, rand)
        ns = genParams([pspec], dicts = False)
        results = runSims(model, ns, river, reach, len(stage), range = [rs])
        # Complication below: results is a dictionary of {rs: {profile number: stage}}
        resultPts = [(ns[ix], [results[ix][rs][jx] for jx in range(1, len(stage) + 1)]) for ix in range(len(ns))]  # Type error: "float" object is not subscriptable
        best = evaluate(stage, resultPts)
        table = evalTable([b[0] for b in best], [b[1] for b in best])
        print(table)
        cont = input("Continue?  Q or q to quit and write results: ") not in "Qq"
        if (not cont) and (outf != ""):
            with open(outf, "w") as f:
                f.write(table)





