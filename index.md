# Raspy-Cal

A free and open-source automatic calibration system for HEC-RAS.  A full description of the implementation is in the associated paper, [Raspy-Cal: A Genetic Algorithm-Based Automatic Calibration Tool for HEC-RAS Hydraulic Models](https://www.mdpi.com/2073-4441/13/21/3061) (Water is an open-access journal, so the full article is available without a subscription).

## Quick Start Guide

You must have HEC-RAS 5.0.7 installed for Raspy-Cal to work.  Support for HEC-RAS 6 will be added in the future.

We recommend installing Raspy-Cal from the Python Package Index, as this version is more actively kept up-to-date and launches much faster than the executable.

1. If you have Python 3 and pip installed, install with `pip install raspy-cal`.  Otherwise, download the latest executable from Releases (see [Downloads](#Downloads)).
2. If installed with pip, run Raspy-Cal with `python -m raspy_cal`.  Otherwise, run the executable.  Note thsat the executable will take some time to launch.
3. To load in a configuration file or specify a configuration file to save settings to, set the "Config File Path (optional)" field, for example to the location of Demo/demo_proj.conf if you are using the demo project.
4. To load the configuration data, click "Load Config".
5. Fill out the applicable fields below.
   1. "Project File Path" should be your HEC-RAS project file.
   2. If you are using a USGS gage, enter its gage number.
   3. Enter the HEC-RAS river name of the calibration location.
   4. Enter the HEC-RAS reach name of the calibration location.
   5. Enter the HEC-RAS river station of the calibration location.
   6. If you are not using a USGS gage, enter the location of the stage (empirical data) file, e.g. DemoStage.csv.  This should have columns "Flow" and "Stage", in cfs/ft for US units or cms/m for SI units.
   7. Enter the slope to use for normal depth as a downstream boundary condition.
   8. Enter the flow file number to overwrite in the HEC-RAS project with the flow data. If it is in the single digits, it should have a leading 0 (e.g. "05").
   9. Enter how many roughness coefficients to test at once for interactive calibration.
   10. Enter the output file path (a .csv file).  In addition to e.g. "DemoOut.csv", which will contain the roughness coefficients and error metrics, Raspy-Cal will also write e.g. "DemoOut-data.csv", containing the model output data for the optimal solutions, and "DemoOut.png", containing the rating curve plot.
   11. Select the desired error metrics, whether to display the plot, whether to use datum adjustment, and whether to use SI units. (If SI units are selected, Raspy-Cal will convert USGS data to SI but will otherwise only change the displayed units in plots etc.  The HEC-RAS project and stage file are assumed to be in the correct unit system).
6. Click "Save Config" to save your settings.
7. Click "Automatic Calibration" or "Interactive Calibration".
8. For automatic calibration:
   1. Enter the number of evaluations to run.
   2. Click "Run Automatic Calibration".  When calibration is complete, Raspy-Cal will display the rating curve plot.  After you close the plot, it will display the error metrics.
9. For interactive calibration:
   1. Enter the minimum roughness coefficient.
   2. Enter the maximum roughness coefficient.
   3. Select whether to use a random or evenly-distributed roughness coefficient distribution.
   4. Click "Run Simulations".
   5. When the simulations are complete, Raspy-Cal will display the rating curve plot and error metrics. You can either save the results or adjust the roughness coefficient range and run it again.
10. After calibration is complete, results will be saved to the specified output files.  The roughness coefficient set in the HEC-RAS project may not be the optimal result, as the optimal result may not have been the last simulation run.

## Downloads

* Raspy-Cal:
  * [executable](https://github.com/quantum-dan/raspy-cal/releases/tag/v1.0.3), [source](https://github.com/quantum-dan/raspy-cal)
  * PyPI installation (recommended if Python is installed): `pip install raspy-cal` (run with `python -m raspy-cal`).
* Raspy (default automation component/reference implementation): [source](https://github.com/quantum-dan/raspy), `raspy-auto` on PyPI.
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

Raspy-Cal is released as a standalone Windows executable available under [Releases](https://github.com/quantum-dan/raspy-cal/releases/tag/v1.0).  This doesn't have any dependencies other than HEC-RAS (5.0.7; version selection will be introduced in a future update).  You can also download and run Raspy-Cal from PyPI using `pip install raspy-cal` to install and `python -m raspy_cal` to run if you have Python installed; this will launch considerably faster than the executable.

Also available under Releases is a full example project, Demo.zip, which includes a HEC-RAS project, two Raspy-Cal configuration files, and an empirical data file.  The demo project uses SI units, so be sure to set SI units on in the GUI or configuration file.

You can either run Raspy-Cal through the command line or through a GUI.  By default, it will launch a GUI, which will request all required information.  You can also save your GUI settings as a configuration file and reload them later.  To use the interactive command-line version, run `raspy-cal.exe CMD`, and it will request all required information through the command line.  To load a configuration file in the command line, run `raspy-cal.exe <config path>`, and it'll load the available information; if everything is specified, it will just start running, or it will request any missing information first.  In those examples, `raspy-cal.exe` is interchangeable with `python -m raspy_cal` if running from source.

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
* Whether to use SI units (the default is US Customary); note that Raspy-Cal won't check the units of the stage file or the HEC-RAS project, so these need to be set correctly by the user.  The SI setting impacts display labels and whether Raspy-Cal converts USGS gage data to SI.

## License

Raspy-Cal is released under the [GNU General Public License Version 3](https://www.gnu.org/licenses/gpl-3.0.html).  This permits free modification and redistribution of the program and its source, as long as those modifications are themselves released under the same license.

## Citing

If you need to reference Raspy-Cal, cite the paper linked at the top of the page.  An example citation and BibTeX entry are included below.

Philippus, D.; Wolfand, J.M.; Abdi, R.; Hogue, T.S. Raspy-Cal: A Genetic Algorithm-Based Automatic Calibration Tool for HEC-RAS Hydraulic Models. Water 2021, 13, 3061. https://doi.org/10.3390/w13213061

```
@Article{RaspyCal,
AUTHOR = {Philippus, Daniel and Wolfand, Jordyn M. and Abdi, Reza and Hogue, Terri S.},
TITLE = {Raspy-Cal: A Genetic Algorithm-Based Automatic Calibration Tool for HEC-RAS Hydraulic Models},
JOURNAL = {Water},
VOLUME = {13},
YEAR = {2021},
NUMBER = {21},
ARTICLE-NUMBER = {3061},
URL = {https://www.mdpi.com/2073-4441/13/21/3061},
ISSN = {2073-4441},
DOI = {10.3390/w13213061}
}
```
