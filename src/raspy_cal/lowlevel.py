"""
Low-level functionality that provides the infrastructure for optimization work.  This is a fairly
simple wrapper around the provided API.  See README.md for expected API functionality.

Copyright (C) 2020 Daniel Philippus
Full copyright notice located in main.py.
"""

STAGE = 0
VELOCITY = 1
ALL = -1

def runSims(model, mannings, river, reach, nprofs, range = None, retrieve = STAGE, log = True):
    """
    Run simulations and return the data.
    :param model: model API, already initialized appropriately
    :param mannings: list of Manning's n to test.  Each n can be a dictionary, list, or number -- see README.
    :param river: river to test
    :param reach: reach to test
    :param nprofs: number of flow profiles
    :param range: list of river stations to use, if specified.  Otherwise, the whole reach
    :param retrieve: STAGE, VELOCITY or ALL (0, 1, -1 respectively).  What data to retrieve.
    :return: list of the result data in order of the params used
    """
    out = []
    count = 1
    for n in mannings:
        if log:
            print("Running iteration")
        model.params.modifyN(n, river, reach)
        model.ops.compute(wait = True)
        # Below is repetitive, but it would introduce a lot of extra complexity to make it work as a function, I think
        if retrieve == STAGE:
            if range is None:
                out.append(model.data.stage(river, reach, None, nprofs))
            else:
                out.append({rs: model.data.stage(river, reach, rs, nprofs) for rs in range})
        elif retrieve == VELOCITY:
            if range is None:
                out.append(model.data.velocity(river, reach, None, nprofs))
            else:
                out.append({rs: model.data.velocity(river, reach, rs, nprofs) for rs in range})
        else:
            if range is None:
                out.append(model.data.allFlow(river, reach, None, nprofs))
            else:
                out.append({rs: model.data.allFlow(river, reach, rs, nprofs) for rs in range})
        if log:
            print("Completed %d simulations" % count)
            count += 1
    return out


def runMultiSim(model, mannings, rivers, reaches, nprofs, ranges = None, log = True):
    """
    Run one simulation of multiple roughness coefficients at different locations
    and return the results.  Intended for use with automatic calibration.
    :param model: model API, already initialized
    :param mannings: list of Manning's n, corresponding to river/reach locations
    :param rivers: list of rivers
    :param reaches: list of reaches
    :param nprofs: number of flow profiles
    :param ranges: list of ranges of river stations to use, if specified. Otherwise, the whole reach
    :param log: log successful iteration or not
    :return: dictionary of {river: {reach: [n, [stages]]}} or {river: {reach: {rs: [n, [stages]]}}}
    """
    if log:
        print("Running multi-n iteration")
    for (ix, n) in enumerate(mannings):
        model.params.modifyN(n, rivers[ix], reaches[ix])
    model.ops.compute(wait=True)
    out = {}
    for (ix, river) in enumerate(rivers):
        reach = reaches[ix]
        n = mannings[ix]
        rng = ranges[ix] if ranges is not None else None
        if not river in out:
            out[river] = {}
        if rng is not None:
            for rs in rng:
                out[river][reach][rs] = [n, model.data.stage(river, reach, rs, nprofs)]
        else:
            out[river][reach] = [n, model.data.stage(river, reach, None, nprofs)]
    return out


