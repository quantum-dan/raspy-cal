# -*- coding: utf-8 -*-
"""
Created on Mon May 23 13:20:06 2022

@author: dphilippus
"""

"""
Create a class that holds arguments to pass around.

Copyright (C) 2022 Daniel Philippus
Full copyright notice located in main.py.
"""

from raspy_cal.midlevel.data import (getUSGSData,
                                     prepareUSGSData, singleStageFile)
from raspy_cal.midlevel.eval import tests


class Settings(object):
    # Stores calibrator settings so that there is a consistent format
    # for passing them around instead of massive lists of arguments.
    def __init__(self):
        # Everything is None to begin with (empty object).
        self.project = None
        self.stagef = None
        self.river = None
        self.reach = None
        self.rs = None
        self.nct = None
        self.outf = None
        self.plot = None
        self.auto = None
        self.evals = None
        self.metrics = None
        self.fileN = None
        self.slope = None
        self.usgs = None
        self.flowcount = None
        self.enddate = None
        self.startdate = None
        self.period = None
        self.datum = None
        self.si = None
        self.flow = None
        self.stage = None

    def specify(self,
                project=None,
                stagef=None,
                river=None,
                reach=None,
                rs=None,
                nct=None,
                outf=None,
                plot=None,
                auto=None,
                evals=None,
                metrics=None,
                fileN=None,
                slope=None,
                usgs=None,
                flowcount=None,
                enddate=None,
                startdate=None,
                period=None,
                correctDatum=None,
                si=False
                ):
        # Set up initial settings with one call.

        # Arguments retrieved from frontend.input.specify as of
        # first writing.
        # Only overwrite settings if argument is provided.
        if project is not None:
            self.project = project
        if stagef is not None:
            self.stagef = stagef
        if river is not None:
            self.river = river
        if reach is not None:
            self.reach = reach
        if rs is not None:
            self.rs = rs
        if nct is not None:
            self.nct = nct
        if outf is not None:
            self.outf = outf
        if plot is not None:
            self.plot = plot
        if auto is not None:
            self.auto = auto
        if evals is not None:
            self.evals = evals
        if metrics is not None:
            self.metrics = metrics
        if fileN is not None:
            self.fileN = fileN
        if slope is not None:
            self.slope = slope
        if usgs is not None:
            if self.stagef is None:
                self.usgs = usgs
            else:
                self.usgs = ""
        if flowcount is not None:
            self.flowcount = flowcount
        if enddate is not None:
            self.enddate = enddate
        if startdate is not None:
            self.startdate = startdate
        if period is not None:
            self.period = period
        if correctDatum is not None:
            self.datum = correctDatum
        if si is not None:
            self.si = si

    def interactive(self):
        # Get settings from user via interactive command line usage.
        def getUSGS(usgs, flowcount, enddate, startdate, period, si):
            flowcount = int(input("Approx. how many flows to retrieve: ")
                            ) if flowcount is None else flowcount
            enddate = input(
                "End date or leave blank for today: ") if enddate is None else\
                enddate
            startdate =\
                input("Start date or leave blank for 1 week ago or period: ")\
                if startdate is None and\
                (period is None or period == "")\
                else startdate
            period = input(
                "Period or leave blank for 1 week or start date: ") if period\
                is None else period
            return prepareUSGSData(
                getUSGSData(usgs, enddate, startdate, period, si=si),
                flowcount
            )

        self.project = input(
            "Enter project path (including .prj file): ") if self.project is\
            None else self.project
        self.usgs = input(
            "USGS gage number or leave blank to use a stage file: ") if\
            self.usgs is None else self.usgs
        if self.usgs == "":
            self.stagef = input(
                "Enter path to stage file: ") if self.stagef is None else\
                self.stagef
        (self.flow, self.stage) = singleStageFile(self.stagef) if\
            self.usgs == "" else getUSGS(
            self.usgs, self.flowcount, self.enddate, self.startdate,
            self.period)
        self.outf = input(
            "Enter output file path or nothing to not have one: ") if\
            self.outf is None else self.outf
        self.fileN = input(
            "Enter flow file number to write (default 01): ") if self.fileN is\
            None else self.fileN
        self.fileN = "01" if self.fileN == "" else self.fileN
        self.slope = input(
            "Enter slope for normal depth (default 0.001): ") if self.slope is\
            None else self.slope
        self.slope = float(0.001) if self.slope == "" else float(self.slope)
        if self.metrics is None:
            self.metrics = [] if input("Enter Y to specify metrics: ") in [
                "Y", "y"] else None
            keys = list(tests.keys())
            if self.metrics == []:
                inp = ""
                while inp not in ["D", "d"]:
                    print("Available metrics: %s" % keys)
                    print("Selected metrics: %s" % self.metrics)
                    inp = input("Enter a metric to add it or D if done: ")
                    if inp in keys:
                        self.metrics.append(inp)
                    elif inp not in ["D", "d"]:
                        print("Warning: entered metric is not an option.")
            if self.metrics == []:
                self.metrics = None
        self.river = input(
            "River name: ") if self.river is None else self.river
        self.reach = input(
            "Reach name: ") if self.reach is None else self.reach
        self.rs = input("River station: ") if self.rs is None else self.rs
        self.auto =\
            input("Enter Y to use automatic calibration\
 (default: interactive): ") in [
                "Y", "y"] if self.auto is None else self.auto
        self.plot = input("Enter N to not plot results (default: plot): ")\
            not in [
            "N", "n"] if self.plot is None else self.plot
        self.nct = int(input("Number of n to test each iteration: ")
                       ) if self.nct is None else self.nct
        self.evals = int(input("How many evaluations to run? ")
                         ) if self.auto and self.evals is None else self.evals
        self.datum =\
            input("Enter Y to correct datum (default: no correction): ") in [
                "Y", "y"] if self.datum is None else self.datum
        self.si = input("Enter Y if HEC-RAS project and flow data are in SI\
 units (default: US customary): ") in [
            "Y", "y"] if self.si is None else self.si
