"""
Run raspy-cal interactively.

Copyright (C) 2020 Daniel Philippus

This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""


from frontend.input import specify, configSpecify
from frontend import gui
from sys import argv

msg = """Raspy-Cal interactive command-line interface.

Copyright (C) 2020 Daniel Philippus
This program comes with ABSOLUTELY NO WARRANTY.
    This is free software, and you are welcome to redistribute it
    under certain conditions.    For details see the LICENSE file
    at https://github.com/quantum-dan/raspy-cal.

Note: in order to run somewhat more economically, you can use:
python raspy_cal/main.py <project path> <stage file path> <output file path>.
Alternatively, to use a config file, run: `python main.py <config file path>`
or `raspy-cal.exe <config file path>`.
"""

"""
Testing with LAR data:
* F37B = Compton Creek : CC : 23350
* F45B = Rio Hondo Chnl : RHC : 7000
* F300 = Upper LAR : Above RH : 195289.1
* F319 = LA River : Below CC : 21500
"""

locs = {
    "F37B": {"river": "Compton Creek", "reach": "CC", "rs": "23350."},
    "F45B": {"river": "Rio Hondo Chnl", "reach": "RHC", "rs": "7000"},
    "F300": {"river": "Upper LAR", "reach": "Above RH", "rs": "195289.1"},
    "F319": {"river": "LA River", "reach": "Below CC", "rs": "21500"}
}

basepath = "V:\\LosAngelesProjectsData\\HEC-RAS\\raspy_cal\\"  # for testing

if __name__ == "__main__":
    if len(argv) == 4:
        specify(project = argv[1], stagef = argv[2], outf = argv[3])
    elif len(argv) == 2:  # for testing
        if argv[1] == "LAR":  # Test with LA project
            gage = input("Gage (F37B, F45B, F300, F319): ")
            for metric in ["r2", "pbias", "rmse", "ks_pval", "ks_stat", "paired", "mae", "nse"]:
                print("Running %s with %s" % (gage, metric))
                specify(
                    project = basepath + "LAR\\FullModel.prj",
                    stagef = basepath + "data\\" + gage + ".csv",
                    river = locs[gage]["river"],
                    reach = locs[gage]["reach"],
                    rs = locs[gage]["rs"],
                    outf = basepath + "data\\Out_" + gage + "_" + metric + ".txt",
                    plot = True,
                    auto = True,
                    metrics=[metric],
                    nct=10,
                    evals=50,
                    fileN="05",
                    slope=0.001
                )
        if argv[1] == "CMDTEST":  # Test the text interface
            basepath = "V:\\LosAngelesProjectsData\\HEC-RAS\\"
            specify(
                project = basepath + "raspy\\DemoProject\\project.prj",
                stagef = basepath + "raspy_cal\\DemoStage.csv",
                outf = basepath + "raspy_cal\\DemoOut.txt"
            )
        if argv[1] == "CMD":
            print(msg)
            specify()
        if argv[1] == "GUI":  # Test the GUI (when implemented)
            gui.main()
        else:
            configSpecify(argv[1], run=True)
    else:
        print("Run python main.py CMD to use the command line version.")
        gui.main()


