#!/usr/bin/python
import logging

from common import prepare_include_data, find_lib_for_file, build_lib_dependencies
import config

__author__ = 'cymric@npg.net'

myConfig = config.get_config()

def print_violations(data):
    ignore, dependencies = build_lib_dependencies(data)
    for dependency in dependencies:
        if dependency.src_lib in myConfig.dependencies and dependency.dst_lib in myConfig.dependencies[dependency.src_lib]:
            continue
        logging.warn("Dependency violation in file: " + dependency.src)
        logging.warn(" with the include: " + dependency.dst)
        logging.warn("  " + dependency.src_lib + " -> " + dependency.dst_lib)


data = prepare_include_data()
print_violations(data)
