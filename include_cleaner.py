#!/usr/bin/python
import sys
import os.path
import shutil
import logging

import config
from common import get_filename_without_extension, is_keyword_used_in_file, remove_file_from_includes, \
    prepare_include_data, log_block, remove_files_without_includes

__author__ = 'cymric@npg.net'


myConfig = config.get_config()

restrict_files = []
if len(sys.argv) > 2:
    for restrict in sys.argv[2:]:
        restrict_files.append(restrict)

# assumes #include "xxx" -> xxx is in include_paths
# assumes #include <xxx> -> xxx is somewhere in the system


def validate_includes(file, data):
    """
    starts the include cleaner for the given file, removes every include found, if it is necessary
    :param file: file to test
    :return:
    """
    if len(restrict_files) > 0 and not any(x in file for x in restrict_files):
        logging.info("  Ignored because of restrictedfiles .")
        return

    os.chdir(myConfig.root_path)

    for test_include in data.all_includes[file]:
        logging.info(" Testing: " + test_include)
        bak_file = file + ".bak"
        shutil.copy(file, bak_file)
        keyword = get_filename_without_extension(test_include)
        if is_keyword_used_in_file(keyword, file):
            logging.info("  Skipping used keyword.")
            data.preserved_includes += 1
            continue
        if any(x in test_include for x in myConfig.include_ignores):
            logging.info("  Ignored by configuration.")
            data.preserved_includes += 1
            continue
        if myConfig.debug:
            logging.info("  Needed.")
            data.preserved_includes += 1
            continue
        if os.system("grep -v '^[ \t]*#include[ \t][ \t]*[\"\<]" + test_include + "[\"\>]' " + bak_file + " > " + file) != 0:
            shutil.copy(bak_file, file)
        elif os.system("make -j" + myConfig.nr_compile_processes + " &> /dev/null") != 0:
            shutil.copy(bak_file, file)
            logging.info("  Needed.")
            data.preserved_includes += 1
        else:
            logging.info("  Removed.")
            data.removed_includes += 1
        os.remove(bak_file)


def check_compiler():
    os.chdir(myConfig.root_path)
    if not myConfig.debug and os.system("make -j" + myConfig.nr_compile_processes + " &> /dev/null") != 0:
        logging.error("Sorry cannot make a successful compile run")
        sys.exit()


def process_files(data):
    log_block("start removing includes from files")

    while len(data.files) > 0:
        logging.info("-" * 60)
        oldsize = len(data.files)
        for file in data.files[:]:
            if file in data.includes:
                continue
            logging.info("Processing: " + file)
            remove_file_from_includes(file, " needed from:", data)
            data.files.remove(file)
            if len(data.limit_files) > 0 and not any(x in file for x in data.limit_files):
                logging.info("  Skipping.")
                continue
            validate_includes(file, data)
        if oldsize == len(data.files):
            break


def process_leftover_files(data):
    log_block("Files with possible errors in includes (e.g. a cycle), extra round:")

    for file in data.files:
        logging.warn("File: " + file)
        validate_includes(file, data)

data = prepare_include_data()

remove_files_without_includes(data)

check_compiler()

process_files(data)

process_leftover_files(data)

log_block("Removed includes:" + str(data.removed_includes) + "/Preserved includes:" + str(data.preserved_includes))
