import logging
import os
import shutil
from csv import DictReader
from dataclasses import dataclass, field
from pathlib import Path
import copy

from keboola.component import ComponentBase, UserException
# configuration variables
from keboola.component.dao import TableDefinition

# global constants'

KEY_COLUMN_MAPPING = 'column_mapping'
# #### Keep for debug
KEY_DEBUG = 'debug'
MANDATORY_PARS = []


@dataclass
class TableDef:
    path: str
    file_name: str
    is_sliced: bool
    manifest: dict = field(default_factory=dict)


class Component(ComponentBase):

    def __init__(self):
        ComponentBase.__init__(self)
        self.validate_configuration_parameters(MANDATORY_PARS)

    def run(self):
        tables = self.get_input_tables_definitions()
        for t in tables:
            self.rename_headers(t)
        # move files
        if os.path.exists(self.files_in_path):
            shutil.copytree(self.files_in_path, self.files_out_path, dirs_exist_ok=True)

    def rename_headers(self, t: TableDefinition):
        patterns = [k for k in list(self.configuration.parameters.keys()) if k.endswith('*')]
        matched_key = None
        for p in patterns:
            pat = p.replace("*", '')
            if t.name.startswith(pat):
                matched_key = p
        if t.name in self.configuration.parameters:
            matched_key = t.name

        if not matched_key:
            # just move the files
            self._copy_table_to_out(t)
            t.full_path = t.full_path.replace(self.tables_in_path, self.tables_out_path)
            self.write_manifest(t)
            return
        mapping = self.configuration.parameters[matched_key].get(KEY_COLUMN_MAPPING, {})
        header = self.get_header(t)
        new_header = list()
        for c in header:
            if c in mapping:
                new_header.append(mapping[c])
            else:
                new_header.append(c)

        self.rename_metadata(t, mapping)

        is_input_mapping_manifest = t.stage == 'in'
        if t.is_sliced:
            shutil.copytree(t.full_path, Path(self.tables_out_path).joinpath(t.name), dirs_exist_ok=True)
        elif t.column_names and not is_input_mapping_manifest:
            shutil.copy(t.full_path, Path(self.tables_out_path).joinpath(t.name))
        else:
            self.replace_header_in_file_and_move(t.full_path, new_header, t.delimiter)

        self.rename_columns_in_table_definition(t, new_header)
        t.full_path = t.full_path.replace(self.tables_in_path, self.tables_out_path)
        self.write_manifest(t)

    def rename_columns_in_table_definition(self, table: TableDefinition, new_column_names: list):
        new_table_definition = copy.deepcopy(table)
        old_column_names = list(table.schema.keys())
        new_table_definition.delete_columns(old_column_names)

        for old_name, new_name in zip(old_column_names, new_column_names):
            new_table_definition.add_column(new_name, table.schema[old_name])

        table.schema = new_table_definition.schema

    def rename_metadata(self, table: TableDefinition, mapping: dict):
        new_metadata = {}
        if table.table_metadata.column_metadata:
            for key, value in table.table_metadata.column_metadata.items():
                if key in mapping:
                    new_key = mapping[key]
                else:
                    new_key = key
                new_metadata[new_key] = value
            table.table_metadata.column_metadata = new_metadata

    def get_header(self, t: TableDefinition):
        if t.is_sliced or t.column_names:
            header = t.column_names
        else:
            with open(t.full_path, encoding='utf-8') as input:
                delimiter = t.delimiter
                enclosure = t.enclosure
                reader = DictReader(input, lineterminator='\n', delimiter=delimiter, quotechar=enclosure)
                header = reader.fieldnames

        return header

    def replace_header_in_file_and_move(self, f, new_header, separator=','):
        new_path = os.path.join(self.tables_out_path, Path(f).name)
        with open(f, encoding='utf-8') as from_file, open(new_path, mode="w", encoding='utf-8') as to_file:
            line = from_file.readline()

            line = separator.join(new_header)
            to_file.write(line + '\n')
            # the pointer in original file is 1 now
            shutil.copyfileobj(from_file, to_file)

    def _copy_table_to_out(self, t: TableDefinition):
        if Path(t.full_path).is_dir():
            shutil.copytree(t.full_path, Path(self.tables_out_path).joinpath(t.name))
        else:
            shutil.copy(t.full_path, Path(self.tables_out_path).joinpath(t.name))


"""
        Main entrypoint
"""
if __name__ == "__main__":
    try:
        comp = Component()
        # this triggers the run method by default and is controlled by the configuration.action parameter
        comp.execute_action()
    except UserException as exc:
        logging.exception(exc)
        exit(1)
    except Exception as exc:
        logging.exception(exc)
        exit(2)
