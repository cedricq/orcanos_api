#!/usr/bin/python3
from lxml import etree

import orcanos_export as export

import os
import argparse


def main():   

    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output_type", required=True, type=str, default='Report', help="Can be \'Plan\ or \'Report\' with results")
    parser.add_argument("-f", "--output_filename", required=False, type=str, default="output.html", help="HTML format, default is \'output.html\'")
    parser.add_argument("-x", "--xml", required=True, type=str, nargs='+',default=None, help="list of xml test files from CI. Ex: file1.xml file2.xml ")
    args = parser.parse_args()
    
    rows_tc_from_xml = []
    for xml_file in args.xml:
        if (os.path.isfile(os.path.abspath(xml_file))):
            print(("\n>>> Loading " + xml_file + " ..."))
            rows_tc_from_xml += export.import_test_xml_file(xml_file)
        else:
            print(("\n>>> ERROR: Cannot find " + xml_file + " ..."))
            return
    
    for r in rows_tc_from_xml:
        r['Objective'] = ""
        for obj in r['SRS']:
            r['Objective'] += obj['Objective'] + '; '  
    
    if args.output_type == 'Plan':
        html = export.generate_html_table(rows_tc_from_xml, ['Key', 'Name', 'Description', 'Objective'], [])
    elif args.output_type == 'Report':
        html = export.generate_html_table(rows_tc_from_xml, ['Key', 'Name', 'Description', 'Objective', 'Last Test Run Result'], [])
    else:
        print("Error - output format argument poorly specified : " + args.output_type)
        return
    
    with open(args.output_filename, "w+") as text_file:
        text_file.write(html)
        print('\nHTML file written: ' + args.output_filename)
    

if __name__ == '__main__':
    main()

