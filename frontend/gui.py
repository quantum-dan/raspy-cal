"""
Graphical front-end.  Just some simple inputs with which to run iterate and autoIterate.
"""

from frontend.input import iteration, autoIterate
from frontend.display import evalTable
from midlevel.eval import tests
from default import Model
import tkinter as tk

# iteration(model, river, reach, rs, stage, flow, nct, rand, nmin, nmax, metrics, plot): [(n, metrics, sim)]
# autoIterate(model, river, reach, rs, flow, stage, nct, plot, outf, metrics): [(n, metrics)]

class GUI(tk.Frame):
    def __init__(self, master = None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.createWidgets()

    def saveParameters(self):
        self.project = self.projectField.get()
        self.river = self.riverField.get()
        self.reach = self.reachField.get()
        self.rs = self.rsField.get()
        self.stagef = self.stageField.get()
        self.nct = int(self.nField.get())
        self.outf = self.outField.get()
        self.metrics = [key for key in self.keyChecks if self.keyChecks[key].get() == 1]
        self.plot = self.plotInt.get() == 1

        print("Parameters: %s" % [self.project, self.river, self.reach, self.rs, self.stagef,
                                  self.nct, self.outf, self.metrics, self.plot])

    def createWidgets(self):
        self.keys = list(tests.keys())

        self.plotInt = tk.IntVar()

        # Entries
        self.entryFrame = tk.Frame(self)
        self.projectField = tk.Entry(self.entryFrame)
        self.riverField = tk.Entry(self.entryFrame)
        self.reachField = tk.Entry(self.entryFrame)
        self.rsField = tk.Entry(self.entryFrame)
        self.stageField = tk.Entry(self.entryFrame)
        self.nField = tk.Entry(self.entryFrame)
        self.outField = tk.Entry(self.entryFrame)
        self.metricField = tk.Frame(self.entryFrame)
        self.plotField = tk.Checkbutton(self.entryFrame, text="Plot?", variable=self.plotInt)
        self.saveButton = tk.Button(self.entryFrame, text="Save", command=self.saveParameters)

        self.keyChecks = {}

        for (ix, key) in enumerate(self.keys):
            var = tk.IntVar()
            chk = tk.Checkbutton(self.metricField, text=key, variable=var)
            chk.grid(row=0, column=ix)
            self.keyChecks[key] = var

        fields = [
            ("Project File Path", self.projectField),
            ("River Name", self.riverField),
            ("Reach Name", self.reachField),
            ("River Station", self.rsField),
            ("Stage File Path", self.stageField),
            ("# ns To Test", self.nField),
            ("Output File Path", self.outField),
            ("Metrics", self.metricField),
            ("Plot", self.plotField),
            ("Save Settings", self.saveButton)
        ]

        for (ix, (name, field)) in enumerate(fields):
            tk.Label(self.entryFrame, text=name).grid(row=ix)
            field.grid(row=ix, column=1)

        self.entryFrame.pack(side="top")

        self.buttonFrame = tk.Frame(self)
        self.runAuto = tk.Button(self.buttonFrame, text = "Automatic Calibration", command = lambda: 1)
        self.runAuto.pack(side="left")
        self.runItv = tk.Button(self.buttonFrame, text = "Interactive Calibration", command = lambda: 1)
        self.runItv.pack(side = "right")
        self.buttonFrame.pack(side = "bottom")



def main():
    root = tk.Tk()
    gui = GUI(root)
    gui.master.title("Raspy-Cal Calibrator")
    gui.mainloop()

if __name__ == "__main__":
    main()


