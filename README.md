# include_cleaner
A collection of small python scripts to remove unused C++ includes and view the dependencies between C++
packages/libraries based on the includes.


Usage:

*./include_cleaner.py config_file [optional restrict files ...]*

Removes unused includes on a try and error basis: Remove one #include, does it still compile? Unnecessary include.
If only some files should be optimized, a list of sub-strings can be added to the call.
The config_file is a json file, which contains the complete configuration (see config.json or example/example.json)

*./check_dependency.py config_file*

In the config file the structure of the C++ application can be specified, it checks if any forbidden dependencies exist.


*./dependency_graph.py config_file*

Shows the package and library path of the application.

