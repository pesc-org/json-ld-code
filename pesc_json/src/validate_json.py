import json
import jsonschema
import time
import os
import sys

def include_error(message):
    """
    function to exclude any errors that violate the schema but are now accepted as valid
    currently there are no such exceptions
    """
    return True

def validate_json(json_instance_fn, json_schema_fn, report_fn):
    schema_fp = open(json_schema_fn, "r")
    instance_fp = open(json_instance_fn, "r")
    output_fp = open(report_fn, "a")
    instance = json.load(instance_fp)
    output_fp.write("\nDate: " + time.strftime('%c') + "\n")
    schema = json.load(schema_fp)
    v = jsonschema.Draft7Validator(schema, format_checker=jsonschema.FormatChecker(('date', 'time',)))
    success = True
    for error in sorted(v.iter_errors(instance), key=str):
        if include_error(error.message):
            success = False
            line = error.message + " json path: " + "$"
            for item in list(error.path):
                if type(item) is int:
                    line += "[" + str(item) + "]"
                else:  # string variable
                    line += "." + item
            print(line)
            line += "\n"
            output_fp.write(line)
    return success

def main():
    if not ("\\" in sys.argv[1] or "/" in sys.argv[1]):
        instance_file = os.getcwd() + "\\json_instance\\HSTranscript_fixed.json"
    else:
        instance_file = sys.argv[1]
    if not ("\\" in sys.argv[2] or "/" in sys.argv[2]):
        schema_file = os.getcwd() + "\\json_schemas\\HST_schema.json"
    else:
        schema_file = sys.argv[2]
    if not ("\\" in sys.argv[3] or "/" in sys.argv[3]):
        report_file = os.getcwd() + "\\report\\HSReport.txt"
    else:
        report_file = sys.argv[3]
    validate_json(instance_file, schema_file, report_file)


if __name__ == "__main__":
    main()