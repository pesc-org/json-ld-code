import json
import re
import xml.etree.ElementTree as ET
import os
import sys
import xmlschema
from xmlschema.validators import (XsdAnyElement, XsdAtomicRestriction, XsdAtomicBuiltin, XsdElement,
                                  XsdAttribute, XsdGroup)

xsd_types = {"base64Binary": "string", "boolean": "boolean", "byte": "integer", "date": "string", "dateTime": "string",
             "dateTimeStamp": "string", "dayTimeDuration": "integer", "decimal": "number", "double": "number",
             "duration": "number", "float": "number", "gDay": "string", "gMonth": "string", "gMonthDay": "string",
             "gYear": "string", "gYearMonth": "string", "hexBinary": "string", "int": "integer", "integer": "integer",
             "language": "string", "long": "integer", "Name": "string", "negativeInteger": "integer",
             "nonNegativeInteger": "integer", "nonPositiveInteger": "integer", "normalizedString": "integer",
             "positiveInteger": "integer", "precisionDecimal": "number",
             "short": "integer", "string": "string", "time": "string", "token": "string",
             "unsignedByte": "integer", "unsignedInt": "integer", "unsignedLong": "integer",
             "unsignedShort": "integer", "yearMonthDuration": "string"}

xsd_patterns = {"base64binary": "^[a-fA-F0-9]*$",
                "gYearMonth": "^[1-2][0-9]{3}-([0][1-9]|[1][0-2])$",
                "gMonth": "^[0][1-9][1][0-2]$",
                "gMonthDay": "^[0][1-9][1][0-2]-([0][1-9]|[1-2][0-9]|[3][0-1])$"
                }
xsd_format = {"date": "date", "dateTime": "date-time"}
xsd_facet = {"length": "maxLength",
             "minLength": "minLength",
             "maxLength": "maxLength",
             "pattern": "pattern",
             "maxInclusive": "maximum",
             "maxExclusive": "exclusiveMaximum",
             "minExclusive": "exclusiveMinimum",
             "minInclusive": "minimum"}


