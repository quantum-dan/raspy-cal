# Raspy-Cal
Python automatic calibrator for HEC-RAS.  RAS + Python + Calibrator = Raspy-Cal.

## Quick Start Guide

You must have HEC-RAS 5.0.7 installed for Raspy-Cal to work.  Support for HEC-RAS 6 will be added in the future.

1. If you have Python 3 and pip installed, install with `pip install raspy-cal`.  Otherwise, download the latest executable from Releases.  The Python/pip approach is preferable, as it launches faster and is usually more up-to-date.
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

## Usage & Installation

### Windows Executable

Note that the preferred method of running, if you have Python 3 installed or are willing to install it, is to download Raspy-Cal from PyPI (see [Installation](#Installation)).  In addition to launching much faster, this version gets every update, whereas the executable is only updated for more major updates.

Download `raspy-cal.exe` from Releases and run it.  The executable should work without any dependencies.  Note that it will take quite some time to start up as it loads libraries; it is not frozen.  The current version assumes HEC-RAS 5.0.7.  This will be made flexible in a future release.

### General

The stage (empirical data) file requested must be a CSV with columns named Flow and Stage.  Alternatively, the user can specify a USGS gage to automatically retrieve data.

The user must have a HEC-RAS project including appropriate geometry, plan, and an empty flow file, where the plan is set up to use the flow file, in addition to providing empirical data or a USGS gage number (from which empirical data will be retrieved).  The flow data will be generated from the provided or retrieved empirical data as long as a flow file is available and the plan is set up to use it. The flow file does not have to be empty, but the selected one will be overwritten.  See [development progress](#General-Development-Plan) below.

The bulk of the internals are unit system-agnostic, and Raspy-Cal does not check the units of the stage file or the HEC-RAS project; these must be set appropriately, and to match, by the user (cms/m or cfs/ft).  The SI units setting determines data and graph labels (e.g. "Flow (cms)" vs "Flow (cfs)"), and, if the unit system is set to SI, Raspy-Cal will convert USGS data to SI.  The demo project is in SI units.

Note that CSVs written by Excel sometimes have special characters in the column headers, which need to be removed in order for the stage file parser to work correctly.

### Command-Line Usage

If installed with PyPI or running from source, use `python -m raspy_cal` to launch.  Use the argument `CMD` for text-based interactive use, or pass a config file path as an argument to load the configuration file into the command line version.

### Dependencies

Some Model object which supports the required functionality as described [below](#Required-API).  The raspy package, which provides such an API, is
included as a submodule.  The raspy API can be accessed through `default.Model` if raspy is somewhere where it can be accessed (e.g. in its subdirectory
as a submodule).  The default installation includes, and uses, raspy-auto, which is the raspy package on PyPI.  All dependencies will be installed automatically if
Raspy-Cal is installed through PyPI.

Packages:
* scipy
* HydroErr
* matplotlib
* platypus-opt (NSGA-II implementation)
* raspy-auto

Raspy-cal is only tested with Python 3.  It may or may not work with Python 2.

### Installation

This section is not relevant for the executable version.  The executable version is standalone, requiring only that HEC-RAS is installed.

Run `pip install raspy-cal` to install via PyPI, in which case `python -m raspy_cal` will run the GUI.

`git clone https://github.com/quantum-dan/raspy-cal raspy_cal` (clone into `raspy_cal` if you want to import it from elsewhere, as `raspy-cal` isn't a valid Python name).

The following will install all dependencies and run raspy-cal (with the GUI) using raspy for HEC-RAS access:

```
git clone https://github.com/quantum-dan/raspy-cal
pip install --user scipy HydroErr matplotlib platypus-opt
cd raspy-cal
python main.py
```

### Building a Standalone Executable

Requires pyinstaller (`pip install pyinstaller`).

From the raspy-cal directory, run: `pyinstaller -F main.py`.  This will build a standalone executable in the `dist` subdirectory (which will be created).

## Functionality & Approach

### Paper

A full description of the implementation is provided in the [associated paper](https://www.mdpi.com/2073-4441/13/21/3061).

### General Functionality
Raspy-cal supports both fully-automatic and partially-manual calibration modes.

In manual mode, the user specifies a range of calibration parameters and a set of criteria.  The program runs a specified number of simulations across the range of parameters, comparing the results of each to the relevant criteria.  Then, it shows the user comparison plots (rating curves) of the top *n* parameter sets based on the criteria.  The user uses that information to specify a new range, and repeat 
until the user is satisfied with the results.

In automatic mode, the user also specifies a range of calibration parameters and a set of criteria.  Then, the program uses a multi-objective genetic algorithm (NSGA-II with possible future support for other algorithms) to optimize for a specified number of generations with a specified number of tests per generation.  After running the last generation, the non-dominated results are displayed as in manual mode, as well as a plot showing the comparison plots for all of the non-dominated results.  This allows the user to select the overall best choice.

In both cases, the user currently has to specify a particular range to calibrate and calibrate against just one empirical data set.  Later, the program will support many data sets covering different ranges.

### Detailed Approach
Top-level (user-facing) functionality:
* Display rating curves with parameters and criteria
* Accept criteria and parameter ranges and specifications
* Accept empirical data

Mid-level (doing the work) functionality:
* Compute criteria
* Choose parameter combinations
* Select best combinations
* Use automatic optimization

Low-level (support) functionality:
* Run simulations
* Update parameter values
* (Eventually) generate flow profiles etc from empirical data; at first, the user will need to specify the flow profiles (pyRasFile supports this use case with minor manual intervention)

## Required API

Raspy-cal assumes that the following functionality is available in an API object.  This is provided by Raspy, but an alternative automation API can be provided by modifying `default.py`; as long as the provided API object has all of the methods detailed below (see Raspy for a reference implementation), no other modifications should be required.  At the current development level, the user must provide an initialized API object with a project open and the appropriate plan, flow, geometry etc selected.

For example, having access to the method "api.ops.compute(steady, plan)" would be written as:

* api
    * ops
        * compute(steady, plan)
        
Required methods:

* api: overarching API object containing all functionality
    * ops: general operations
        * openProject(projectPath): open the relevant project (project path including *.prj file)
        * compute(steady = True, plan = None, wait = True): compute for the relevant plan, if specified.  If wait is true, don't continue until the computation is done.  Note that the current (prototype) implementation of raspy ignores both arguments and just runs the current plan.
    * data: data retrieval from the latest simulation.  Unless otherwise noted, all the methods work the same way with specifying locations and profiles as allFlow (see below).
        * allFlow(river = None, reach = None, rs = None, nprofs = 1): returns all flow data for the specified location (or, if unspecified, nested dictionaries to the point that it is specified--all None would be `{river: {reach: {rs: }}}`).  Flow data entries have values .velocity, .flow, .maxDepth, and .etc, where etc is a dictionary of everything else.  If nprofs is 1, it will return that for the first profile.  If not, it will return a dictionary of `{profile number: results}` for each profile up to nprofs wrapping the aforementioned results.
        * getSingleDatum(func, river, reach, rs, nprofs = 1): like allFlow, but without default arguments and `func` specifies which aspect to extract (e.g. `lambda x: x.velocity`).  This is mainly in raspy for internal use (hence lack of default arguments), but may be needed to extract values not automatically provided.
        * velocity(river = None, reach = None, rs = None, nprofs = 1): returns the velocity.
        * stage(river = None, reach = None, rs = None): returns the maximum depth
    * params: setting parameters
        * modifyN(manning, river, reach, geom = None): set Manning's n for the given geometry file (if specified).  Note that the current implementation of raspy ignores the geom argument and just uses the current geometry file.  At least the following forms of `manning` must be supported (note: in raspy currently, setting the "main channel n" actually sets all three ns to the same value): `manning` is a...
            * list:
                * of lists of numbers: for each cross section (from the bottom), set the ns going from left to right to those provided in the corresponding list.
                * of numbers: for each cross section, set the main channel n to the corresponding value from the list.
            * dictionary ({rs: [...]): set ns by cross section specifically.  The values can be either numbers or lists of numbers, which works the same as the list version above.
            * number: set all the main channel ns to the specified value.
        * setSteadyFlows(river, reach, rs, flows, slope, fileN, hecVer): set the steady flows at that location (or the top cross-section if rs is None).  `flows` is a list of flows.  `rs` can be None, in which case it will use the uppermost river station in the reach.  `slope` is the slope for normal depth as a boundary condition.  `fileN` is the flow file number as a string (e.g. "01").  `hecVer` is the HEC-RAS version, and must be optional.
