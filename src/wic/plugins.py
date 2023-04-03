import logging
import glob
import os
from pathlib import Path
import re
from typing import Dict

import cwltool.load_tool
import yaml

from . import utils
from .wic_types import Cwl, StepId, Tool, Tools


# Filter out the "... previously defined" id uniqueness validation warnings
# from line 1162 of ref_resolver.py in the schema_salad library.
# TODO: Figure out if there is a problem with our autogenerated CWL.
class NoPreviouslyDefinedFilter(logging.Filter):
    # pylint:disable=too-few-public-methods
    def filter(self, record: logging.LogRecord) -> bool:
        return not record.getMessage().endswith('previously defined')


logger_salad = logging.getLogger("salad")
logger_salad.addFilter(NoPreviouslyDefinedFilter())


class NoResolvedFilter(logging.Filter):
    # pylint:disable=too-few-public-methods
    def filter(self, record: logging.LogRecord) -> bool:
        m = re.match(r"Resolved '.*' to '.*'", record.getMessage())
        return not bool(m)  # (True if m else False)


logger_cwltool = logging.getLogger("cwltool")
logger_cwltool.addFilter(NoResolvedFilter())


def validate_cwl(cwl_path_str: str, skip_schemas: bool) -> None:
    """This is the body of cwltool.load_tool.load_tool but exposes skip_schemas for performance.
    Skipping significantly improves initial validation performance, but this is not always desired.
    See https://github.com/common-workflow-language/cwltool/issues/623

    Args:
        cwl_path_str (str): The path to the CWL file.
        skip_schemas (bool): Skips processing $schemas tags.
    """
    # NOTE: This uses NoResolvedFilter to suppress the info messages to stdout.
    loading_context, workflowobj, uri = cwltool.load_tool.fetch_document(cwl_path_str)
    # NOTE: There has been a breaking change in the API for skip_schemas.
    # TODO: re-enable skip_schemas while satisfying mypy
    # loading_context.skip_schemas = skip_schemas
    loading_context, uri = cwltool.load_tool.resolve_and_validate_document(
        loading_context, workflowobj, uri, preprocess_only=False  # , skip_schemas=skip_schemas
    )
    # NOTE: Although resolve_and_validate_document does some validation,
    # some additional validation is done in make_tool, i.e.
    # resolve_and_validate_document does not in fact throw an exception for
    # some invalid CWL files, but make_tool does!
    process_ = cwltool.load_tool.make_tool(uri, loading_context)
    # return process_ # ignore process_ for now


