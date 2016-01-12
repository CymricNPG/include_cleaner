#!/usr/bin/python
import os

from common import prepare_include_data, log_block, build_lib_dependencies, find_package_for_file
import config

__author__ = 'cymric@npg.net'

myConfig = config.get_config()


def write_lib_graph(data):
    log_block("writing library dependency graph")
    dependencies, ignore = build_lib_dependencies(data)
    with open('libraries.gv', 'w') as output:
        output.write("digraph G {\n")
        for src in dependencies.keys():
            for dst in dependencies[src]:
                line = ""
                if src in myConfig.dependencies and dst in myConfig.dependencies[src]:
                    line = src + " -> " + dst + ";\n"
                else:
                    line = src + " -> " + dst + " [color = red];\n"
                output.write(line)
        for src in myConfig.dependencies:
            for dst in myConfig.dependencies[src]:
                if src in dependencies and dst in dependencies[src]:
                    continue
                else:
                    line = src + " -> " + dst + " [color = blue];\n"
                    output.write(line)
        output.write("}\n")

def build_package_cluster_name(container):
    """
    hack to create a cluster of packages
    :param container: the name of the container (normally the library name)
    :return: add "cluster_" to the container name
    """
    if myConfig.ignore_package_cluster:
        return container
    else:
        return "cluster_" + container


def write_package_graph(data):
    log_block("writing package dependency graph")

    already_written = {}

    with open('packages.gv', 'w') as output:
        output.write("digraph G {\n")

        for container in myConfig.libraries:
            output.write(" subgraph \"" + build_package_cluster_name(container) + "\" {\n")
            for package in myConfig.libraries[container]:
                output.write("  " + package + ";\n")
            output.write(" }\n")

        for cfile in data.files:
            src = find_package_for_file(cfile, data)
            if src is None:
                continue
            for include in data.all_includes[cfile]:
                dst = None
                if include in data.include_path_mapping:
                    dst = find_package_for_file(data.include_path_mapping[include], data)
                else:
                    dst = find_package_for_file(include, data)
                if dst is None or src is dst:
                    continue
                line = src + " -> " + dst + ";\n"
                if line not in already_written:
                    output.write(line)
                    already_written[line] = True
        output.write("}\n")


data = prepare_include_data()

write_lib_graph(data)

write_package_graph(data)

os.system("dot -Tjpg  packages.gv -opackages.jpg")
os.system("dot -Tjpg  libraries.gv -olibraries.jpg")
