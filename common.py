import subprocess
import os.path
import re
import traceback
import config
import logging
import sys

__author__ = 'cymric@npg.net'

myConfig = config.get_config()


def find_package_for_file(filename, data):
    if filename in data.unknown_libraries:
        return None
    for package in myConfig.packages:
        for path in myConfig.packages[package]:
            if filename.find(path) >= 0:
                return package
    logging.warn("Cannot find package for file:" + filename)
    data.unknown_libraries[filename] = True
    return None


def find_lib_for_file(filename, data):
    if filename in data.unknown_libraries:
        return None
    if any(x in filename for x in myConfig.ignore_dependency_paths):
        data.unknown_libraries[filename] = True
        return None
    if filename in data.file_lib_cache:
        return data.file_lib_cache[filename]
    for lib in myConfig.libraries:
        for package in myConfig.libraries[lib]:
            for path in myConfig.packages[package]:
                if filename.find(path) >= 0:
                    data.file_lib_cache[filename] = lib
                    return lib
    logging.warn("Cannot find lib for file:" + filename)
    data.unknown_libraries[filename] = True
    return None


def build_lib_dependencies(data):
    dependencies = {}
    already_written = {}
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
            line = src + "->" + dst
            if line not in already_written:
                already_written[line] = True
                dependencies.setdefault(src, []).append(dst)
    return dependencies


class IncludeStruct:
    def __init__(self):
        self.removed_includes = 0
        self.preserved_includes = 0
        self.files = []
        # a map to build a hierarchy of includes
        self.includes = {}
        # map<file,list<include file>> all includes found in one file
        self.all_includes = {}
        self.include_path_mapping = {}
        self.no_includes = []
        self.limit_files = []

        self.found_file_list = []

        self.unknown_libraries = {}
        self.file_lib_cache = {}


def log_block(message):
    logging.info("-" * 60)
    logging.info(message)
    logging.info("-" * 60)


def get_filename_without_extension(file_path):
    """
    get only the filename without path and extension
    :param file_path: the full filename with path
    :return: string
    """
    head, tail = os.path.split(file_path)
    root, ext = os.path.splitext(tail)
    return root


def is_keyword_used_in_file(keyword, file):
    """
    try to find keywords in a file (except if used in forward declarations). If keyword is found, we can assume we need
    this include
    :param keyword: string to search
    :param file: file tp check
    :return: boolean
    """
    if myConfig.skip_keyword_match:
        return False
    keywords_in_file = subprocess.check_output(["grep", keyword, file])
    for line in keywords_in_file.split("\n"):
        if "include" in line:
            continue
        if re.search("\W" + keyword + "\W", line) is not None:
            if "class" in line:
                return False
            if "struct" in line:
                return False
            logging.debug("  Found in:" + line)
            return True
    return False


def find_files_in_path(data):
    """
    find all files which are relevant in the root_path
    fills found_file_list[]
    """
    for subdir, dirs, files in os.walk(myConfig.root_path):
        for file in files:
            if file.endswith(tuple(myConfig.file_extensions)):
                file_path = os.path.join(subdir, file)
                if not any(x in file_path for x in myConfig.file_excludes):
                    data.found_file_list.append(file_path)


def find_real_path_to_include(file, include, data):
    """
    find the real path to an include and insert it to include_path_mapping
    :param file: file in which the include is found
    :param include: the include
    :param data: fills include_path_mapping map<string,string> include->path
    """
    rel_path = os.path.join(os.path.dirname(file), include)
    if os.path.isfile(rel_path):
        data.include_path_mapping[include] = rel_path
        return
    for include_path in myConfig.include_paths:
        fullpath = os.path.join(myConfig.root_path, include_path, include)
        if os.path.isfile(fullpath):
            if include in data.include_path_mapping:
                logging.warn("Duplicate file name found in different include paths:" + fullpath + " and " +
                             data.include_path_mapping[include])
            data.include_path_mapping[include] = fullpath
    if include not in data.include_path_mapping:
        logging.warn(" Cannot find: " + include)


def find_includes_in_file(file, includes_from_file, data):
    """
    find all includes in a file
    :param file:
    :return:
    """
    local_sys_includes = []
    local_includes = []
    for inc_line in includes_from_file.split("\n"):
        if inc_line.find("<") > -1:
            include = re.search('<(.+)>', inc_line).group(1)
            if include in local_sys_includes:
                logging.warn(" Duplicate include found:"+include)
            else:
                local_sys_includes.append(include)
        elif inc_line.find('"') > -1:
            include = re.search('"(.+)"', inc_line).group(1)
            if include in local_includes:
                logging.warn(" Duplicate include found:"+include)
            else:
                local_includes.append(include)
                if include not in data.include_path_mapping:
                    find_real_path_to_include(file, include, data)

    data.all_includes[file] = local_sys_includes + local_includes
    logging.debug(" includes: " + str(data.all_includes[file]))
    if len(local_includes) > 0:
        data.includes[file] = local_includes


def remove_file_from_includes(file, message, data):
    for remove_file in data.files:
        if remove_file not in data.includes:
            continue
        new_includes = []
        for remove_include in data.includes[remove_file]:
            if not file.endswith("/" + remove_include):
                new_includes.append(remove_include)
            else:
                logging.info(message + " " + remove_file)
        if len(new_includes) > 0:
            data.includes[remove_file] = new_includes
        else:
            del data.includes[remove_file]


def gather_includes_from_files(data):
    for file in data.found_file_list:
        if not os.path.isfile(file):
            continue
        try:
            logging.info("Parse file: " + file)
            includes_from_file = subprocess.check_output(["grep", "#include", file])
            data.files.append(file)
            find_includes_in_file(file, includes_from_file, data)
        except subprocess.CalledProcessError:
            data.no_includes.append(file)
        except:
            traceback.print_exc()


def prepare_include_data():
    data = IncludeStruct()
    log_block("gather includes from the files")
    find_files_in_path(data)
    gather_includes_from_files(data)
    logging.info("Found:" + str(len(data.files) + len(data.no_includes)) + " files")
    if len(data.files) == 0:
        logging.error("No C/C++ files read via stdin")
        sys.exit()
    return data


def remove_files_without_includes(data):
    log_block("remove files which have no #include-directive to find start files")

    for file in data.no_includes:
        logging.info("Processing: " + file)
        remove_file_from_includes(file, " removed from:", data)

