#!/usr/bin/env python3
import os

from jinja2 import Environment, PackageLoader


class ORMInternalRenderException(Exception):
    pass


class RenderOutput:
    def __init__(self, rule_docs, output_file, globals_doc=None):
        self.rule_docs = rule_docs
        if not globals_doc:
            globals_doc = {}
        self.globals_doc = globals_doc
        self.output_file = output_file
        self.config = ""
        self.jinja = Environment(
            loader=PackageLoader("orm", "templates"), trim_blocks=True
        )

    def write_config_to_file(self, directory=None):
        """ Outputs the rules list to a file """
        filename = self.output_file
        if directory:
            if not os.path.exists(directory):
                os.mkdir(directory)
            filename = os.path.join(directory, filename)
        with open(filename, mode="wt") as file:
            file.write(self.config)

    def print_config(self):
        print(self.config)
