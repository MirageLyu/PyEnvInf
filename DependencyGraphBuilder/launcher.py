import DockerfileParser
import RequirementsParser
import os

# DockerfileParser.parse("sample_dockerfile/files/", 50000)
# RequirementsParser.reparseOutputRecursively("out.log")

# RequirementsParser.parse("sample_requirements/files/", 50000)
# RequirementsParser.reparseOutputRecursively("reqout.log")

out = open("samples.data", "w")
fa = open("out.log5", "r")
fb = open("reqout.log5", "r")

linesa = fa.read().splitlines()
linesb = fb.read().splitlines()
for line in linesa:
    print(line, file=out)
for line in linesb:
    print(line, file=out)