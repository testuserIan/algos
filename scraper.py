from traceback import print_tb
import requests 
import os
from datetime import date
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
    os.makedirs(dest_path, exist_ok=True)
    root = ET.parse(xml_path).getroot()
    f = open(os.path.join(dest_path, "PR" + date.today().strftime("%y%m%d") + ".txt"), "w")
    for item in root[0][0].findall('{urn:bvmf.052.01.xsd}BizGrp'):
        symbol = item[1][0].find('{urn:bvmf.217.01.xsd}SctyId')
        vol = item[1][0].find('{urn:bvmf.217.01.xsd}FinInstrmAttrbts').find('{urn:bvmf.217.01.xsd}NtlFinVol')
        if symbol is None or vol is None:
            continue
        f.write(f'{symbol[0].text} {vol.text}\n')
    f.close()
    shutil.copy2(xml_path, dest_path)
    os.remove(xml_path)

clean_cwd()
file_name = "PR" + date.today().strftime("%y%m%d") + ".zip"
save_path = os.path.join(os.getcwd(), "result.zip")
download_file_from_url("https://www.b3.com.br/pesquisapregao/download?filelist=" + file_name, save_path)        ## Download master zip from B3 
extract_zip(save_path, os.getcwd())                                                                             ## Extract master zip in place and remove it ('result.zip')
extract_zip(os.path.join(os.getcwd(), file_name), os.getcwd())                                                  ## Extract PR report zip in place and remove it ('PR{YYMMDD}.zip')
latest_file = sorted([file for file in os.listdir(os.getcwd()) if file.endswith(".xml")])[-1]                   ## PR zip has every PR report version, get only latest
parse_xml_and_spit_result(latest_file, os.path.join(os.getcwd(), "output" , date.today().strftime("%y%m%d")))   ## Parse xml, spit to ./output/YYMMDD/PRYYMMDD.txt and copy base xml
clean_cwd()