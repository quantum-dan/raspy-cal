"""
Graphical front-end.  Just some simple inputs with which to run iterate and autoIterate.

Copyright (C) 2020 Daniel Philippus
Full copyright notice located in main.py.
"""

from raspy_cal.frontend.input import autoIterate, singleStageFile, configSpecify
from raspy_cal.midlevel.data import getUSGSData, prepareUSGSData
from raspy_cal.midlevel.calibrators import nstageIteration
from raspy_cal.frontend.display import evalTable, csv, nDisplay
from raspy_cal.midlevel.eval import tests
from raspy_cal.default import Model
from raspy_cal.settings import Settings
import tkinter as tk
from tkinter import filedialog

# iteration(model, river, reach, rs, stage, flow, nct, rand, nmin, nmax, metrics, plot): [(n, metrics, sim)]
# autoIterate(model, river, reach, rs, flow, stage, nct, plot, outf, metrics, evals = None): [(n, metrics)]

defaultBase = "V:\\LosAngelesProjectsData\\HEC-RAS\\"

def browseButton(parent, f):
    return tk.Button(parent, text="Browse", command=lambda: f(filedialog.askopenfilename()))

class GUI(tk.Frame):
    def __init__(self, master, settings):
        super().__init__(master)
        self.displayed = False
        self.master = master
        self.settings = settings
        self.pack()
        self.createWidgets()

    def saveParameters(self):
        self.version = self.versionField.get()
        self.project = self.projectField.get()
        self.river = self.riverField.get()
        self.reach = self.reachField.get()
        self.rs = self.rsField.get()
        self.usgs = self.usgsField.get()
        self.stagef = self.stageField.get()
        (self.flow, self.stage) = singleStageFile(self.stagef) if self.usgs == "" else\
            prepareUSGSData(getUSGSData(self.usgs, period = 365 * 2))
        self.normalSlope = (lambda s: 0.001 if s == "" else float(s))(self.slopeField.get())
        self.fileN = (lambda n: "01" if n == "" else n)(self.fileNField.get())

        self.nct = int(self.nField.get())
        self.outf = self.outField.get()
        self.metrics = [key for key in self.keyChecks if self.keyChecks[key].get() == 1]
        self.plot = self.plotInt.get() == 1
        self.datum = self.datumInt.get() == 1
        self.si = self.siInt.get() == 1
        
        self.settings.specify(
                project=self.project,
                stagef=self.stagef,
                river=self.river,
                reach=self.reach,
                rs=self.rs,
                stage=self.stage,
                flow=self.flow,
                nct=self.nct,
                outf=self.outf,
                plot=self.plot,
                metrics=self.metrics,
                fileN=self.fileN,
                slope=self.normalSlope,
                usgs=self.usgs,
                period=365*2,
                correctDatum=self.datum,
                si=self.si,
                version=self.version)

        print("Parameters: %s" % [self.project, self.river, self.reach, self.rs, self.stagef,
                                  self.nct, self.outf, self.metrics, self.plot, self.datum])

    def mainMenu(self):
        self.iterFrame.destroy()
        self.entryFrame.pack(side="top")
        self.buttonFrame.pack(side="bottom")

    def selectRunType(self, runType):
        # runType: "auto" or "manual"
        self.saveParameters()
        self.model = Model(self.project, self.version)
        self.model.params.setSteadyFlows(self.river, self.reach, rs=None, flows=self.flow, slope=self.normalSlope,
                                         fileN=self.fileN)

        self.entryFrame.pack_forget()
        self.buttonFrame.pack_forget()
        self.iterFrame = tk.Frame(self)
        self.inputFrame = tk.Frame(self.iterFrame)
        if runType == "auto":
            self.autoInterface()
        elif runType == "manual":
            self.manualInterface()
        self.inputFrame.pack(side="top")
        self.iterFrame.pack(side="bottom")
        tk.Button(self.iterFrame, text="Return to Main Menu", command=self.mainMenu).pack(side="bottom")

    def autoInterface(self):
        self.evalsEntry = tk.Entry(self.inputFrame)
        tk.Label(self.inputFrame, text="How many evaluations to run?").grid(row=0)
        self.evalsEntry.grid(row=0, column=1)
        tk.Button(self.iterFrame, text="Run Automatic Calibration", command=self.runGenetic).pack(side="bottom")

    def manualInterface(self):
        self.nminEntry = tk.Entry(self.inputFrame)
        self.nmaxEntry = tk.Entry(self.inputFrame)
        self.randVar = tk.IntVar()
        self.randCheck = tk.Checkbutton(self.inputFrame, text="Random n distribution?", variable=self.randVar)

        fields = [
            ("Minimum n", self.nminEntry),
            ("Maximum n", self.nmaxEntry),
            ("Randomize n", self.randCheck)
        ]

        for (ix, (name, field)) in enumerate(fields):
            tk.Label(self.inputFrame, text=name).grid(row = ix)
            field.grid(row=ix, column=1)

        tk.Button(self.iterFrame, text="Run Simulations", command=self.runSims).pack(side="bottom")

    def runGenetic(self):
        print("Launching automatic calibration")
        self.evals = int(self.evalsEntry.get())
        self.settings.specify(evals=self.evals)
        # self.result = autoIterate(self.model, self.river, self.reach, self.rs,
        #                           self.flow, self.stage, self.nct, False, self.outf,
        #                           self.metrics, self.datum, self.evals, self.si)
        self.result = autoIterate(self.settings, self.model)
        self.displayResult()

    def runSims(self):
        self.nmin = float(self.nminEntry.get())
        self.nmax = float(self.nmaxEntry.get())
        self.rand = self.randVar.get() == 1
        self.result = nstageIteration(self.model, self.river, self.reach, self.rs, self.stage,
                                      self.nct, self.rand, self.nmin, self.nmax, self.metrics,
                                      self.datum)
        self.displayResult()

    def displayResult(self):
        if self.displayed:
            self.displayFrame.destroy()
        self.resultTable = evalTable([r[0] for r in self.result], [r[1] for r in self.result])
        self.displayFrame = tk.Frame(self.iterFrame)
        tk.Label(self.displayFrame, text=self.resultTable).pack(side="top")
        tk.Button(self.displayFrame, text="Save Results", command=self.writeResult).pack(side="bottom")
        self.displayFrame.pack(side="top")
        self.displayed = True
        if self.plot:
            nDisplay(self.result, self.flow, self.stage, plot=True, correctDatum=self.datum, si=self.si)

    def writeResult(self):
        self.plotpath = ".".join(self.outf.split(".")[:-1]) + ".png"
        nDisplay(self.result, self.flow, self.stage, csvpath=self.outf, plot=False, plotpath=self.plotpath,
                 correctDatum=self.datum, si=self.si)

    def loadConfig(self):
        vals = configSpecify(self.confField.get(), run=False)
        for k in self.pairs:
            self.pairs[k].delete(0, tk.END)  # clear everything so e.g. USGS gage number doesn't accidentally transfer
            if vals[k] is not None:
                self.pairs[k].insert(0, str(vals[k]))
        for k in self.boxes:
            if vals[k] is not None:
                self.boxes[k].set(int(vals[k]))

    def saveConfig(self):
        out = [[k, self.pairs[k].get()] for k in self.pairs] + [[k, str(bool(self.boxes[k].get()))] for k in self.boxes]
        file = self.confField.get()
        with open(file, "w") as f:
            f.write("\n".join([":".join(i) for i in out]))
    
    def setVal(self, entry):
        def setter(val):
            entry.delete(0, tk.END)
            entry.insert(0, val)
        return setter
            
    def browseField(self, parent):
        def setVal(entry, val):
            entry.delete(0, tk.END)
            entry.insert(0, val)
        browseFrame = tk.Frame(parent)
        entry = tk.Entry(browseFrame, width=100)
        browse = tk.Button(text="Browse", command=lambda: setVal(entry, tk.filedialog.askdirectory()))
        entry.grid(column=0, row=0)
        browse.grid(column=1, row=0)
        
        return (browseFrame, entry, browse)

    def createWidgets(self):
        self.keys = list(tests.keys())

        self.plotInt = tk.IntVar()
        self.datumInt = tk.IntVar()
        self.siInt = tk.IntVar()

        # Entries
        self.entryFrame = tk.Frame(self)
        self.confField = tk.Entry(self.entryFrame, width=100)
        self.saveConfigButton = tk.Button(self.entryFrame, text="Save Config", command=self.saveConfig)
        self.loadConfigButton = tk.Button(self.entryFrame, text="Load Config", command=self.loadConfig)
        self.versionField = tk.Entry(self.entryFrame, width=20)
        self.projectField = tk.Entry(self.entryFrame, width=100)
        self.usgsField = tk.Entry(self.entryFrame, width = 100)
        self.riverField = tk.Entry(self.entryFrame, width=100)
        self.reachField = tk.Entry(self.entryFrame, width=100)
        self.rsField = tk.Entry(self.entryFrame, width=100)
        self.stageField = tk.Entry(self.entryFrame, width=100)
        self.slopeField = tk.Entry(self.entryFrame, width=100)
        self.fileNField = tk.Entry(self.entryFrame, width=100)
        self.nField = tk.Entry(self.entryFrame, width=100)
        self.outField = tk.Entry(self.entryFrame, width=100)
        self.metricField = tk.Frame(self.entryFrame)
        self.plotField = tk.Checkbutton(self.entryFrame, text="Plot?", variable=self.plotInt)
        self.datumField = tk.Checkbutton(self.entryFrame, text="Correct Datum?", variable=self.datumInt)
        self.siField = tk.Checkbutton(self.entryFrame, text="SI Units?", variable=self.siInt)

        self.pairs = {
            "version": self.versionField,
            "project": self.projectField,
            "stagef": self.stageField,
            "river": self.riverField,
            "reach": self.reachField,
            "rs": self.rsField,
            "nct": self.nField,
            "outf": self.outField,
            "filen": self.fileNField,
            "slope": self.slopeField,
            "usgs": self.usgsField
        }

        self.boxes = {
            "plot": self.plotInt,
            "datum": self.datumInt,
            "si": self.siInt
        }

        self.keyChecks = {}

        for (ix, key) in enumerate(self.keys):
            var = tk.IntVar()
            chk = tk.Checkbutton(self.metricField, text=key, variable=var)
            chk.grid(row=0, column=ix)
            self.keyChecks[key] = var

        fields = [
            ("Config File Path (optional): store/retrieve settings",
             self.confField,
             browseButton(self.entryFrame, self.setVal(self.confField))),
            ("Save Config", self.saveConfigButton),
            ("Load Config", self.loadConfigButton),
            ("HEC-RAS Version Number (e.g., 507, 631)", self.versionField),
            ("HEC-RAS Project File Path", self.projectField,
             browseButton(self.entryFrame, self.setVal(self.projectField))),
            ("USGS Gage # (optional): automatic USGS data retrieval",
             self.usgsField),
            ("Calibration River Name", self.riverField),
            ("Calibration Reach Name", self.reachField),
            ("Calibration River Station", self.rsField),
            ("Stage File Path (CSV with flow, stage; not required if USGS gage specified)",
             self.stageField,
             browseButton(self.entryFrame, self.setVal(self.stageField))),
            ("Slope for Normal Depth (downstream boundary condition)",
             self.slopeField),
            ("Flow file number to write (e.g. 01, to overwrite <project>.f01)",
             self.fileNField),
            ("# Roughness coefficients to test per iteration", self.nField),
            ("Output File Path", self.outField,
             browseButton(self.entryFrame, self.setVal(self.outField))),
            ("Metrics", self.metricField),
            ("Plot", self.plotField),
            ("Datum", self.datumField),
            ("SI Units", self.siField)
        ]

        for (ix, vals) in enumerate(fields):
            name = vals[0]
            field = vals[1]
            tk.Label(self.entryFrame, text=name).grid(row=ix)
            field.grid(row=ix, column=1)
            if len(vals) == 3:
                vals[2].grid(row=ix, column=2)

        self.entryFrame.pack(side="top")

        self.buttonFrame = tk.Frame(self)
        self.runAuto = tk.Button(self.buttonFrame, text = "Automatic Calibration", command=lambda: self.selectRunType("auto"))
        self.runAuto.pack(side="left")
        self.runItv = tk.Button(self.buttonFrame, text = "Interactive Calibration", command = lambda: self.selectRunType("manual"))
        self.runItv.pack(side = "right")
        self.buttonFrame.pack(side = "bottom")


LICENSE = """Raspy-Cal Automatic Calibrator
Copyright (C) 2021 Daniel Philippus
This program comes with ABSOLUTELY NO WARRANTY.  This is free software, and you are
welcome to redistribute it under certain conditions.  For details, see the LICENSE
file at github.com/quantum-dan/raspy-cal.  This software is released under the GNU
General Public License v3.
"""

def main(settings):
    root = tk.Tk()
    mainframe = tk.Frame(root)
    tk.Label(mainframe, text=LICENSE).pack(side="bottom")
    gui = GUI(mainframe, settings)
    mainframe.master.title("Raspy-Cal Calibrator")
    mainframe.pack()
    gui.mainloop()

if __name__ == "__main__":
    main()


