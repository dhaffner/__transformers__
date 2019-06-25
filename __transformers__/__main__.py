"""Transformers.

Usage:
  __transformers__ [-v | --verbose] print <filename>...
  __transformers__ [-v | --verbose] run <filename>...
  __transformers__ (-h | --help)
  __transformers__ --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  -v --verbose  Show verbose logging.
"""

from runpy import run_module
from pathlib import Path

import logging
import sys
import astor

from . import setup
from docopt import docopt


def print_transformed(filename):
    from .loader import transform
    ast = astor.parse_file(filename)
    print(astor.to_source(transform(ast)))


def run_transformed(filename):
    path = Path(filename).parent.as_posix()
    module_name = Path(filename).name[:-3]
    sys.path.insert(0, path)
    run_module(module_name)


def main():
    arguments = docopt(__doc__, version='Transformers 0.0.1')
    if arguments['--verbose']:
        logging.basicConfig(level=logging.DEBUG)

    setup()
    filenames = arguments['<filename>']
    if arguments['print']:
        for filename in filenames:
            print_transformed(filename)

    elif arguments['run']:
        for filename in filenames:
            run_transformed(filename)


if __name__ == '__main__':
    main()