#!/usr/bin/python3
from os.path import expanduser
import json
import xml.etree.ElementTree as ET
import httplib2
http = httplib2.Http()

orcanos_api_url = 'https://app.orcanos.com/xxxxxx/api/v2/Json/'

token_id = 'Basic Z2l0bGFiLnVzZXI6UlU0MGU2Y3A='

Solution_ID = {
    'Project_Name' : 'IDXX',
    }

Filter = {}
Filter['All'] = 'xxx'
Filter['TC']    = 'xxx'
Filter['RISKS'] = 'xxx'
Filter['Defects'] = 'xxx'
Filter['SOUP_Results']   = 'xxx'
Filter['Results']   = 'xxx'


def remove_brackets(string):
    pos1 = -1
    pos2 = -1
    for num, char in enumerate(string):
        if char == "(":
            pos1 = num
        if char == ")":
            pos2 = num 
    dlte_str = ""
    while pos1 <= pos2:
        dlte_str = dlte_str + string[pos1]
        pos1 = pos1 + 1
    if pos1 != -1 and pos2 != -1:
        string = string.replace(dlte_str, "")
    output = string.split(' ')
    return output[0]


def loginInOrcanos():
    url = orcanos_api_url + 'QW_Login'
    print(url)
    headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'Authorization': token_id}
    resp, content = http.request(url, 'POST', body="", headers=headers)
    print(content)
    return json.loads(content)


def getRowsFromJson(jsonInput):
    rows = []
    
    if "No results" not in jsonInput['Data']: 
        json_data = jsonInput['Data']['Object']
        total = int(jsonInput['Data']['Total_records'])
        for i in range(0, total):
            row = {}
            for field in range (0, 1000):
                try:
                    field_name = json_data[i]['Field'][field]['Title']
                    field_value = json_data[i]['Field'][field]['Text']
                    row[field_name] = field_value
                except IndexError as error:
                    break
            rows.append(row)
    
    return rows


def getDescFromJson(jsonInput):
    json_data = jsonInput['Data']['Field']
    for field in json_data:
        if field['Name'] == 'Description':
            return field['Text']
    return None


def getTitleFromJson(jsonInput):
    json_data = jsonInput['Data']['Field']
    for field in json_data:
        if field['Name'] == 'Name':
            return field['Text']
    return None

def updateWorkItemDescription(par_id, html_content):
        
    name, data = getWorkItem(par_id)
    print(str(name) + ' ' + str(data))
    
    payload = str(html_content)
    payload_json = json.dumps({"Object_ID": par_id, "Description": payload})
    
    url = orcanos_api_url + 'QW_Update_Object'    
    print(url)
    headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'Authorization': token_id}
    resp, content = http.request(url, 'POST', body=payload_json, headers=headers)
    
    content = json.loads(content)
    print(resp)
    print(content)
    assert(True == content['IsSuccess'])


def getWorkItem(item):
    url = orcanos_api_url + 'QW_Get_Object?id=' + item
    print(url)
    headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'Authorization': token_id}
    resp, content = http.request(url, 'GET', body="", headers=headers)
    
    print(content)
    data = getDescFromJson(json.loads(content))
    name = getTitleFromJson(json.loads(content))
    
    return name, data


def getWorkItems(item_type, filter_id, project_id):
            
    data = {
        "Filter_id": filter_id,
        "Page_no": "1",
        "Page_size": "999",
        "Item_type": item_type,
        "Version_id": project_id,
        "Filter_By": "",
        "Order_By": "",
        "IsNewPaging": "1",
        "IsReturnPageCount":"0"
    }
    data_json = json.dumps(data)
    
    url = orcanos_api_url + 'QW_Get_Filter_Results'
    print(url + ' ' + project_id + ' ' + item_type + ' ' + filter_id)
    headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'Authorization': token_id}
    resp, content = http.request(url, 'POST', body=data_json, headers=headers)
    
    rows = getRowsFromJson(json.loads(content))
    
    for r in rows:
        r['Key'] = remove_brackets(r['Key'])
    
    return rows


def getExecutionSet(exec_id):
    
    data = {
        "VersionId": Atalante_ID['2.1'],
        "ItemType": 'T_EXEC',
        "ItemId": exec_id,
        "PageNo": "1",
        "PageSize": "999",
    }
    
    url = orcanos_api_url + 'QW_Get_Execution_Set?'
    print(url)
    
    for k in data.keys():
        url += k + "=" + data[k] + '&'
    url = url[:-1]
    print(url)
    
    headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'Authorization': token_id}
    resp, content = http.request(url, 'GET', body="", headers=headers)
    
    content_json = json.loads(content)
    
    for element in content_json['Data']['filterlist']:
        print(element)
        print()
    
    return content_json['Data']


def getExecutionSetDetails(exec_id, test_id):
    payload = json.dumps({
        "Execution_Set_ID": exec_id,
        "Run_Status_Filter": "",
        "Assigned_Filter": "",
        "Work_Status_Filter": "",
        "Test_ID": test_id,
        "TestInExecLineID": "",
        "Type": "",
        "convertHTMLtoText": True
    })

    url = orcanos_api_url + 'Get_Execution_Run_Details_xml'
    print(url)
    headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'Authorization': token_id}
    resp, content = http.request(url, 'POST', body=payload, headers=headers)
    
    return content


def recordExecutionSet(xml, actuals, status):
        
    tree = ET.ElementTree(ET.fromstring(xml))
    root = tree.getroot()
    
    test_steps = []
    
    for element in root.findall(".//Step"):
        order = element.get('Order')
        a = element.find('Actual')
        a.text = actuals[int(order)-1]
        a = element.find('Run')
        a.set('Status', status[int(order)-1])    
    
    payload = str(ET.tostring(root).decode('utf-8'))
    payload_json = json.dumps({"sXML": payload})
    
    url = orcanos_api_url + 'Record_Execution_Results_New'    
    print(url)
    headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'Authorization': token_id}
    resp, content = http.request(url, 'POST', body=payload_json, headers=headers)
    
    content = json.loads(content)
    assert(True == content['IsSuccess'])
     
            
def main():
    res = loginInOrcanos()
    if str(res['IsSuccess']):
        print('SUCCESS')
    else:
        print('FAILURE')
    
    Paragraphs = {}
    Paragraphs['All'] = {}
    Paragraphs['All']['References']   = '56285'
    Paragraphs['All']['Purpose']   = '56286'
    
    
    name, data = getWorkItem(Paragraphs['All']['References'])
    print('Name : ' + name)
    print(data)
    print()
    
    rows = getWorkItems('DEFECT', Filter['All']['Defects'], Solution_ID['Eve'])
    print(rows)
            

if __name__ == '__main__':
    main()
