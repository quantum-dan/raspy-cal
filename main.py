from frontend.input import iterate, specify
from sys import argv

msg = """Note: in order to run somewhat more economically, you can use:
python raspy_cal/main.py <project path> <stage file path> <output file path>
"""

if __name__ == "__main__":
    print(msg)
    if len(argv) == 4:
        specify(project = argv[1], stagef = argv[2], outf = argv[3])
    else:
        specify()


