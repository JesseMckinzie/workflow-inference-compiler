czi_extract_ict = {'author': ['Author One'],
 'contact': 'test@test.com',
 'container': 'polusai/czi-extract-plugin:1.1.1',
 'description': 'Extracts individual fields of view from a CZI file. Saves as '
                'OME TIFF.',
 'entrypoint': '[python3, main.py]',
 'inputs': [{'description': 'Input collection',
             'format': ['genericData'],
             'name': 'inpDir',
             'required': True,
             'type': 'path'},
            {'description': 'Input collection',
             'format': ['genericData'],
             'name': 'outDir',
             'required': True,
             'type': 'path'}],
 'name': 'polusai/ExtractTIFFsFromCZI',
 'outputs': [{'description': 'Output data for the plugin',
              'format': ['collection'],
              'name': 'outDir',
              'required': True,
              'type': 'path'}],
 'repository': 'https://github.com/polusai/image-tools',
 'specVersion': '1.0.0',
 'title': 'Extract TIFFs From CZI',
 'ui': [{'description': 'Collection name...',
         'key': 'inputs.inpDir',
         'title': 'Input collection: ',
         'type': 'path'}],
 'version': '1.1.1'}

czi_extract_clt = {'baseCommand': '[python3, main.py]',
 'class': 'CommandLineTool',
 'cwlVersion': 'v1.2',
 'doc': 'None',
 'inputs': {'inpDir': {'inputBinding': {'prefix': '--inpDir'},
                       'type': 'Directory'},
            'outDir': {'inputBinding': {'prefix': '--outDir'},
                       'type': 'Directory'}},
 'label': 'Extract TIFFs From CZI',
 'outputs': {'outDir': {'outputBinding': {'glob': '$(inputs.outDir.basename)'},
                        'type': 'File'}},
 'requirements': {'DockerRequirement': {'dockerPull': 'polusai/czi-extract-plugin:1.1.1'},
                  'InitialWorkDirRequirement': {'listing': [{'entry': '$(inputs.outDir)',
                                                             'writable': True}]},
                  'InlineJavascriptRequirement': {}}}