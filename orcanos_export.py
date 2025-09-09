#!/usr/bin/python3
import orcanos_api as api

import os
from lxml import etree
import argparse
import re

green_light = '#ccffcc'
yellow_light = '#FFD966'
red_light = '#ffcccc'
grey_light = '#d3d3d3'
white = '#FFFFFF'

req_id_regexp = r"\s*((?:SDD|SRS)[- _,.]*0*\d{1,6})"


def clean_from_html(input):
    if input is None:
        return ""
    p = re.compile(r'<.*?>')
    output = p.sub('', input)
    output = output.replace('&nbsp;', '')
    output = output.replace('&deg;', '°')
    output = output.replace('&lt;', '<')
    output = output.replace('&gt;', '>')
    output = output.replace('&ldquo;', '\"')
    output = output.replace('&rdquo;', '\"')
    output = output.replace('&#39;', '\'')
    output = output.replace('&quot;', '\'')
    output = output.replace('&micro;', 'u')
    return output


def colorize(value):
    if ("5-Catastrophic" in value 
        or "5-Frequent" in value 
        or "Unacceptable(" in value
        or "(FAIL)" in value
        or "Error" == value
        or "Fail" == value
        or '' == value):
        return red_light
    elif ("4-Significant" in value or "3-Moderate" in value 
        or "4-Possible" in value or "3-Unlikely" in value
        or "Review(" in value
        or "Review" == value
        or "(SKIPPED)" in value
        or "Skipped" == value):
        return yellow_light
    elif ("2-Minor" in value or "1-Negligible" in value 
        or "2-Rare" in value or "1-Improbable" in value
        or "Acceptable(" in value
        or "Approved" == value
        or "Published" == value
        or "(PASS)" in value
        or "Pass" == value):
        return green_light
    elif ("New" == value
          or "Reopen" == value
          or "Not in execution" == value
          or "Not Completed" == value):
        return grey_light
    else:
        return white


def tracea(rows1, rows2, category=[]):
    output = []
    for r1 in rows1:
        if 'Product Requirement Category' not in r1:
            r1['Product Requirement Category'] = ""
        elif r1['Product Requirement Category'] is None:
            r1['Product Requirement Category'] = ""
        r1['tracea'] = []
        if r1['Traced Items Info'] is not None:
            for r2 in rows2:
                if r2['Key'] in r1['Traced Items Info']:
                    r1['tracea'].append(r2)
                        
        if len(category) > 0:
            filter_in = False 
            for c in category:
                if c in r1['Product Requirement Category']:
                    filter_in = True
            if filter_in is True:
                output.append(r1)
        else:
            output.append(r1)
    return output


def print_tracea(input):
    for i in input:
        print('****************************************')
        category = ""
        if i['Product Requirement Category'] is not None:
            category = ", " + i['Product Requirement Category']
        print(i['Key'] + ' ' + i['Name'] + category)
        for j in i['tracea']:
            print('\t' + j['Key'] + ' ' + j['Name'])



def remap_srs_to_tc_sw(rows_srs, rows_tc):
    for srs in rows_srs:
        srs['Traced Items Info'] = ""
        for tc in rows_tc:
            for srs_ in tc['SRS']:
                if srs_['Key'] == srs['Key']:
                    srs['Traced Items Info'] += tc['Key'] + ', '  
    return rows_srs



def analyse_xml_obj(raw_string):
    current_cursor = 0
    current_req_set = list()
    returned_analysed_obj = list()

    for req in re.finditer(req_id_regexp, raw_string, re.IGNORECASE):
        if req.start() == current_cursor:
            normalized_id = req.group(0).strip()
            if len(current_req_set) > 0:
                returned_analysed_obj.append((current_req_set, ""))
            current_req_set = normalized_id
        else:
            returned_analysed_obj.append((current_req_set, raw_string[current_cursor:req.start()].strip()))
            normalized_id = req.group(0).strip()
            current_req_set = normalized_id
        current_cursor = req.end()
    if current_cursor > 0:
        returned_analysed_obj.append((current_req_set, raw_string[current_cursor:].strip()))

    return returned_analysed_obj


