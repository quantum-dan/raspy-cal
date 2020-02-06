"""
Functions to display results.
"""

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
    header = [space(i) for i in [paramName] + keys]
    rows = [header]
    for ix in range(len(params)):
        row = ["%.3f" % params[ix]] + ["%.3f" % metricSets[ix][k] for k in keys]
        rows.append([space(i) for i in row])
    if string:
        return "\n".join([" ".join(row) for row in rows])
    else:
        return rows


