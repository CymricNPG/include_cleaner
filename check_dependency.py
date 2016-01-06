#!/usr/bin/python
import logging

from common import prepare_include_data, find_lib_for_file
import config

__author__ = 'cymric@npg.net'

myConfig = config.get_config()


def check_dependencies(data):
    violations = []
    for cfile in data.files:
        src = find_lib_for_file(cfile, data)
        if src is None:
            continue
        for include in data.all_includes[cfile]:
            dst = None
            if include in data.include_path_mapping:
                dst = find_lib_for_file(data.include_path_mapping[include], data)
            else:
                dst = find_lib_for_file(include, data)
            if dst is None or src is dst:
                continue
            if src in myConfig.dependencies and dst in myConfig.dependencies[src]:
                continue
            violations.append((cfile, include, src, dst))
    return violations


def print_violations(violations):
    for (cfile, include, src, dst) in violations:
        logging.warn("Dependency violation in file: " + cfile)
        logging.warn(" with the include: " + include)
        logging.warn("  " + src + " -> " + dst)


data = prepare_include_data()
violations = check_dependencies(data)
print_violations(violations)
