"""CWL generation for ICT objects.""" ""

from typing import TypeVar

ICT = TypeVar("ICT")


def requirements(ict_: ICT, network_access: bool) -> dict:
    """Return the requirements from an ICT object."""
    reqs = {}
    reqs["DockerRequirement"] = {"dockerPull": ict_.container}  # type: ignore
    output_names = [io.name for io in ict_.outputs]  # type: ignore
    if "outDir" in output_names:
        reqs["InitialWorkDirRequirement"] = {
            "listing": [{"entry": "$(inputs.outDir)", "writable": True}]
        }
        reqs["InlineJavascriptRequirement"] = {}
    if network_access:
        reqs["NetworkAccess"] = {"networkAccess": True}
    return reqs


def clt_dict(ict_: ICT, network_access: bool) -> dict:
    """Return a dict of a CommandLineTool from an ICT object."""

    clt_ = {
        "class": "CommandLineTool",
        "cwlVersion": "v1.2",
        "inputs": {
            io.name: io._input_to_cwl()  # pylint: disable=W0212
            for io in ict_.inputs + ict_.outputs  # type: ignore
        },
        "outputs": {
            io.name: io._output_to_cwl([io.name for io in ict_.inputs])  # pylint: disable=W0212
            for io in ict_.outputs  # type: ignore
        },
        "requirements": requirements(ict_, network_access),
        "baseCommand": ict_.entrypoint,
        "label": ict_.title,
        "doc": str(ict_.documentation),
    }
    
    return clt_

def remove_none(d):
    """Recursively remove keys with None values."""
    if isinstance(d, dict):
        return {k: remove_none(v) for k, v in d.items() if v is not None}
    elif isinstance(d, str):
        return d  # Return the string unchanged
    else:
        return d  # Return other types of values unchanged

def input_output_dict(ict_: ICT) -> dict:
    """Return a input or output dictionary from an ICT object."""
    io_dict = {}
    for prop in ict_:
        io_dict[prop.name] = {
            'type': prop.io_type.value,
            'description': prop.description,
            'defaultValue': prop.defaultValue,
            'required': prop.required,
            'format': prop.io_format,
        }
    # recursively remove keys with None values
    return remove_none(io_dict)

def ui_dict(ict_: ICT) -> dict:
    """Return a CommandLineTool from an ICT object."""
    ui_list = []
    for prop in ict_:
        prop_dict = {
            'key': prop.key.root,  # Assuming 'root' attribute contains the actual key
            'title': prop.title,
            'description': prop.description,
            'type': prop.ui_type
        }
        if prop.customType:
            prop_dict['customType'] = prop.customType
        if prop.condition:
            prop_dict['condition'] = prop.condition.root
        if prop.ui_type == 'select':
            prop_dict['fields'] = prop.fields
        ui_list.append(prop_dict)
    return ui_list

def hardware_dict(ict_: ICT) -> dict:
    """Return a CommandLineTool from an ICT object."""
    hardware_dict = {
        'cpu.type': ict_.cpu_type,
        'cpu.min': ict_.cpu_min,
        'cpu.recommended': ict_.cpu_recommended,
        'memory.min': ict_.memory_min,
        'memory.recommended': ict_.memory_recommended,
        'gpu.enabled': ict_.gpu_enabled,
        'gpu.required': ict_.gpu_required,
        'gpu.type': ict_.gpu_type
    }
    return hardware_dict

def ict_dict(ict_: ICT) -> dict:
    """Return a CommandLineTool from an ICT object."""
    inputs_dict = input_output_dict(ict_.inputs)
    outputs_dict = input_output_dict(ict_.outputs)
    clt_ = {
        "inputs": inputs_dict,
        "outputs": outputs_dict,
        "ui": ui_dict(ict_.ui)
    }
    if ict_.hardware is not None:
        clt_["hardware"] = hardware_dict(ict_.hardware)
    return clt_
