# -*- coding: utf-8 -*-
"""
Created on Wed Mar 28 15:11:52 2018

@author: MorrisM
"""

import xmlschema
import json
from datetime import datetime
from xml.etree import ElementTree
import sys


def create_converter():
    return xmlschema.converters.XMLSchemaConverter(
        namespaces=None,
        dict_class=None,
        list_class=None, text_key='value',
        attr_prefix='', cdata_prefix=None,
    )


schema_fn = sys.argv[1]
instance_fn = sys.argv[2]
doc_request_schema = xmlschema.XMLSchema(f"xml_schemas\\{schema_fn}")
tree = ElementTree.parse(f"xml_instance\\{instance_fn}")
root = tree.getroot()
print(root.tag)
dict_form = doc_request_schema.to_dict(f"xml_instance\\{instance_fn}", decimal_type=float, converter=create_converter())
json_form = json.dumps(dict_form, indent=2)
date = datetime.now().strftime('%y_%m_%d_%H_%M')
with open(f"report\\{'.'.join(instance_fn.split('.')[0:-1])}.json", 'w') as fd:
    fd.write(json_form)
    fd.close()