def import_test_xml_file(fi):
    testcase_with_no_id = 0
    testcase_number = 0
    success_number = 0
    failure_number = 0
    error_number = 0
    skipped_number = 0
    rows_tc = []
    
    file_name = os.path.basename(fi)
    testsuites = etree.parse(fi).getroot()
    
    for testsuite in testsuites.iter('testsuite'):
        # Go through all the testcases
        for testcase in testsuite.iter('testcase'):
            test_name_xunit = testcase.attrib.get('name', None)
            test_id = ""
            test_name = ""
            test_desc = ""
            test_objective_raw = ""
            test_objective_analysed = ""
            for tc in testcase.iter('property'):
                if tc.get('name', None) != None:
                    if tc.get('name') == "name":
                        test_name_xunit = tc.get('value', None)
                    if tc.get('name') == "description":
                        test_desc = tc.get('value', None)
                    if tc.get('name') == "objective":
                        test_objective_raw = tc.get('value', None)
                        test_objective_analysed = analyse_xml_obj(test_objective_raw)
                    if tc.get('name') == "test_id":
                        test_id = tc.get('value', None)
            if test_id == "" and testcase.attrib.get('name', None) != None:
                test_name_xunit = testcase.attrib.get('name', "")
                test_id = testcase.attrib.get('test_id', "")
                test_desc = testcase.attrib.get('description', "")
                test_objective_raw = testcase.attrib.get('objective', "")
                test_objective_analysed = analyse_xml_obj(test_objective_raw)
            
            testcase_number += 1
            
            if test_id is None or test_id == "" or "TC-" not in test_id:
                testcase_with_no_id += 1
                continue  # If no test_id, skip the testcase.

            srs_list = []
            for o in test_objective_analysed:
                srs = {}
                srs['Key'] = o[0]
                srs['Objective'] = o[1]
                if "SRS-" in srs['Key']:
                    srs_list.append(srs)
                
            if testcase.find('failure') is not None:
                failure_number += 1
                test_result = "Fail"
            elif testcase.find('error') is not None:
                error_number += 1
                test_result = "Error"
            elif testcase.find('skipped') is not None:
                skipped_number += 1
                test_result = "Skipped"
            else:
                success_number += 1
                test_result = "Pass"
            
            tc = {}
            tc['Key'] = test_id
            tc['Name'] = test_name_xunit
            tc['Description'] = test_desc
            tc['Last Test Run Result'] = test_result
            tc['SRS'] = srs_list
            rows_tc.append(tc)
                
    print(("\nFrom {}: extracted {} tests, \n\t- {} ignored because no test id, \n\t- {} tests passed, \n\t- {} tests failed, \n\t- {} tests skipped and \n\t- {} error(s)".format(
            file_name, testcase_number, testcase_with_no_id,
            success_number, failure_number, skipped_number, error_number)))
    return rows_tc
    

def create_table_around(title):
    output = '<table border=1 width=100%>\n'
    output += '  <tr><td>' + title + '\n' + '</td></tr>'
    output += '</table>\n'
    output += '<br>\n'
    return output


def table_as_html(table_in, table_title):
    root = etree.Element('html')
    table = etree.SubElement(root, 'table')
    table.set('border', "1")
    table.set('cellpadding', "2")
    thead = etree.SubElement(table, 'thead')
    tr = etree.SubElement(thead, 'tr')
    if table_title != "":
        th = etree.SubElement(tr, 'th')
        th.set('colspan', str(len(table_in[0])))
        th.set('bgcolor', grey_light)
        th.text = table_title
    tr1 = etree.SubElement(thead, 'tr')
    for title in table_in[0]:
        etree.SubElement(tr1, 'th').text = title
    for th in tr1:
        th.set("bgcolor", grey_light)
    tbody = etree.SubElement(table, 'tbody')
    
    for line in table_in[1:]:
        tr = etree.SubElement(tbody, 'tr')
        for item in line:
            value = clean_from_html(item)
            etree.SubElement(tr, 'td').text = value
        for td in tr:
            text = (etree.tostring(td)).decode('utf-8')
            text = clean_from_html(text)
            td.set('bgcolor', colorize(text))
    output = etree.tostring(root).decode("utf-8")

    return output


def flatify_rows_in_table(rows, fields1, fields2):
    
    table_output = []
    table_output.append(fields1 + fields2)
    
    for r1 in rows:
        row1 = []        
        for f1 in fields1:
            row1.append(r1[f1])
        
        if len( r1['tracea'] ) > 0 :
            for r2 in  r1['tracea']:
                row2 = []
                for f2 in fields2:
                    row2.append(r2[f2])
                table_output.append(row1 + row2)
        else:
            row2 = []
            for f2 in fields2:
                row2.append("")
            table_output.append(row1 + row2)    
    
    return table_output
            

def merge_table(table1, table2):
    table_output = []
    # retrieve the index of the last occurence of 'Key' in the first line of column titles
    index_table2 = len(table2[0]) - 1 - table2[0][::-1].index('Key') if 'Key' in table2[0] else None
    table_output.append(table1[0] + table2[0][index_table2:]) 
    for l1 in table1[1:]:
        empty = True
        for l2 in table2[1:]:
            if l2[0] in l1:
                table_output.append(l1 + l2[index_table2:])
                empty = False
        if empty:
            table_output.append(l1 + (len(l2) - index_table2)*[''])
    return table_output
        

