import glob
import json
import logging
import os
import shutil
import sys
from csv import DictReader
from dataclasses import dataclass, field
from pathlib import Path

from kbc.env_handler import KBCEnvHandler

# global constants'


# configuration variables
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


class Component(KBCEnvHandler):

    def __init__(self, debug=False):
        KBCEnvHandler.__init__(self, MANDATORY_PARS)
        # override debug from config
        if self.cfg_params.get(KEY_DEBUG):
            debug = True

        log_level = logging.DEBUG if debug else logging.INFO
        # setup GELF if available
        if os.getenv('KBC_LOGGER_ADDR', None):
            self.set_gelf_logger(log_level)
        else:
            self.set_default_logger(log_level)

        logging.info('Loading configuration...')

        try:
            self.validate_config(MANDATORY_PARS)
        except ValueError as e:
            logging.exception(e)
            exit(1)

    def run(self):
        '''
        Main execution code
        '''
        params = self.cfg_params  # noqa
        tables = self.get_tables_def()
        for t in tables:
            self.rename_headers(t)

    def get_tables_def(self):
        table_files = [f for f in glob.glob(self.tables_in_path + "/**", recursive=False) if
                       not f.endswith('.manifest')]
        table_defs = list()
        for t in table_files:
            is_sliced = False
            manifest = dict()
            p = Path(t)
            if Path(t + '.manifest').exists():
                manifest = json.load(open(t + '.manifest'))

            if p.is_dir() and manifest:
                is_sliced = True
            elif p.is_dir() and not manifest:
                # skip folders that do not have matching manifest
                logging.warning(f'Folder {t} does not have matching manifest, it will be ignored!')
                continue

            table_defs.append(TableDef(path=t, file_name=p.name, is_sliced=is_sliced, manifest=manifest))
        return table_defs

    def rename_headers(self, t):
        if t.file_name not in self.cfg_params:
            # just move the files
            self._copy_table_to_out(t)
            self._copy_manifest_to_out(t)
            return
        mapping = self.cfg_params[t.file_name].get(KEY_COLUMN_MAPPING, {})
        header = self.get_header(t)
        new_header = list()
        for c in header:
            if c in mapping:
                new_header.append(mapping[c])
            else:
                new_header.append(c)

        if t.is_sliced:
            self.replace_header_in_manifest_and_move(t.path, t.manifest, new_header)
            shutil.copytree(t.path, Path(self.tables_out_path).joinpath(t.file_name))
        else:
            self.replace_header_in_file_and_move(t.path, new_header, t.manifest.get('delimiter', ','))
            self._copy_manifest_to_out(t)

    def _copy_manifest_to_out(self, t):
        if t.manifest:
            new_path = os.path.join(self.tables_out_path, Path(t.path).name + '.manifest')
            shutil.copy(t.path + '.manifest', new_path)

    def get_header(self, t: TableDef):
        if t.is_sliced or t.manifest.get('columns'):
            header = t.manifest['columns']
        else:
            with open(t.path) as input:
                delimiter = t.manifest.get('delimiter', ',')
                enclosure = t.manifest.get('enclosure', '"')
                reader = DictReader(input, lineterminator='\n', delimiter=delimiter, quotechar=enclosure)
                header = reader.fieldnames

        return header

    def replace_header_in_file_and_move(self, f, new_header, separator=','):
        new_path = os.path.join(self.tables_out_path, Path(f).name)
        with open(f) as from_file, open(new_path, mode="w") as to_file:
            line = from_file.readline()

            line = separator.join(new_header)
            to_file.write(line + '\n')
            # the pointer in original file is 1 now
            shutil.copyfileobj(from_file, to_file)

    def replace_header_in_manifest_and_move(self, file_path, manifest, new_header):
        manifest['columns'] = new_header
        with open(os.path.join(self.tables_out_path, Path(file_path).name + '.manifest'), 'w+') as out_f:
            json.dump(manifest, out_f)

    def _copy_table_to_out(self, t):
        if Path(t.path).is_dir():
            shutil.copytree(t.path, Path(self.tables_out_path).joinpath(t.file_name))
        else:
            shutil.copy(t.path, Path(self.tables_out_path).joinpath(t.file_name))


"""
        Main entrypoint
"""
if __name__ == "__main__":
    if len(sys.argv) > 1:
        debug_arg = sys.argv[1]
    else:
        debug_arg = False
    try:
        comp = Component(debug_arg)
        comp.run()
    except Exception as ex:
        logging.exception(ex)
        exit(1)
