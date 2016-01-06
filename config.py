import logging
import sys
import json

__author__ = 'cymric@npg.net'

_config = None


def get_config():
    global _config
    if _config is None:
        if len(sys.argv) <= 1:
            raise ValueError("Missing configuration in arguments, call e.g. 'dependency_graph.py my_config.json'', Given Arguments= " + str(sys.argv))
        _config = Config(sys.argv[1])
    return _config


class Config:
    """
    Configuration for all include cleaner scripts, uses an external json file for configuration
    """

    def __init__(self, filename):
        with open(filename) as fp:
            file_dictionary = json.load(fp)
            for name, value in file_dictionary["__Config__"].items():
                setattr(self, name, value)

        # Log config
        logging.basicConfig(format='%(levelname)s  %(filename)s %(lineno)d :  %(message)s', level=logging.INFO,
                            stream=sys.stdout)