def export_traceability_html(rows, fields, title):
    table_trac = []
    
    
    if len(matrix_rows) == 1:
        table_trac.append(export_item_to_item(matrix_rows[0], [], fields[0], []))
    else:
        for i in range(len(matrix_rows) -1 ):
            if i < (len(matrix_rows) -2) :
                table_trac.append(export_item_to_item(matrix_rows[i], matrix_rows[i+1], fields[i], fields[i+1]))
            else:
                table_trac.append(export_item_to_items(matrix_rows[i], matrix_rows[i+1], fields[i]))

    output = merge_tables(table_trac)[0]
    
    key_num = 0
    for i, o in enumerate(output[0]):
        if o == 'Key':
            output[0][i] = o + ' #' +  str(key_num)
            key_num += 1 

    return table_as_html(output, title) 
        

def generate_html_table(data_list, main_columns=None, tracea_columns=None):
    if main_columns is None:
        raise ValueError("main_columns cannot be None")
    if tracea_columns is None:
        raise ValueError("tracea_columns cannot be None")
    
    total_columns = main_columns + tracea_columns
    
    def get_cell_style(value):
        v = str(value).strip() 
        color = colorize(v)
        if color != white:
            return 'background-color: ' + color + ';'
        else:
            return ""
    
    html = """
<html>
<head>
  <meta charset="UTF-8">
  <title>Orcanos HTML table</title>
  <style>
    table { border-collapse: collapse; }
    th, td { border: 1px solid black; padding: 5px; }
    th { cursor: pointer; }
    input[type="text"] { width: 95%; box-sizing: border-box; }
  </style>
  <script>
    function sortTable(colIndex) {
      var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
      table = document.getElementById("myTable");
      switching = true;
      dir = "asc";
      while (switching) {
        switching = false;
        rows = table.rows;
        // 2 first lines are headers lignes. Data start at index 2.
        for (i = 2; i < (rows.length - 1); i++) {
          shouldSwitch = false;
          x = rows[i].getElementsByTagName("TD")[colIndex];
          y = rows[i + 1].getElementsByTagName("TD")[colIndex];
          if (dir === "asc") {
            if (x.textContent.toLowerCase() > y.textContent.toLowerCase()) {
              shouldSwitch = true;
              break;
            }
          } else if (dir === "desc") {
            if (x.textContent.toLowerCase() < y.textContent.toLowerCase()) {
              shouldSwitch = true;
              break;
            }
          }
        }
        if (shouldSwitch) {
          rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
          switching = true;
          switchcount++;
        } else {
          if (switchcount === 0 && dir === "asc") {
            dir = "desc";
            switching = true;
          }
        }
      }
    }
    
    function filterTable() {
      var table, tr, i, j, td, filter, txtValue, showRow;
      table = document.getElementById("myTable");
      tr = table.getElementsByTagName("tr");
      var filterInputs = table.rows[1].getElementsByTagName("input");
      for (i = 2; i < tr.length; i++) {
        showRow = true;
        for (j = 0; j < filterInputs.length; j++) {
          td = tr[i].getElementsByTagName("td")[j];
          if (td) {
            filter = filterInputs[j].value.toLowerCase();
            txtValue = td.textContent || td.innerText;
            if (txtValue.toLowerCase().indexOf(filter) === -1) {
              showRow = false;
              break;
            }
          }
        }
        tr[i].style.display = showRow ? "" : "none";
      }
    }
  </script>
</head>
<body>
  <table id="myTable">
    <tr>
"""
 
    for idx, header in enumerate(total_columns):
        html += f'      <th onclick="sortTable({idx})">{header}</th>\n'
    html += "    </tr>\n"
    
    html += "    <tr>\n"
    for _ in total_columns:
        html += '      <td><input type="text" onkeyup="filterTable()"></td>\n'
    html += "    </tr>\n"
    
    for record in data_list:
        html += "    <tr>\n"
        # Main columns, 1 data per cell 
        for col in main_columns:
            value = record.get(col, "")
            style = get_cell_style(value)
            html += f'      <td style="{style}">{value}</td>\n'
        # Tracea columns, multiple data per cell 
        tracea_list = record.get("tracea", [])
        for col in tracea_columns:
            if tracea_list:
                values = [str(trace.get(col, '')).strip() for trace in tracea_list]
                if len(values) > 1:
                    # Multiple data
                    cell_content = ""
                    for val in values:
                        line_style = get_cell_style(val)
                        cell_content += f'<div style="margin:0; padding:0; {line_style}">{val}</div>'
                    html += f'      <td>{cell_content}</td>\n'
                else:
                    # 1 unique data
                    cell_content = values[0] if values else ""
                    style = get_cell_style(cell_content)
                    html += f'      <td style="{style}">{cell_content}</td>\n'
            else:
                # No data
                html += '      <td style="background-color: #ffcccc;"></td>\n'
        html += "    </tr>\n"
    
    html += """  </table>
</body>
</html>"""
    return html

   
