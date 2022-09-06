from genericpath import exists
from operator import contains
from traceback import print_tb
import requests 
import os
from datetime import date
from datetime import timedelta
import zipfile
import xml.etree.ElementTree as ET
import shutil

def download_file_from_url(url, save_path, chunk_size=128):
    r = requests.get(url, stream=True)
    with open(save_path, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            fd.write(chunk)

def extract_zip(zip_path, extract_path):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)

def clean_cwd():
    for file in [file for file in os.listdir(os.getcwd()) if file.endswith(".xml") or file.endswith(".zip")]:
        os.remove(file)

def parse_xml_and_spit_result(xml_path, dest_path):
    head, tail = os.path.split(dest_path)
    os.makedirs(head, exist_ok=True)
    root = ET.parse(xml_path).getroot()
    f = open(dest_path, "w")
    for item in root[0][0].findall('{urn:bvmf.052.01.xsd}BizGrp'):
        symbol = item[1][0].find('{urn:bvmf.217.01.xsd}SctyId').find('{urn:bvmf.217.01.xsd}TckrSymb')
        vol = item[1][0].find('{urn:bvmf.217.01.xsd}FinInstrmAttrbts').find('{urn:bvmf.217.01.xsd}NtlFinVol')
        if symbol is None or vol is None:
            continue
        f.write(f'{symbol.text} {vol.text}\n')
    f.close()
    shutil.copy2(xml_path, head)
    os.remove(xml_path)

def donwload_and_process_date(date_str, missing_days):
    print(f'Will try to process {date_str}...', end ="")
    clean_cwd()
    zip_filename = "PR" + date_str + ".zip"
    extract_path = os.path.join(os.getcwd(), zip_filename)
    save_path = os.path.join(os.getcwd(), "result.zip")
    result_filename = os.path.join(os.getcwd(), "output" , date_str, "PR" + date_str + ".txt")

    if exists(result_filename):
        print(f'exists')
        clean_cwd()
        return True
    
    print('downloading...', end ="")
    download_file_from_url("https://www.b3.com.br/pesquisapregao/download?filelist=" + zip_filename, save_path)         ## Download master zip from B3 
    extract_zip(save_path, os.getcwd())                                                                                 ## Extract master zip in place and remove it ('result.zip')
    
    if zip_filename not in os.listdir(os.getcwd()):
        print(f'{zip_filename} not found, skipping this date')
        clean_cwd()
        return False

    extract_zip(extract_path, os.getcwd())                                                                              ## Extract PR report zip in place and remove it ('PR{YYMMDD}.zip')
    latest_file = sorted([file for file in os.listdir(os.getcwd()) if file.endswith(".xml")])[-1]                       ## PR zip has every PR report version, get only latest
    parse_xml_and_spit_result(latest_file, result_filename)                                                             ## Parse xml, spit to ./output/YYMMDD/PRYYMMDD.txt and copy base xml
    clean_cwd()
    missing_days.append(date_str)
    print(f'success ({result_filename})')
    return True


date_window = 30
days_behind = 0
consecutive_fail_count = 0
missing_days = []
while date_window > 0:
    date_str = (date.today() - timedelta(days=days_behind)).strftime("%y%m%d")
    if donwload_and_process_date(date_str, missing_days):
        date_window = date_window - 1
        consecutive_fail_count = 0
    else:
        consecutive_fail_count = consecutive_fail_count + 1
        if consecutive_fail_count > 10:
            print('Failed 10 times in a row, aborting')
            break
    days_behind = days_behind + 1
print(f'DONE : processed {len(missing_days)} missing date(s) ', end="")
if len(missing_days) > 0:
    print("->", end=" ")
    print(*missing_days)