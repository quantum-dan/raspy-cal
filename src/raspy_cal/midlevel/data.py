"""
Data support functionality like retrieving USGS gage data and parsing stage files.

Copyright (C) 2020 Daniel Philippus.
Full copyright notice in main.py.
"""

from urllib.request import urlopen


def usgsURL(gage, end=None, start=None, period=None):
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


def getUSGSData(gage, end=None, start=None, period=None, urlFunc=usgsURL, si=False):
    """
    Retrieve USGS gage data for the given gage.
    :param gage: gage number
    :param end: end date (yyyy-mm-dd)
    :param start: start date
    :param period: number of days to retrieve data for
    :param urlFunc: url generator function (usually should be left as default) (arguments gage, start, end, period)
    :param si: if true, convert data from cfs/ft to cms/m
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
    volfactor = (12 / 39.37) ** 3 if si else 1
    stagefactor = 12 / 39.37 if si else 1
    return [
        # skip first 2 rows which are headers, not data, and make sure each row is long enough
        (float(row[flowcol]) * volfactor,
         float(row[stagecol])) * stagefactor for row in rows[2:] if len(row) > stagecol and
                                                                    len(row) > flowcol and
                                                                    len(row[flowcol]) > 0 and
                                                                    len(row[stagecol]) > 0
    ]


def prepareUSGSData(usgsData, flowcount=100, log=True):
    """
    Prepare flow and stage for use.  Returns a roughly evenly distributed set of flows across the relevant
    range.
    :param usgsData: usgs data as returned by getUSGSData - [(flow, stage)]
    :param flowcount: how many flows to return
    :param log: whether to evenly distribute logarithmically (alternative: linearly)
    :return: (flows, stages)
    """
    sortedData = sorted([u for u in usgsData if u[0] > 0], key=lambda d: d[0])  # sort by flow rate
    # Range: either largest / smallest or largest * smallest
    rng = sortedData[-1][0] / sortedData[0][0] if log else sortedData[-1][0] - sortedData[0][0]
    # flowcount - 1 steps
    step = rng ** (1 / (flowcount - 1)) if log else rng / (flowcount - 1)
    flow = [sortedData[0][0]]
    if flow[0] < 0.1:
        flow[0] = 0.1
    stage = [sortedData[0][1]]
    first = sortedData[0][0]

    # To avoid overlong numbers, since the HEC-RAS flow files are fixed-width, PyRASFile rounds to 1 decimal place
    first = first if first >= 0.1 else 0.1
    vals = [first * step ** ix if log else first + step + ix for ix in range(1, flowcount)]
    vals = [round(val, 1) for val in vals]
    vals = sorted(list(set(vals)))  # Only unique values, since rounding might introduce duplicates
    ixv = 0
    for (fl, st) in sortedData:
        if fl >= vals[ixv] and fl > flow[-1]:  # Make sure it's also greater than previous - no point in duplicates
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
