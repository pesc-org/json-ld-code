from rdflib import Graph
from rdflib import Dataset
import sys
import json

project_path = "C:\\Users\\micha\\PycharmProjects\\json-ld-code\\pesc_json\\"
# 1. Your input JSON-LD data (as a string or loaded from a file)pyth
input_path = project_path + sys.argv[1]
print(input_path)
output_path = project_path + sys.argv[3]
print(output_path)
rdf_input_format = sys.argv[2]
rdf_output_format = sys.argv[4]
# input_path = "jsonld_instance\person.json-ld"
# rdf_input_format = "json-ld"
# output_path = "converted_rdf\person.ttl"
# rdf_output_format = "turtle"

# formats
# turtle: turtle, ttl, turtle2
# rdf/xml: xml pretty-xml
# json-ld: json-ld
# n-triples: ntriples nt nt11
# notation-3: n3
# trig: trig
#n-guads: nquads
# trix: trix

# 2. Create an RDFLib Graph
g = Graph()
# g = Dataset()

# Parse the JSON-LD data into the graph
# The format 'json-ld' is automatically detected or can be specified.
with open(input_path) as file:
    data = str(file.read())
    g.parse(data=data, format=rdf_input_format)

# Serialize the graph to the desired RDF format (e.g., Turtle)
rdf_output = g.serialize(format=rdf_output_format)
print(rdf_output)

# store the result
print(f"--- Converted {rdf_input_format} to  {rdf_output_format} format ---")
with open(output_path, 'w') as fd:
    fd.write(rdf_output)
    fd.close()
