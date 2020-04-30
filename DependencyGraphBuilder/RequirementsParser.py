import re
import pydbc
import os
import netutils

pjf = open("pinjie.log", "w")

def is_url(line):
    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, line)

def parseline(line, fff, pathprefix):
    onearg_dismiss_flag = False
    requirements_flag = False
    vcs_flag = False
    onearg_dismiss_lst = ["-i", "--index-url", "--extra-index-url", "-c",
                          "--constraint", "-t", "--target", "--platform",
                          "--python-version", "--implementation", "--abi",
                          "--root", "--prefix", "-b", "--build", "--src",
                          "--upgrade-strategy", "--install-option",
                          "--global-option", "--no-binary", "--only-binary",
                          "--progress-bar", "-f", "--find-links", "--timeout",
                          "--index"]
    dismiss_lst = ["--no-deps", "--pre", "--user", "-U", "--upgrade",
                   "--force-reinstall", "-I", "--ignore-installed",
                   "--ignore-requires-python", "--no-build-isolation",
                   "--use-pep517", "--compile", "--no-compile",
                   "--no-warn-script-location", "--no-warn-conflicts",
                   "--prefer-binary", "--no-clean", "--require-hashes",
                   "--no-index", "--no-cache-dir", "--no-use-pep517", "--cache-dir"]
    requirements_lst = ["-r", "--requirement", "-Ur", "-rU"]
    vcs_lst = ["-e", "--editable"]
    
    lexes = line.split()
    for lex in lexes:
        result = lex.split("==")[0].split("<=")[0].split("<")[0].split(">=")[0].split(">")[0].split("!=")[0].split("~=")[0]
        result = result.split("=")[0]
        if result in dismiss_lst:
            continue
        if result in onearg_dismiss_lst:
            onearg_dismiss_flag= True
            continue
        if onearg_dismiss_flag:
            onearg_dismiss_flag = False
            continue
        
        if re.match("-r.*", result):
            requirements_flag=True
            result = result[2:]
        
        if result in requirements_lst:
            requirements_flag = True
            continue
        if requirements_flag:
            if re.match("/.*", result):
                result = pathprefix+result
            else:
                result = pathprefix + "/" + result
            print("拼接拼接Result!!!!  " + result, file=pjf)
            result = "req_" + result
            requirements_flag = False
        if result in vcs_lst:
            vcs_flag = True
            continue
        if vcs_flag:
            vcs_flag = False
            if not is_url(result):
                continue
            result = "vcs_" + result
                
        if re.match("\..*", result) or re.match("/.*", result):
            continue
        if re.match("git+.*", result) or is_url(result) or re.match("hg+.*", result) or re.match("svn+.*", result) or re.match("bzr+.*", result):
            result = "vcs_" + result
        
        try:
            print("pip_" + result + " ", file=fff, end='')
        except Exception:
            pass


def parsefile(filepath, fff):
    f = open(filepath, "r", encoding="utf-8")
    lines = f.read().splitlines()

    
    comment_re = "#.*"
    none_re = "[0-9]{3}.*"
    
    for line in lines:
        line = line.strip()
        if re.match(comment_re, line) or re.match(none_re, line) or re.match("--.*", line):
            continue
        
        line = line.split("#")[0].strip().split(";")[0].strip().split("==")[0].split("<=")[0].split("<")[0].split(">=")[0].split(">")[0].split("!=")[0].strip()
        parseline(line, fff)
        
def parseContent(lines, fff, pathprefix):
    comment_re = "#.*"
    none_re = "[0-9]{3}.*"
    
    for line in lines:
        line = line.strip()
        if re.match(comment_re, line) or re.match(none_re, line) or re.match("--.*", line):
            continue
        
        line = line.split("#")[0].strip().split(";")[0].strip().split("==")[0].split("<=")[0].split("<")[0].split(">=")[0].split(">")[0].split("!=")[0].strip()
        parseline(line, fff, pathprefix)

    
    
def removeEmptyLines(filename, outfile):
    f = open(filename, "r")
    wf = open(outfile, "w")
    lines = f.read().splitlines()
    for line in lines:
        if len(line.split())>=2:
            wf.write(line.strip() + "\n")
    f.close()
    wf.close()

def parse(path, r):
    fff = open("reqout.log", "w")
    for i in range(r):
        filepath = path + str(i) + "/requirements.txt"
        if not os.path.exists(filepath):
            continue
    
        print(str(i))
        print(str(i) + " ", file=fff, end='')
        parsefile(filepath, fff)
        print("", file=fff)
    fff.close()
    removeEmptyLines("reqout.log", "reqout.log2")
    os.remove("reqout.log")
    
def reparseOutput(outlogfile, output):
    dirtyFlag = False
    
    db = pydbc.DBUtils("url.db")
    ff = open(output, "w")
    
    f = open(outlogfile, "r")
    lines = f.read().splitlines()
    index = 0
    for line in lines:
        print(index)
        index += 1
        tokens = line.split(" ")
        id = tokens[0]
        r = ""
        for i in range(len(tokens)):
            if re.match("pip_req_.*", tokens[i]):
                dirtyFlag = True
                
                remotepath = db.getRemotePathByID(id)
                relativepath = tokens[i].split("_", 2)[2]
                if re.match("/.*", relativepath):
                    remotepath += relativepath
                else:
                    remotepath += "/" + relativepath
                exc_flag, content = netutils.downloadSingleFileToMemory(remotepath)
                
                if exc_flag:
                    continue
                
                llines = content.splitlines()
                for ii in range(len(llines)):
                    llines[ii] = str(llines[ii], encoding="utf-8")
                
                ssss = relativepath.strip("/").rsplit("/", 1)
                pathprefix = ""
                if not len(ssss)==1:
                    pathprefix = relativepath.strip("/").rsplit("/", 1)[0]                
                tmpf = open("out.tmp", "w")
                parseContent(llines, tmpf, pathprefix)
                tmpf.close()
                
                itmpf = open("out.tmp", "r")
                l = itmpf.read().splitlines()
                lresult = ""
                if len(l)>0:
                    lresult = l[0].strip()
                    
                tokens[i] = lresult
                r += lresult
                itmpf.close()
                
                os.remove("out.tmp")
            else:
                r += tokens[i] + " "
        print(r.strip(), file=ff)
    f.close()
    return dirtyFlag

def reparseOutputRecursively(prefix):
    index = 2
    path = prefix
    while reparseOutput(path + str(index), path + str(index + 1)):
        index += 1
                
                
    
    
    
# parse("sample_requirements/files/", 2000)
    