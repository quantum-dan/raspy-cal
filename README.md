# raspy-cal
Python automatic calibrator for HEC-RAS.  RAS + Python = raspy.

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
        * compute(steady = True, plan = None): compute for the relevant plan, if specified.  Note that the current (prototype) implementation of raspy ignores both arguments and just runs the current plan.
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