import re
import os
import csv
from dockerfile_parse import DockerfileParser
import json
import bashlex
from bashlex import ast

env_dict = {}

class nodevisitor(ast.nodevisitor):
    def __init__(self, positions, fff):
        self.positions = positions
        self.fff = fff
    def visitcommand(self, n, parts):
        # parse apt-get packages
        Commands = ["update", "upgrade", "dist-upgrade", "install",
                    "remove", "source", "check", "clean", "autoclean",
                    "autoremove", "build", "build-dep"]
        Option_re = "-.*"
        Config_re = "[A-Za-z]*::.*"
        topenv_re = "\$.*"
        innerenv_re = "[^\$]+\$.*"
        aptget_flag = False
        install_flag = False
        for child in n.parts:
            if child.word == "apt-get":
                aptget_flag = True
            if aptget_flag == False:
                break
            if child.word == "install":
                install_flag = True
            if child.word in Commands:
                continue
            if re.match(Option_re, child.word) or re.match(Config_re, child.word):
                continue
            if install_flag:
                # remove version info
                result = child.word.split("=")[0]
                
                # parse top env
                if re.match(topenv_re,  result):
                    print("Matched:  " + result)
                    if result.split("$")[1].strip() in env_dict.keys():
                        result = env_dict[result.split("$")[1]]
                    else:
                        continue
                    if result is None or result == "":
                        continue
                # parse inner env
                inner_finish_flag = True
                while re.match(innerenv_re, result):
                    print("Matched..: " + result)
                    pre = result.split("$")[0]
                    env = result.split("$")[1].split("}")[0].split("{")[1]
                    post = ""
                    if len(result.split("}"))>1:
                        post = result.split("}")[1]
                    if env in env_dict.keys():
                        result = pre +env_dict[env] + post
                    else:
                        inner_finish_flag = False
                        break
                if not inner_finish_flag:
                    continue
                
                if len(result.split(" "))>1:
                    for p in result.strip().split(" "):
                        p = p.strip("'").strip('"')
                        if p in Commands:
                            continue
                        if re.match(Option_re, p) or re.match(Config_re, p):
                            continue
                        print("apt_" + p, file=self.fff, end='')
                else:
                    print("apt_" + result + " ", file=self.fff, end='')
        
        # parse pip packages
        pip_flag = False
        pipinstall_flag = False
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
        
        for child in n.parts:
            if child.word == "pip":
                pip_flag = True
            if not pip_flag:
                break
            if child.word == "install":
                pipinstall_flag = True
                continue
            if pipinstall_flag:
                # remove version info
                result = child.word.split("==")[0].split("<=")[0].split("<")[0].split(">=")[0].split(">")[0]
                
                # parse top env
                if re.match(topenv_re,  result):
                    print("Matched:  " + result)
                    if result.split("$")[1].strip() in env_dict.keys():
                        result = env_dict[result.split("$")[1]]
                    else:
                        continue
                    if result is None or result == "":
                        continue
                # parse inner env
                inner_finish_flag = True
                while re.match(innerenv_re, result):
                    print("Matched..: " + result)
                    pre = result.split("$")[0]
                    env = result.split("$")[1].split("}")[0].split("{")[1]
                    post = ""
                    if len(result.split("}"))>1:
                        post = result.split("}")[1]
                    if env in env_dict.keys():
                        result = pre +env_dict[env].strip('"\' ') + post
                    else:
                        inner_finish_flag = False
                        break
                if not inner_finish_flag:
                    continue
                
                if result in dismiss_lst:
                    continue
                if result in onearg_dismiss_lst:
                    onearg_dismiss_flag= True
                    continue
                if onearg_dismiss_flag:
                    onearg_dismiss_flag = False
                    continue
                if result in requirements_lst:
                    requirements_flag = True
                    continue
                if requirements_flag:
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
                
                print("pip_" + result + " ", file=self.fff, end='')                

def is_url(line):
    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, line)
        

def parseDockerfile(content):
    dfp = DockerfileParser()
    dfp.content = content
    bash_dict = []
    for dic in json.loads(dfp.json):
        if dic.get("ENV")!=None or dic.get("RUN")!=None:
            bash_dict.append(dic)     
    return bash_dict

