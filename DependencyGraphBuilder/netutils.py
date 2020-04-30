import csv
import requests
import os 
import sys
import time
import pydbc

# download files recognized in csvfile to all-known path
def downloadDockerfileCsv(csvfile):
    requests.adapters.DEFAULT_RETRIES=5
    db = pydbc.DBUtils("url.db")
    
    i = 0
    url = "https://raw.githubusercontent.com/"
    with open(csvfile) as f:
        f_csv = csv.reader(f)
        for row in f_csv:
            new_url = url + row[0] + "/" + row[1].split("/")[len(row[1].split("/"))-1] + "/" + row[2]
            print("Downloading: " + new_url)
            
            if not os.path.exists("sample_dockerfile/files/" + str(i)):
                os.makedirs("sample_dockerfile/files/" + str(i))
            #urllib.request.urlretrieve(new_url, "files/" + str(i) + "/Dockerfile")
            #try:
            #    urllib.request.urlretrieve(new_url, "files/" + str(i) + "/Dockerfile")
            #except Exception as e:
            #    print(e)
            db.insertToUrlTable(i, new_url.rsplit("/", 1)[1], new_url.rsplit("/", 1)[0], "Dockerfile")
            try:
                r = requests.get(new_url, verify=False)
                
                with open("sample_dockerfile/files/" + str(i) + "/Dockerfile", "wb") as df:
                    df.write(r.content)
            except Exception as e:
                print(e)
            i += 1
            
# downloadDockerfileCsv("sample_dockerfile/github_dockerfile_info.csv")

# download files recognized in csvfile to all-known path
def downloadRequirementsCsv(csvfile):
    requests.adapters.DEFAULT_RETRIES=5
    db = pydbc.DBUtils("url.db")
    
    i = 0
    url = "https://raw.githubusercontent.com/"
    with open(csvfile) as f:
        f_csv = csv.reader(f)
        for row in f_csv:
            new_url = url + row[0] + "/" + row[1].split("/")[len(row[1].split("/"))-1] + "/" + row[2]
            print("Downloading: " + new_url)
            
            if not os.path.exists("sample_requirements/files/" + str(i)):
                os.makedirs("sample_requirements/files/" + str(i))
            #urllib.request.urlretrieve(new_url, "files/" + str(i) + "/Dockerfile")
            #try:
            #    urllib.request.urlretrieve(new_url, "files/" + str(i) + "/Dockerfile")
            #except Exception as e:
            #    print(e)
            db.insertToUrlTable(i, new_url.rsplit("/", 1)[1], new_url.rsplit("/", 1)[0], "Requirements")
            try:
                r = requests.get(new_url, verify=False)
                
                with open("sample_requirements/files/" + str(i) + "/requirements.txt", "wb") as df:
                    df.write(r.content)
            except Exception as e:
                print(e)
            i += 1

# downloadRequirementsCsv("sample_requirements/req_data.csv")

# download a single file
def downloadSingleFile(remoteurl, localpath, filename):
    requests.adapters.DEFAULT_RETRIES=5
    
    if not os.path.isdir(localpath):
        print("File downloads failed, as path " + localpath + " dose not exists.")
        assert(os.path.isdir(localpath))
    
    try:
        r = requests.get(remoteurl, verify=False)
        with open(localpath + filename, "wb") as df:
            df.write(r.content)
    except Exception as e:
        print(e)

# return string, lines of downloaded file
def downloadSingleFileToMemory(remoteurl):
    print("Downloading: " + remoteurl)
    requests.adapters.DEFAULT_RETRIES=5
    exc_flag = False
    
    r = None
    try:
        r = requests.get(remoteurl, verify=False)
    except Exception as e:
        exc_flag = True
        print(e)
    
    return exc_flag, r.content