def get_tools_cwl(cwl_dirs_file: Path, validate_plugins: bool = False, skip_schemas: bool = False) -> Tools:
    """Uses glob() to find all of the CWL CommandLineTool definition files within any subdirectory of cwl_dir

    Args:
        cwl_dirs_file (Path): The subdirectories in which to search for CWL CommandLineTools
        validate_plugins (bool, optional): Performs validation on all CWL CommandLiineTools. Defaults to False.
        skip_schemas (bool, optional): Skips processing $schemas tags. Defaults to False.

    Returns:
        Tools: The CWL CommandLineTool definitions found using glob()
    """
    utils.copy_config_files()
    # Load ALL of the tools.
    tools_cwl: Tools = {}
    cwl_dirs = utils.read_lines_pairs(cwl_dirs_file)
    for plugin_ns, cwl_dir in cwl_dirs:
        # "PurePath.relative_to() requires self to be the subpath of the argument, but os.path.relpath() does not."
        # See https://docs.python.org/3/library/pathlib.html#id4 and
        # See https://stackoverflow.com/questions/67452690/pathlib-path-relative-to-vs-os-path-relpath
        cwl_dir_rel = os.path.relpath(cwl_dir)  # w.r.t. current working directory
        pattern_cwl = str(Path(cwl_dir_rel) / '**/*.cwl')
        # print(pattern_cwl)
        # Note that there is a current and a legacy copy of each cwl file for each tool.
        # The only difference appears to be that some legacy parameters are named
        # *_file as opposed to *_path. Since glob does NOT return the results in
        # any particular order, and since we are using stem as our dict key, current
        # files may be overwritten with legacy files (and vice versa), resulting in
        # an inconsistent naming scheme. Since legacy files are stored in an additional
        # subdirectory, if we sort the paths by descending length, we can overwrite
        # the dict entries of the legacy files.
        cwl_paths_sorted = sorted(glob.glob(pattern_cwl, recursive=True), key=len, reverse=True)
        Path('autogenerated/schemas/tools/').mkdir(parents=True, exist_ok=True)
        if len(cwl_paths_sorted) == 0:
            print(f'Warning! No cwl files found in {cwl_dir_rel}.\nCheck {cwl_dirs_file.absolute()}')
            print('This almost certainly means you are not in the correct directory.')
        # These two cwl files throw a yaml.scanner.ScannerError, but they are both legacy, so ignore.
        exceptions = ['biobb/biobb_adapters/cwl/biobb_md/gromacs_extra/ndx2resttop.cwl',
                      'biobb/biobb_adapters/cwl/biobb_md/gromacs/genrestr.cwl',
                      # No outputs (messes up the schema). Use pdb4amber_run
                      'biobb/biobb_adapters/cwl/biobb_amber/pdb4amber/pdb4amber.cwl',
                      'biobb/biobb_adapters/cwl/biobb_amber/pdb4amber.cwl',
                      # Empty dockerPull: '' Use autodock_vina_run
                      'biobb/biobb_adapters/cwl/biobb_vs/vina/autodock_vina.cwl',
                      'biobb/biobb_adapters/cwl/biobb_vs/autodock_vina.cwl']
        for cwl_path_str in cwl_paths_sorted:
            if any(e.replace('/', os.sep) in cwl_path_str for e in exceptions):
                continue
            # print(cwl_path)
            with open(cwl_path_str, mode='r', encoding='utf-8') as f:
                tool: Cwl = yaml.safe_load(f.read())
            stem = Path(cwl_path_str).stem
            # print(stem)

            if validate_plugins:
                validate_cwl(cwl_path_str, skip_schemas)

            # Add / overwrite stdout and stderr
            tool.update({'stdout': f'{stem}.out'})
            tool.update({'stderr': f'{stem}.err'})
            tools_cwl[StepId(stem, plugin_ns)] = Tool(cwl_path_str, tool)
            # print(tool)
            # utils_graphs.make_tool_dag(stem, (cwl_path_str, tool))
    return tools_cwl


def get_yml_paths(yml_dirs_file: Path) -> Dict[str, Dict[str, Path]]:
    """Uses glob() to recursively find all of the yml workflow definition files
    within any subdirectory of each yml_dir in yml_dirs_file.
    NOTE: This function assumes all yml files found are workflow definition files,
    so do not mix regular yml files and workflow files in the same root directory.
    Moreover, each yml_dir should be disjoint; do not use both '.' and './subdir'!

    Args:
        yml_dirs_file (Path): The subdirectories in which to search for yml files

    Returns:
        Dict[str, Dict[str, Path]]: A dict containing the filepath stem and filepath of each yml file
    """
    utils.copy_config_files()
    yml_dirs = utils.read_lines_pairs(yml_dirs_file)
    # Glob all of the yml files too, so we don't have to deal with relative paths.
    yml_paths_all: Dict[str, Dict[str, Path]] = {}
    for yml_namespace, yml_dir in yml_dirs:
        # "PurePath.relative_to() requires self to be the subpath of the argument, but os.path.relpath() does not."
        # See https://docs.python.org/3/library/pathlib.html#id4 and
        # See https://stackoverflow.com/questions/67452690/pathlib-path-relative-to-vs-os-path-relpath
        yml_dir_rel = os.path.relpath(yml_dir)  # w.r.t. current working directory
        pattern_yml = str(Path(yml_dir_rel) / '**/*.yml')
        yml_paths_sorted = sorted(glob.glob(pattern_yml, recursive=True), key=len, reverse=True)
        Path('autogenerated/schemas/workflows/').mkdir(parents=True, exist_ok=True)
        if len(yml_paths_sorted) == 0:
            print(f'Warning! No yml files found in {yml_dir_rel}.\nCheck {yml_dirs_file.absolute()}')
            print('This almost certainly means you are not in the correct directory.')
        yml_paths = {}
        for yml_path_str in yml_paths_sorted:
            # Exclude our autogenerated inputs files
            if '_inputs' not in yml_path_str:
                yml_path = Path(yml_path_str)
                yml_paths[yml_path.stem] = yml_path
        # Check for existing entry (so we can split a single
        # namespace across multiple lines in yml_dirs.txt)
        ns_dict = yml_paths_all.get(yml_namespace, {})
        yml_paths_all[yml_namespace] = {**ns_dict, **yml_paths}

    return yml_paths_all