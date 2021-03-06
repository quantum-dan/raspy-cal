"""
Generate parameter combinations.  Currently, it is only intended to be used with Manning's n, but
multiple parameters could be used in the future.

Copyright (C) 2020 Daniel Philippus
Full copyright notice located in main.py.
"""

import random

def paramSpec(name, min, max, n = 10, random = False):
    """
    Specifies a parameter suitable for use in genParams.  Just doing it this way because a class
    seemed excessive.
    :param name: name of the parameter (string)
    :param min: minimum value of parameter
    :param max: maximum value of parameter
    :param n: how many variants to generate
    :param random: generate variants randomly instead of evenly spaced
    :return: just a dictionary with the above information
    """
    return {
        "name": name,
        "min": min,
        "max": max,
        "n": n,
        "random": random
    }

def mkCombs(lists):
    """
    Make all possible combinations of the elements in the lists, in order
    :param lists: list of lists
    :return: list of combinations (also a list of lists)
    """
    out = [[]]
    for l in lists:
        out = [ox + [lx] for lx in l for ox in out]
    return out

def genParams(paramSpecs, dicts = True):
    """
    Generate combinations of parameters.
    :param paramSpecs: a list of dictionaries like those generated by paramSpec()
    :param dicts: return a list of dictionaries with the parameters named, instead of just a list of lists
    :return: a list of dictionaries {name: value} of parameter combinations, or a list of lists
    """
    out = []
    plists = []
    for ps in paramSpecs:
        if ps["random"]:
            plists.append([
                random.uniform(ps["min"], ps["max"]) for _ in range(ps["n"])
            ])
        else:
            plists.append(
                [i * (ps["max"] - ps["min"]) / (ps["n"] - 1) + ps["min"] for i in range(ps["n"])]
            )
    combs = mkCombs([range(ps["n"]) for ps in paramSpecs])
    for cx in combs:
        if dicts:
            out.append({
                paramSpecs[i]["name"]: plists[i][cx[i]] for i in range(len(cx))
            })
        else:
            out.append([
                plists[i][cx[i]] for i in range(len(cx))
            ])
    if dicts or len(out[0]) > 1:
        return out
    else:
        return [i[0] for i in out] # Allows for use with a single parameter

if __name__ == "__main__":
    # For debugging
    pspecs1 = [paramSpec("a", 1, 5, 5), paramSpec("r", -5, 0, random = True)]
    pspecs2 = [paramSpec("n", 0.01, 0.1, 10, True)]
    # print(genParams(pspecs1, dicts = False))
    print(genParams(pspecs2, dicts = False))


