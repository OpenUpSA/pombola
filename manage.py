#!/usr/bin/env python
from __future__ import print_function
import os
import sys
import yaml

from django.core.management.base import (
    BaseCommand, CommandParser, CommandError
)

def run_default_tests(command_line_args):
    # This reproduces the logic used by execute_from_command_line to
    # extra whether the subcommand is "test" and whether a settings
    # module has been manually specified.
    try:
        subcommand = command_line_args[1]
    except IndexError:
        return False

    parser = CommandParser(None, usage="%(prog)s subcommand [options] [args]", add_help=False)
    parser.add_argument('--settings')
    parser.add_argument('--pythonpath')
    parser.add_argument('args', nargs='*')
    try:
        options, args = parser.parse_known_args(command_line_args[2:])
    except CommandError:
        # Ignore any errors, we just wanted to extract any settings option
        # that might have been specified.
        options = {'settings': None}

    return subcommand == 'test' and not options.settings


if __name__ == "__main__":

    if run_default_tests(sys.argv):
        settings_module = 'pombola.settings.tests'
        print("Warning: we recommend running tests with ./run-tests instead")
    else:
        settings_module = "pombola.settings.south_africa"

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