# Unsolved Case: Dockerfile-459
# maybe download requirments.txt alongwith Dockerfile
# pip -e: pip_github ?
def parsefile(filepath, fff):
    
    env_dict.clear()
    
    parsed_df = parseDockerfile(open(filepath, encoding="UTF-8").read())
    for dic in parsed_df:
        if dic.get("ENV") != None:
            s = dic["ENV"]
            if len(s.split("="))>1:
                sp_eq = s.split("=")
                s = ""
                for i in range(len(sp_eq)):
                    if i == len(sp_eq)-1:
                        s += sp_eq[i]
                    else:
                        s += sp_eq[i] + " = "
                lexes = s.split()
                ii = 0
                while ii<len(lexes):
                    # print(lexes[ii])
                    if lexes[ii] == "=":
                        r = ""
                        jj = ii+1
                        while jj<len(lexes) and lexes[jj]!="=":
                            if jj+1<len(lexes) and lexes[jj+1]=="=":
                                break
                            r += (" "+lexes[jj])
                            jj += 1
                        print("Inserting to Env dict: " + lexes[ii-1] + " " + r.strip('"\''))
                        env_dict[lexes[ii-1]] = r.strip('"').strip("'")
                    ii += 1  
            else:
                if len(s.split()) > 1:
                    if len(s.split()) == 2:
                        if len(s.split()[0].split("="))>1 and len(s.split()[1].split("="))>1:
                            for ss in s.split():
                                print("Inserting to Env dict: " + ss.split("=")[0] + " " + ss.split("=")[1])
                                env_dict[ss.split("=")[0].strip()] = ss.split("=")[1].strip()
                        else:
                            print("Inserting to Env dict: " + dic["ENV"].split()[0] + " " + dic["ENV"].split()[1])
                            env_dict[dic["ENV"].split()[0]] = dic["ENV"].split()[1]
                    else:
                        ss = ""
                        for i in range(1, len(s.split())):
                            ss += s.split()[i] + " "
                        print("Inserting to Env dict: " + s.split()[0] + " " + ss.strip())
                        env_dict[s.split()[0]] = ss.strip()
                else:
                    if len(dic["ENV"].split("="))>1:
                        print("Inserting to Env dict: " + dic["ENV"].split("=")[0] + " " + dic["ENV"].split("=")[1])
                        env_dict[dic["ENV"].split("=")[0].strip()] = dic["ENV"].split("=")[1].strip()
        if dic.get("RUN") != None:
            try:
                parts = bashlex.parse(dic["RUN"])
                positions=[]
                for ast in parts:
                    visitor = nodevisitor(positions, fff)
                    visitor.visit(ast)
            except BaseException as e:
                print(e)

def removeEmptyLines(filename, outfile):
    f = open(filename, "r")
    wf = open(outfile, "w")
    lines = f.read().splitlines()
    for line in lines:
        if len(line.split())>=2:
            wf.write(line.strip() + "\n")
    f.close()
    wf.close()
def convertToCsv(filename, outcsv):
    f = open(filename, "r")
    cf = open(outcsv, "w")
    f_csv = csv.writer(cf)
    lines = f.read().splitlines()
    for line in lines:
        lexes = line.split()
        f_csv.writerow(lexes)
    f.close()
    cf.close()
    

def parse(path, r):
    try:
        fff = open("out.log", "w")
        for i in range(r):
            filepath = path + str(i) + "/Dockerfile"
            
            if not os.path.exists(filepath):
                continue
            
            print(str(1000000 + i))
            print(str(1000000 + i) + " ", file=fff, end='')
            parsefile(filepath, fff)
            print("", file=fff)
        fff.close()
        removeEmptyLines("out.log", "out.log2")
        os.remove("out.log")
    except Exception:
        pass
    
    # (out.log2)parse req and download requirements.txt, then reparse req.

# os.remove("out.log2")

def parseSingleFile(filepath, id, outfile):
    fff = open(outfile, "a")
    print(str(id))
    print(str(id) + " ", file=fff, end='')
    parsefile(filepath, fff)
    print("", file=fff)
    fff.close()