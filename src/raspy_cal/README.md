# Raspy-Cal
Python automatic calibrator for HEC-RAS.  RAS + Python + Calibrator = Raspy-Cal.

## Usage & Installation

### Windows Executable

Download `raspy-cal.exe` from Releases and run it.  The executable should work without any dependencies.  Note that it will take quite some time to start up as it loads libraries; it is not frozen.  The current version assumes HEC-RAS 5.0.7.  This will be made flexible in a future release.

### General

The stage (empirical data) file requested must be a CSV with columns named Flow and Stage.  Alternatively, the user can specify a USGS gage to automatically retrieve data.

The user must have a HEC-RAS project including appropriate geometry, plan, and an empty flow file, where the plan is set up to use the flow file, in addition to providing empirical data or a USGS gage number (from which empirical data will be retrieved).  The flow data will be generated from the provided or retrieved empirical data as long as a flow file is available and the plan is set up to use it. The flow file does not have to be empty, but the selected one will be overwritten.  See [development progress](#General-Development-Plan) below.

Note that CSVs written by Excel sometimes have special characters in the column headers, which need to be removed in order for the stage file parser to work correctly.

### Command-Line Usage

`python main.py` to launch a graphical interface.  `python main.py CMD` for text-based interactive use.  `python main.py <config file path>` to load a configuration file and then launch the command line (there is also an option to load config files in the GUI, but some options are ignored).

### Dependencies

Some Model object which supports the required functionality as described [below](#Required-API).  The raspy package, which provides such an API, is
included as a submodule.  The raspy API can be accessed through `default.Model` if raspy is somewhere where it can be accessed (e.g. in its subdirectory
as a submodule).  Running through `main.py` will use raspy, which is automatically cloned as well as a submodule if cloning from git.  A future update will upload Raspy-Cal and Raspy to PyPI.

Packages:
* scipy
* HydroErr
* matplotlib
* platypus-opt (NSGA-II implementation)

Raspy-cal is only tested with Python 3.  It may or may not work with Python 2.

### Installation

This section is not relevant for the executable version.  The executable version is standalone, requiring only that HEC-RAS is installed.

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

## General Development Plan
Current progress: minimum feature set implemented.  Basic GUI implemented.  Next is analysis & recommendations.

1. Minimum feature set - DONE
    1. Implement critical low-level functionality (run simulations, update *n* values) - DONE
    1. Implement critical mid-level functionality for semi-manual mode (compute criteria, generate parameter combinations, choose best combinations) - DONE
    1. Implement critical top-level functionality (accept inputs, display outputs, accept updated inputs & iterate) (covers both semi-manual and automatic)
        1. Text-based outputs (table of n vs error stats) - DONE
        1. Graphical outputs (comparison plots) - DONE
    1. Implement critical mid-level functionality for automatic mode (automatic optimization) - DONE
1. Analysis & recommendations
    1. Analyze which criteria lead to best results under which geometry and flow conditions - IN PROGRESS
1. Basic improvements
    1. Implement automatic data preparation from empirical data (flow profiles etc) - DONE
    1. Implement multi-target calibration support
        1. Multiple flow ranges
        1. Multiple locations/empirical data sets (manual range specification)
    1. Implement automatic generic-use outputs (for use by interfaces) - DONE (outputs CSV of n vs metrics)
    1. Implement R interface
    1. Implement generic config file + command line interface for use by other programs - DONE (config file)
1. Luxury improvements
    1. Implement any necessary changes to make the tool fully generic with respect to both parameters and criteria, allowing it to be used outside of HEC-RAS (if this is not already the case naturally) - IN PROGRESS (working on generic modular design)
    1. Implement full GUI - DONE
    1. Implement calibration support tools (e.g. automatic hydrologic-hydraulic model interfacing) (this - very distant - goal would basically mean, for particular applications, "put in rainfall, geometry, and empirical flow data, get out calibrated model" or analogous)
    
### Rough Timeline
1. Minimum feature set: done
1. Analysis & recommendations: by late March
1. Basic improvements: i and ii (important for functionality) by late April; iii-v (convenience features for external use) in fall 2020
1. Luxury improvements: low-priority continuing development with no specific timelines  

## Required API

Raspy-cal assumes that the following functionality is available in an API object.  This is provided by raspy.  At the current development level, the user must provide an initialized API object with a project open and the appropriate plan, flow, geometry etc selected.

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
