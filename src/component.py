import json
import logging
import os
import shutil
from csv import DictReader
from dataclasses import dataclass, field
from pathlib import Path

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
            self._copy_manifest_to_out(t)
            return
        mapping = self.configuration.parameters[matched_key].get(KEY_COLUMN_MAPPING, {})
        header = self.get_header(t)
        new_header = list()
        for c in header:
            if c in mapping:
                new_header.append(mapping[c])
            else:
                new_header.append(c)
        if t.is_sliced:
            self.replace_header_in_manifest_and_move(t.full_path, t._raw_manifest, new_header)  # noqa
            shutil.copytree(t.full_path, Path(self.tables_out_path).joinpath(t.name), dirs_exist_ok=True)
        elif t.columns:
            self.replace_header_in_manifest_and_move(t.full_path, t._raw_manifest, new_header)  # noqa
            shutil.copy(t.full_path, Path(self.tables_out_path).joinpath(t.name))
        else:
            self.replace_header_in_file_and_move(t.full_path, new_header, t.delimiter)
            self._copy_manifest_to_out(t)

    def _copy_manifest_to_out(self, t: TableDefinition):
        if t.get_manifest_dictionary():
            new_path = os.path.join(self.tables_out_path, Path(t.full_path).name + '.manifest')
            shutil.copy(t.full_path + '.manifest', new_path)

    def get_header(self, t: TableDefinition):
        if t.is_sliced or t.columns:
            header = t.columns
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

    def replace_header_in_manifest_and_move(self, file_path, manifest, new_header):
        manifest['columns'] = new_header
        with open(os.path.join(self.tables_out_path, Path(file_path).name + '.manifest'), 'w+') as out_f:
            json.dump(manifest, out_f)

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