class ProcessXMLSchema:
    def __init__(self, file_path, root_element_name, debug=False):
        self.schema = xmlschema.XMLSchema(file_path)
        self.debug = debug
        self.root_element_name = root_element_name
        self.root_element = self.schema.elements[root_element_name]
        self.definitions = dict()
        self.import_schemas = dict()
        self.import_schemas[self.schema.target_namespace] = ET.parse(file_path)
        for key in self.schema.imports.keys():
            import_schema = self.schema.imports[key]
            if self.debug:
                print(import_schema.target_namespace)
            import_file = "\\".join(file_path.split('\\')[:-1]) + "\\" + import_schema.name
            self.import_schemas[import_schema.target_namespace] = ET.parse(import_file)

    def get_types(self):
        for component in self.schema.simple_types:
            if self.debug:
                print(component.tostring())


    def list_components(self, schema):
        for xsd_component in schema.iter_components():
            print(xsd_component)
        for import_schema in schema.imports.keys():
            next_schema = schema.imports[import_schema]
            print(next_schema)
            for xsd_component in next_schema.complex_types:
                print(xsd_component)

    def create_schemas(self, schema, schemas):
        for import_schema in schema.imports.keys():
            next_schema = schema.imports[import_schema]
            if len(next_schema.imports) > 0:
                schemas = self.create_schemas(next_schema, schemas)
            prefix = next_schema.target_prefix
            schemas[prefix] = next_schema
        return schemas

    def get_type(self, prefixed_name, schemas):
        split_name = prefixed_name.split(':')
        prefix = split_name[0]
        name = split_name[1]
        schema = schemas[prefix]
        type = schema.types[name]
        print('type: ', type)
        return type

    def process_group_old(self, group):
        print('    group: ', group.elem)
        for child in group.elem:
            print('    group child name: ', child.tag, end=' ')
            if 'name' in child.attrib.keys():
                print('name=', child.attrib['name'], end=' ')
            if 'type' in child.attrib.keys():
                print('type=', child.attrib['type'])

    def get_documentation(self, xml_string):
        match = re.match(r".*<xs:documentation>([^<]*)<", xml_string, flags=re.S)
        if match is None:
            return ""
        else:
            return match.group(1)

    def get_enum_documentation_backup(self, simple_type):
        xml_string = simple_type.tostring()
        print('enum string:', xml_string)
        match = re.findall(r"<xs:documentation>([^<]*)<", xml_string, flags=re.S)
        comment = ""
        for enum in simple_type.enumeration:
            comment += enum + ": " + match.pop(0) + "\n"
        return comment

    def get_enum_documentation(self, simple_type):
        xml_string = simple_type.tostring()
        enums = xml_string.split('</xs:enumeration>')[0:-1]
        comment = ""
        for enum in enums:
            documentation = self.get_documentation(enum)
            enumeration = re.match(r'.*value="([^"]*)"', enum, flags=re.S).group(1)
            comment += enumeration + ": " + documentation + '\n'
        return comment

    def get_facet_value(self, facet):
        xml_string = facet.tostring()
        pattern = r'<xs:([^ ]*) .* value=\"([^\"]*)\"'
        match = re.match(pattern, xml_string, flags=re.S)
        if match is None:
            return "", ""
        else:
            return match.group(1), match.group(2)

    def get_simple_documentation(self, simple_type):
        """documentation is not present is schema so must use etree to get comment"""
        if simple_type.qualified_name is None:
            return ""
        xsd_namespace = '{http://www.w3.org/2001/XMLSchema}'
        namespace_name = simple_type.qualified_name.split("}")[0][1:]
        type_name = simple_type.local_name
        xpath = f"./{xsd_namespace}simpleType[@name='{type_name}']//{xsd_namespace}documentation"
        s = self.import_schemas[namespace_name]
        root = s.getroot()
        elem = root.find(xpath)
        if elem is not None:
            data = elem.text
            return data
        else:
            return ""

    def is_attribute_required(self, attribute):
        xml_string = attribute.tostring()
        pattern = r'<xs:attribute.* use=\"([^\"]*)\"'
        match = re.match(pattern, xml_string, flags=re.S)
        if match is None:
            return False
        else:
            return match.group(1) == 'required'

    def get_import_schema(self, xsd_component):
        namespace = xsd_component.qualified_name.spilt("}")[0][1:]
        return self.import_schemas[namespace]

    def get_attributes(self, component):
        """documentation is not present is schema so must use etree to get comment"""
        schema = dict()
        print('component: ', component)
        if component.qualified_name is None:
            return "None"
        xsd_namespace = '{http://www.w3.org/2001/XMLSchema}'
        namespace_name = component.qualified_name.split("}")[0][1:]
        print('namespace name: ', namespace_name)
        type_name = component.local_name
        print('local_name', type_name)
        xpath = f"./*[@name='{type_name}']//{xsd_namespace}attribute"
        # [@name='{type_name}']//{xsd_namespace}attribute"
        print(xpath)
        s = self.import_schemas[namespace_name]
        root = s.getroot()
        print(root.tag)
        xsd_attributes = root.findall(xpath)
        print(xsd_attributes)
        for attr in xsd_attributes:
            print('name: ', attr.attrib['name'])
            if 'type' in attr.attrib.keys():
                print('type: ', attr.attrib['type'])
            if 'use' in attr.attrib.keys():
                print('use: ', attr.attrib['use'])
            print('this schema includes attributes')

    def process_model_group(self, model_group: XsdGroup, schema: dict):
        required = dict()
        for element in model_group.iter_elements():
            required = {'required': [element.local_name]}
            schema['properties'][element.local_name] = self.process_element(element)
            if model_group.model == 'choice':
                if model_group.min_occurs == 1 and model_group.max_occurs == 1:
                    if 'oneOf' not in schema.keys():
                        schema['oneOf'] = list()
                    schema['oneOf'].append(required)
                elif model_group.min_occurs == 1 and model_group.max_occurs > 1:
                    if 'anyOf' not in schema.keys():
                        schema['anyOf'] = list()
                    schema['anyOf'].append(required)
            elif model_group.model == 'sequence':
                for sub_element in element:
                    if isinstance(sub_element, XsdGroup):
                        self.process_model_group(sub_element, schema)
                    elif isinstance(sub_element, XsdElement):
                        schema['properties'][element.local_name] = self.process_element(element)
                        if element.min_occurs > 0:
                            schema['required'].append(element.local_name)
        return schema


    def process_complex_type(self, complex_type):
        """create a json object with elements from complex type"""
        model_group = complex_type.content
        schema = dict()
        schema['type'] = 'object'
        schema['description'] = self.get_documentation(model_group.tostring())
        schema['properties'] = dict()
        schema['additionalProperties'] = False
        schema['required'] = list()
        for element in model_group:
            if isinstance(element, XsdGroup):
                self.process_model_group(element, schema)
            else:
                schema['properties'][element.local_name] = self.process_element(element)
                if element.min_occurs > 0:
                    schema['required'].append(element.local_name)
        while len(complex_type.attributes) > 0:
            item = complex_type.attributes.popitem()
            schema['properties'][item[0]] = self.process_element(item[1])
            if self.is_attribute_required(item[1]):
                schema['required'].append(item[0])
        if len(schema['required']) == 0:
            schema.pop('required')
        return schema

    def process_simple_type(self, element):
        simple_type = element.type
        schema = dict()
        base_name = None
        if simple_type.base_type.local_name in xsd_types.keys():
            base_name = simple_type.base_type.local_name
            schema['type'] = xsd_types[base_name]
            if simple_type.enumeration is not None:
                schema['description'] = self.get_enum_documentation(simple_type)
                schema['enum'] = list()
                for enum in simple_type.enumeration:
                    schema['enum'].append(enum)
            else:  # regular simple type
                schema['description'] = self.get_simple_documentation(simple_type)
            if base_name in xsd_format.keys():
                schema['format'] = xsd_format[base_name]
            if base_name in xsd_patterns.keys():
                schema['pattern'] = xsd_patterns[base_name]
            for key in simple_type.facets.keys():
                facet = simple_type.facets[key]
                facet_name, facet_value = self.get_facet_value(facet)
                if facet_name in xsd_facet.keys():
                    if facet_value.isnumeric():
                        facet_value = int(facet_value)
                    schema[xsd_facet[facet_name]] = facet_value
        return schema

    def process_simple_content(self, simple_element):
        """process elements that have no constraints and a builtin type"""
        schema = dict()
        schema['type'] = xsd_types[simple_element.type.local_name]
        schema['description'] = self.get_documentation(simple_element.tostring())
        return schema

    def process_element(self, element):
        schema = dict()
        sub_schema = dict()
        if type(element) in [XsdAnyElement]:
            pass
        elif element.type.is_complex():  # element with children
            if element.type.has_complex_content():  # complex element with subelement
                name = element.local_name
                if self.debug:
                    print('element: ', element)
                    print('element type: ', element.type)
                    print('element type content: ', element.type.content)
                    print()
                if element.type.qualified_name is None:
                    schema = self.process_complex_type(element.type)
                else:
                    if element.max_occurs is None or element.max_occurs > 1:
                        schema['type'] = 'array'
                        if element.min_occurs > 0:
                            schema['minItems'] = element.min_occurs
                        schema['items'] = dict()
                        schema['items']['$ref'] = '#/definitions/' + element.type.prefixed_name
                        schema['items']['description'] = self.get_documentation(element.tostring())
                    else:
                        schema['$ref'] = '#/definitions/' + element.type.prefixed_name
                        schema['description'] = self.get_documentation(element.tostring())
                    if element.type.prefixed_name not in self.definitions.keys():
                        self.definitions[element.type.prefixed_name] = self.process_complex_type(element.type)
        elif element.type.is_simple():
            if self.debug:
                print('simple element: ', element)
                print('simple element type:', element.type)
            if type(element.type) == XsdAtomicBuiltin:
                sub_schema = self.process_simple_content(element)
            elif type(element.type) == XsdAtomicRestriction:
                sub_schema = self.process_simple_type(element)
            if type(element) == XsdElement and (element.max_occurs is None or element.max_occurs > 1):
                schema['type'] = 'array'
                schema['items'] = dict()
                if element.type.prefixed_name is not None:
                    schema['items']['$ref'] = '#/definitions/' + element.type.prefixed_name
                    schema['items']['description'] = self.get_documentation(element.tostring())
                else:
                    schema['items'] = sub_schema
                    schema['description'] = self.get_documentation(element.tostring())
            else:
                if element.type.prefixed_name is not None:
                    schema['$ref'] = '#/definitions/' + element.type.prefixed_name
                    schema['description'] = self.get_documentation(element.tostring())
                else:
                    schema = sub_schema
            if (element.type.prefixed_name not in self.definitions.keys() or element.type.prefixed_name is not None) \
                    and type(element) not in (XsdAtomicBuiltin, XsdAtomicRestriction, XsdAttribute):
                self.definitions[element.type.prefixed_name] = sub_schema
        else:
            print('not processed:', element.type, end='\n\n')
            exit(0)

        return schema

    def delete_properties(self, search_keys: list, schema):
        if isinstance(schema, dict):
            search_schema = dict()
            for key in schema.keys():
                if key not in search_keys:
                    search_schema[key] = self.delete_properties(search_keys, schema[key])
        elif isinstance(schema, list):
            search_schema = list()
            for list_item in schema:
                if list_item not in search_keys:
                    search_schema.append(self.delete_properties(search_keys, list_item))
        else:
            search_schema = schema
        return search_schema

    def remove_prefixes(self, prefixes, schema):
        json_string = json.dumps(schema)
        for prefix in prefixes:
            json_string = json_string.replace(prefix, "")
        return json.loads(json_string)

    def __fix_pattern(self, pattern):
        new_pattern = pattern
        if pattern[0] != "^":
            new_pattern = "^" + new_pattern
        if pattern[-1] != '$':
            new_pattern = new_pattern + "$"
        new_pattern = new_pattern.replace("\\d", "[0-9]")
        return new_pattern

    def fix_regular_expressions(self, schema):
        pattern = 'pattern'
        if isinstance(schema, dict):
            if pattern in schema.keys():
                pattern_value = schema[pattern]
                schema[pattern] = self.__fix_pattern(pattern_value)
            else:
                for key in schema.keys():
                    self.fix_regular_expressions(schema[key])
        elif isinstance(schema, list):
            for element in schema:
                self.fix_regular_expressions(element)
        return


    def process_schema(self, file_name, delete_properties=None, delete_prefixes=None):
        json_schema = dict()
        json_schema['$schema'] = "http://json-schema.org/draft-07/schema#"
        json_schema['$id'] = f"https://www.pesc.org/json-schemas/{self.root_element_name}"
        json_schema.update(self.process_complex_type(self.root_element.type))
        json_schema['definitions'] = self.definitions
        if delete_properties is not None:
            json_schema = self.delete_properties(delete_properties, json_schema)
        if delete_prefixes is not None:
            json_schema = self.remove_prefixes(delete_prefixes, json_schema)
        self.fix_regular_expressions(json_schema)
        file = file_name
        with open(file, "w") as fp:
            json.dump(json_schema, fp, indent=4)
        return json_schema

def main():
   if not ("\\" in sys.argv[1] or "/" in sys.argv[1]):
       xml_file_path = os.getcwd() + f"\\xml_schemas\\{sys.argv[1]}"
   else:
       xml_file_path = sys.argv[1]
   if not("\\" in sys.argv[1] or "/" in sys.argv[1]):
       json_file_path = os.getcwd() + f"\\json_schemas\\{sys.argv[2]}"
   else:
       json_file_path = sys.argv[2]
   pxs = ProcessXMLSchema(xml_file_path, sys.argv[3])
   json_schema = pxs.process_schema(json_file_path,
                                    delete_properties=("UserDefinedExtensions", "core:UserDefinedExtensionsType"),
                                    delete_prefixes=('core:', 'AcRec:'))

if __name__ == "__main__":
    main()