def main_():
    rows_br = api.getWorkItems('MR_REQ', api.Filter['All'], api.Solution_ID['Eve'])
    rows_pr = api.getWorkItems('REQ', api.Filter['All'], api.Solution_ID['Eve'])
    rows_srs = api.getWorkItems('SRS', api.Filter['All'], api.Solution_ID['Eve'])
    
    rows_pr_srs = tracea( rows_pr, rows_srs )
    rows_br_pr = tracea( rows_br, rows_pr )
    
    table_pr_srs = flatify_rows_in_table(rows_pr_srs, ['Key', 'Name'], ['Key', 'Name'])
    table_br_pr = flatify_rows_in_table(rows_br_pr, ['Key', 'Name'], ['Key', 'Name'])
    
    output = merge_table(table_br_pr, table_pr_srs)
    for o in output:
        print(o)
    
    html = table_as_html(output, "xxxxxxxxxx----------xxxxxxxxxxx")
    with open('output.html', "w+") as text_file:
        text_file.write(html)
        print('HTML file written: ' + 'output.html')
        

def main():   

    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--tracea", required=False, type=str, default=None, help="\'PR-TC\', \'PR-SRS\' or \'PR-SRS.MECRS.ELCRS\'")
    parser.add_argument("-f", "--output_filename", required=False, type=str, default="output.html", help="HTML format, default is \'output.html\'")
    parser.add_argument("-p", "--project", required=False, type=str, default='Eve', help="Project can be \'Eve\' or \'Atalante\'")
    parser.add_argument("-x", "--xml", required=False, type=str, nargs='+',default=None, help="list of xml test files from CI. Ex: file1.xml file2.xml ")
    args = parser.parse_args()
    
    html = ""
    
    if args.xml is None:
        rows_pr = api.getWorkItems('REQ', api.Filter['All'], api.Solution_ID[args.project])
        rows_srs = api.getWorkItems('SRS', api.Filter['All'], api.Solution_ID[args.project])
        rows_mech = api.getWorkItems('MEC', api.Filter['All'], api.Solution_ID[args.project])
        rows_elec = api.getWorkItems('HW', api.Filter['All'], api.Solution_ID[args.project])
        rows_tc = api.getWorkItems('T_CASE', api.Filter['TC'], api.Solution_ID[args.project])
        
        content = []
        if args.tracea == 'PR-SRS.MECRS.ELCRS':
            t = tracea( rows_pr, rows_srs + rows_mech + rows_elec, ['Software', 'Mechanics', 'Electronics'])
            html = generate_html_table(t, ['Key', 'Name', 'Product Requirement Category', 'Status'], ['Key', 'Name', 'Status'])
        elif args.tracea == 'PR-SRS':
            t = tracea( rows_pr, rows_srs, ['Software'])
            html = generate_html_table(t, ['Key', 'Name', 'Product Requirement Category', 'Status'], ['Key', 'Name', 'Status'])
        elif args.tracea == 'PR-TC':
            t = tracea( rows_pr, rows_tc )
            html = generate_html_table(t, ['Key', 'Name', 'Product Requirement Category', 'Status'], ['Key', 'Name', 'Status', 'Last Test Run Result'])
            
        print_tracea(t)
    else:
        rows_tc_from_xml = []
        for xml_file in args.xml:
            if (os.path.isfile(os.path.abspath(xml_file))):
                print(("\n>>> Loading " + xml_file + " ..."))
                rows_tc_from_xml += import_test_xml_file(xml_file)
            else:
                print(("\n>>> ERROR: Cannot find " + xml_file + " ..."))
                return
        
        rows_srs = api.getWorkItems('SRS', api.Filter['All'], api.Solution_ID[args.project])
        rows_srs = remap_srs_to_tc_sw(rows_srs, rows_tc_from_xml)
        t_srs_tc_xml = tracea( rows_srs, rows_tc_from_xml )
        html = generate_html_table(t_srs_tc_xml, ['Key', 'Name', 'Status'], ['Key', 'Name', 'Last Test Run Result'])
    
    with open(args.output_filename, "w+") as text_file:
        text_file.write(html)
        print('HTML file written: ' + args.output_filename)
    

if __name__ == '__main__':
    main()

