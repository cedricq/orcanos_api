#!/usr/bin/python3

from tkinter import *
from tkinter.filedialog import asksaveasfile
from tkinter.ttk import *

from os.path import dirname, join, abspath

import orcanos_export as view
import orcanos_api as orca

VERSION = "2.0"

ITEMS =     ["RISKS",   "PR",   "SRS", "HW",    "MEC",  "TC",       'BR',       'Defects']
ITEMS_ORC = {"RISKS":"RISK", "PR":"REQ",  "SRS":"SRS", "HW":"HW",  "MEC":"MEC",  "TC":"T_CASE",   "BR":'MR_REQ',   "Defects":'DEFECT'}

window = Tk()
window.title("EVE - Orcanos Table Generator - " + VERSION)
window.geometry('700x350')

NB_COL = 4
data = []
frame = []
label = []
variables_lists = []
current_selections_temp = []

autocolorVal = BooleanVar()
autocolorVal.set(True)

def file_save(html_data):
    f = asksaveasfile(mode='w', defaultextension=".html", initialfile="output.html")
    if f is None: 
        return
    f.write(html_data)
    f.close() 
    

def check_variable_list_change(event):
    global variables_lists
    global current_selections_temp

    for i in range(NB_COL):
        try:
            # New item selected
            if len(variables_lists[i].curselection()) > len(current_selections_temp[i]) :
                for item in variables_lists[i].curselection() :
                    if item not in current_selections_temp[i] :
                        current_selections_temp[i].append(item)
            # Item to remove
            elif len(variables_lists[i].curselection()) < len(current_selections_temp[i]) :
                for item in current_selections_temp[i] :
                    if item not in variables_lists[i].curselection() :
                        current_selections_temp[i].remove(item)
        except IndexError:
            return None


def update_labels():
    for i in range(NB_COL):
        str = ""
        for j in range(len(ITEMS)):
            if data[i][ITEMS[j]].get() == True:
                if str == "":
                   str += ITEMS[j]
                else:
                   str += ', ' + ITEMS[j]
        label[i]["text"]=str

rows = {}
rows_all = []

def main():
    global autocolorVal
    global variables_lists
    for i in range(NB_COL):
        data.append({})
        
        f = Frame(window)
        f.grid(column=i, row=1)
        frame.append(f)
        
        l = Label(text = 'label'+str(i))
        l.grid(column=i, row=0)
        l["text"]=""
        label.append(l)
        
        mb =  Menubutton ( frame[i], text="Items")
        mb.menu  =  Menu ( mb, tearoff = 0 )
        mb["menu"]  =  mb.menu
        for item in ITEMS:
            var = BooleanVar()
            mb.menu.add_checkbutton(label=item, variable=var, command=update_labels)
            data[i][item] = var 
        mb.pack()
        
        variables_list = Listbox(frame[i], selectmode = "multiple", exportselection=0)
        variables_list.pack()
        variables_lists.append(variables_list)
    
    window.bind('<Button-1>', check_variable_list_change)
    
    pb = Progressbar(window, orient='horizontal', mode='determinate', length=280)
    pb.grid(column=0, row=2, columnspan=3, padx=10, pady=20)
    pb['value'] = 0
    
    def update_progress_label(str_in):
        return str_in + f"{pb['value']}%"
    
    value_label = Label(window, text=update_progress_label("Current progress: "))
    value_label.grid(column=2, row=2, columnspan=1)
    
    def clickImportButton():
        listItems_ = [] 
        index = 0 
        for d in data:
            listItems_.append([])
            for j in range(len(ITEMS)):
                if d[ITEMS[j]].get() == True:
                    if j not in listItems_[index]: 
                        listItems_[index].append(ITEMS[j])
            index += 1 
        
        listItems = []
        for it in listItems_:
            if len(it) != 0:
                listItems.append(it)
        print(listItems)
        
        overallNbItems = 0
        for i in listItems:
            for j in i:
                overallNbItems += 2
        downloadedItems = 0 
        
        rows_all.clear()
        fields = []
        for i, col in enumerate(listItems):
            r = []
            fields.append([]) 
            for j, item in enumerate(col):
                fields[i].append([]) 
                print("Downloading " + item + " from Orcanos ...")
                value_label['text'] = update_progress_label("Downloading " + item + ": ")
                downloadedItems += 1
                pb['value'] = int(downloadedItems * 100 / overallNbItems)
                value_label['text'] = update_progress_label("Downloading " + item + ": ")
                window.update()
                if not item in rows:
                    if ITEMS_ORC[item] == 'T_CASE':
                        rows[item] = orca.getWorkItems(ITEMS_ORC[item], orca.Filter['TC'], orca.Solution_ID['Eve'])
                    elif ITEMS_ORC[item] == 'RISK':
                        rows[item] = orca.getWorkItems(ITEMS_ORC[item], orca.Filter['RISKS'], orca.Solution_ID['Eve'])
                    else:
                        rows[item] = orca.getWorkItems(ITEMS_ORC[item], orca.Filter['All'], orca.Solution_ID['Eve'])
                    print(ITEMS_ORC[item] + ' ' +  orca.Filter['All'] + ' ' + orca.Solution_ID['Eve'])
                r += rows[item]
                downloadedItems += 1
                pb['value'] = int(downloadedItems * 100 / overallNbItems)
                value_label['text'] = update_progress_label("Downloading " + item + ": ")
                print("Downloading " + item + " from Orcanos complete")
                window.update()
                
                print(rows)

                for k in rows[item][0]:
                    fields[i][j].append(k)
                    
            temp_field = fields[i][0]
            for k in range(0, len(fields[i])-1):
                temp_field = list(set(temp_field).intersection(set(fields[i][k+1])))
            
            temp_field.insert(0, temp_field.pop(temp_field.index('Name')))
            temp_field.insert(0, temp_field.pop(temp_field.index('Key')))
            
            for k in temp_field:
                variables_lists[i].insert(END, k)
            variables_lists[i].select_set(0)
            variables_lists[i].select_set(1)
            current_selections_temp.append(list(variables_lists[i].curselection()))
            variables_lists[i].event_generate("<<ListboxSelect>>")
                
            rows_all.append(r)
        
        pb['value'] = 100
        value_label['text'] = update_progress_label("Current Progress: ")

    def clickGenButton():
        global autocolorVal        

        fields = []
        table = []
        trac = []
        try:
            for i in range(NB_COL):
                fields.append([variables_lists[i].get(idx) for idx in current_selections_temp[i]])
                if i > 0:
                    trac =  view.tracea( rows_all[i-1], rows_all[i] )
                    t = view.flatify_rows_in_table(trac, fields[i-1], fields[i])
                    table.append(t) 
        except IndexError:
            print("Do nothing")
        
        if len(table) == 0:
            html_content = view.generate_html_table(rows_all[0], fields[0], [])
        elif len(table) == 1:
            html_content = view.generate_html_table(trac, fields[0], fields[1])
        else:
            output = table[-1]
            for i in range(len(table)-2,-1,-1):
                output = view.merge_table(table[i], output)
            html_content = view.table_as_html(output, titleEntry.get())
            

        file_save(html_content)
                    
    importButton = Button(window, text="Import", command=clickImportButton)
    importButton.grid(column=0, row=2)
    
    genButton = Button(window, text="Generate", command=clickGenButton)
    genButton.grid(column=0, row=3, columnspan=1)
    
    titleLabel = Label(window, text="Table title: ")
    titleLabel.grid(column=1, row=3, columnspan=1, sticky = E)
    titleEntry = Entry(window, text="")
    titleEntry.grid(column=2, row=3, columnspan=1)

    Autocolor = Checkbutton(window, text = "Autocolor", variable = autocolorVal)
    Autocolor.grid(column=3, row=3, columnspan=1)

    window.mainloop()

