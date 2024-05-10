import json
from pyshacl import validate
from rdflib.graph import Graph
def validate_json_ld(data_file, shacl_file):
    data_graph = Graph()
    data_graph.parse(data_file)
    shacl_graph = Graph()
    shacl_graph.parse(shacl_file)
    r = validate(
        data_graph,
        shacl_graph=shacl_graph,
        ont_graph=None,
        inference='none',
        abort_on_first=False,
        allow_warnings=False,
        meta_shacl=False,
        advanced=False,
        js=False,
        debug=False)
    conforms, result_graph, result_text = r
    json_string = result_graph.serialize(format='json-ld', indent=4)
    with open('out/results_graph.json', 'w') as fp:
        fp.write(json_string)
    report = json.loads(json_string)
    PREFIX = "http://www.w3.org/ns/shacl#"
    success = report[0][PREFIX + 'conforms'][0]['@value']
    if success:
        print('The json-ld is valid')
    else:
        print('json-ld file failed validation')
        print()
    for error in report[1:]:
        for key in error.keys():
            if key == PREFIX + 'focusNode':
                print('focus node:', error[key][0]['@id'])
            elif key == PREFIX + 'resultPath':
                print('result path:', error[key][0]['@id'])
                print()
            elif key == PREFIX + 'resultMessage':
                print('message:', error[key][0]['@value'])

def rdf_convert(infile, outfile):
    data_graph = Graph()
    data_graph.parse(infile)
    map = {'json-ld': 'json-ld', 'ttl': 'turtle'}
    format = map[outfile.split('.')[-1]]
    with open(outfile, 'w') as fp:
        fp.write(data_graph.serialize(format=format, indent=4))



if __name__ == "__main__":
    done = False
    while not done:
        input_value = input("operation: ")
        if input_value == "convert":
            rdf_convert('shacl/student_courses.ttl', 'out/student_courses_shacl_ttl2jsonld.json-ld')
        elif input_value == "validate":
            # validate_json_ld('shacl/courses.json-ld', 'shacl/courses.ttl')
            validate_json_ld('shacl\\student_courses.json-ld', 'shacl\\student_courses.ttl')
        elif input_value == 'end':
            done = True
        else:
            print (f"No such operation as {input_value}")
