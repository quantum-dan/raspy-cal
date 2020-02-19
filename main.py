from frontend.input import iterate, specify
from frontend import gui
from sys import argv

msg = """Note: in order to run somewhat more economically, you can use:
python raspy_cal/main.py <project path> <stage file path> <output file path>
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
            name = input("Output file name?  Out_<Gage>_<name>.txt, name: ")
            specify(
                project = basepath + "LAR\\FullModel.prj",
                stagef = basepath + "data\\" + gage + ".csv",
                river = locs[gage]["river"],
                reach = locs[gage]["reach"],
                rs = locs[gage]["rs"],
                outf = basepath + "data\\Out_" + gage + "_" + name + ".txt",
                plot = True,
                auto = True
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
        print("Run python main.py CMD to use the command line version.")
        gui.main()