def mainTest():
    
    ### For testing without Orcanos access
    raws = {}
    
    raws['RISKS'] =   [{'Key':'RISK-1', 'Name':'risk 1', 'Traced Items Info':'PR-1, PR-2', 'blah':'bloh'},
                       {'Key':'RISK-2', 'Name':'risk 2', 'Traced Items Info':'PR-2', 'blah':'bloh'},
                       {'Key':'RISK-3', 'Name':'risk 3', 'Traced Items Info':'', 'blah':'bloh'}]
    raws['PR']      = [{'Key':'PR-1', 'Name':'pr 1', 'Traced Items Info':'MECRS-1, MECRS-2'},
                       {'Key':'PR-2', 'Name':'pr 2', 'Traced Items Info':'MECRS-1, ElcRS-1'}, 
                       {'Key':'PR-3', 'Name':'pr 3', 'Traced Items Info':''}]
    raws['HW']      = [{'Key':'ElcRS-1', 'Name':'elec 1', 'Traced Items Info':'TC-10, TC-12', 'haha': "hoho"},
                       {'Key':'ElcRS-2', 'Name':'elec 2', 'Traced Items Info':'TC-11', 'haha': "hihi"}]
    raws['MEC']     = [{'Key':'MECRS-1', 'Name':'mech 1', 'Traced Items Info':'TC-20', "tata":"toto"},
                       {'Key':'MECRS-2', 'Name':'mech 2', 'Traced Items Info':'TC-21', "tata": "toto"}]
    raws['TC']      = [{'Key':'TC-10', 'Name':'tc 10', 'Last Test Run Result':'Pass'},
                       {'Key':'TC-11', 'Name':'tc 11', 'Last Test Run Result':'Pass'},
                       {'Key':'TC-12', 'Name':'tc 12', 'Last Test Run Result':'Pass'},
                       {'Key':'TC-20', 'Name':'tc 20', 'Last Test Run Result':'Fail'},
                       {'Key':'TC-21', 'Name':'tc 21', 'Last Test Run Result':'Pass'}]
    raws['SRS']     = []
    
    listItems = [['RISKS'], ['PR'], ['HW', 'MEC', 'SRS'], ['TC']]
    
    rows_pr_sub = view.tracea( raws['PR'], raws['HW'] + raws['MEC'] + raws['SRS'] )
    table_pr_sub = view.flatify_rows_in_table(rows_pr_sub, ['Key', 'Name'], ['Key', 'Name'])
    
    rows_risk_pr = view.tracea( raws['RISKS'], raws['PR'])
    table_risk_pr = view.flatify_rows_in_table(rows_risk_pr, ['Key', 'Name'], ['Key', 'Name'])
    
    rows_sub_tc = view.tracea( raws['HW'] + raws['MEC'] + raws['SRS'], raws['TC'])
    table_sub_tc = view.flatify_rows_in_table(rows_sub_tc, ['Key', 'Name'], ['Key', 'Name'])
    
    table = [table_risk_pr, table_pr_sub, table_sub_tc]
    output = table[-1] 
    output = view.merge_table(table[1], output)
    output = view.merge_table(table[0], output)
    
    for o in output:
        print(o)
    
    html = view.table_as_html(output, "xxxxxxxxxx----------xxxxxxxxxxx")
    with open("output.html", "w+") as text_file:
        text_file.write(html)
        
if __name__ == "__main__":
    main()
