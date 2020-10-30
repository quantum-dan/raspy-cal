# Raspy-Cal

A free and open-source automatic calibration system for HEC-RAS.

## Downloads

* Raspy-Cal: [executable](https://github.com/quantum-dan/raspy-cal/releases/tag/v1.0), [source](https://github.com/quantum-dan/raspy-cal)
* Raspy (default automation component/reference implementation): [source](https://github.com/quantum-dan/raspy)
* PyRASFile (HEC-RAS file writer/parser): [source](https://github.com/larflows/pyrasfile)
  * PyRASFile is also available through PyPI (`pip install pyrasfile`).
  * PyRASFile provides ad-hoc file parsing and writing functionality (e.g. writing flow files, parsing report output).  It is used by Raspy to write flow files; most other functionality is handled through the HEC-RAS COM.

## How does it work?

Raspy-Cal makes calibration of HEC-RAS hydraulic models easy.  The user just provides the model and empirical data for it (or a USGS gage number).  Then, Raspy-Cal runs simulations with a range of Manning's roughness coefficients and selects the best ones based on a set of goodness-of-fit metrics.  It can do the whole process automatically with a genetic algorithm, just returning the finalized results after iterating.  If you'd prefer more control, it can also run a set of simulations within a specified range of roughness coefficients, then show you the best 10 results and let you refine the range.

Raspy-Cal is developed in a modular way so that it depends as little as possible on HEC-RAS functionality and on the implementation details of the automation (Raspy).  It should be relatively straightforward to:

* Swap in other automation modules in place of Raspy, as long as they support the required API functionality
* Develop similar automation modules for other models and use them with Raspy-Call with minimal modification
* Build a different calibration platform on top of Raspy

This is intended to facilitate the use of Raspy-Cal as a generic calibration engine, rather than tying it specifically to HEC-RAS.  As much as possible of the HEC-RAS-specific functionality (except for data the user has to provide that's specific to HEC-RAS) is in Raspy, not Raspy-Cal, so changing the model or automation layer should only require modest modifications to a few lines of code in Raspy-Cal itself.

Raspy-Cal is releases under an open-source license, the GNU GPL v3, so anyone else can develop and release such a variant as long as it, too, is open-source (although components that are used by but not dependent on Raspy-Cal can remain proprietary; typically, the automation layer would not be dependent on Raspy-Cal).

## Usage

Raspy-Cal is released as a standalone Windows executable available under [Releases](https://github.com/quantum-dan/raspy-cal/releases/tag/v1.0).  This doesn't have any dependencies other than HEC-RAS (5.0.7; version selection will be introduced in a future update).  You can also download and run directly from [source](https://github.com/quantum-dan/raspy-cal), which requires the Python packages `scipy`, `HydroErr`, `matplotlib`, and `platypus-opt` to be installed.  Running from source is faster to launch.

Also available under Releases is a full example project, Demo.zip, which includes a HEC-RAS project, two Raspy-Cal configuration files, and an empirical data file.

You can either run Raspy-Cal through the command line or through a GUI.  By default, it will launch a GUI, which will request all required information.  You can also save your GUI settings as a configuration file and reload them later.  To use the interactive command-line version, run `raspy-cal.exe CMD`, and it will request all required information through the command line.  To load a configuration file in the command line, run `raspy-cal.exe <config path>`, and it'll load the available information; if everything is specified, it will just start running, or it will request any missing information first.  In those examples, `raspy-cal.exe` is interchangeable with `python main.py` if running from source.

However you run it, you need to specify:

* The project file location (with an extant flow file that you know the number for)
* Which flow file number to overwrite (e.g. 01)
* The empirical data location (stage file path) or USGS gage number
  * If you specify a USGS gage, you can optionally specify a time span or date range to retrieve data for, and approximately how many flows to retrieve across the range
  * The stage file is a CSV of Flow,Stage (exact names required, case-sensitive) in cfs and ft; note that Excel CSVs can append odd special characters to the column names that don't show up when viewing the file
* The river name, reach name, and river station from which to retrieve model data
* The slope to use for the normal depth boundary condition at the outlet
* How many roughness coefficients to test per iteration
* The output file location (a CSV file; the same path but ending in .png will be used to write plots to)
* Which goodness-of-fit metrics to use
* Whether to plot the results
* Whether to adjust the datum (since the datum for stage vs. max channel depth doesn't always line up, Raspy-Cal can adjust the data so that the average depth of the lowest 5% of flows is the same for fit metric purposes)

## License

Raspy-Cal is released under the [GNU General Public License Version 3](https://www.gnu.org/licenses/gpl-3.0.html).  This permits free modification and redistribution of the program and its source, as long as those modifications are themselves released under a similar (copyleft) license.
