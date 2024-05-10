echo off
pyshacl -s shacl/student_courses.ttl -sf turtle -f human shacl/student_courses_revised.json-ld -df json-ld
rem pyshacl -s shacl/student_courses_shacl.json-ld -sf json-ld -f human shacl/student_courses_revised.json-ld -df json-ld
rem pyshacl -s out/student_courses_jsonld2ttl.ttl -sf turtle -f human shacl/student_courses_revised.json-ld -df json-ld
rem pyshacl -s shacl/clean-shacl.ttl -sf turtle -f human shacl/minimal_passing.json-ld -df json-ld