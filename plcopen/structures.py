#!/usr/bin/env python
# -*- coding: utf-8 -*-

#This file is part of PLCOpenEditor, a library implementing an IEC 61131-3 editor
#based on the plcopen standard. 
#
#Copyright (C) 2007: Edouard TISSERANT and Laurent BESSARD
#
#See COPYING file for copyrights details.
#
#This library is free software; you can redistribute it and/or
#modify it under the terms of the GNU General Public
#License as published by the Free Software Foundation; either
#version 2.1 of the License, or (at your option) any later version.
#
#This library is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#General Public License for more details.
#
#You should have received a copy of the GNU General Public
#License along with this library; if not, write to the Free Software
#Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import string, os, sys, re
from plcopen import LoadProject
from collections import OrderedDict

LANGUAGES = ["IL","ST","FBD","LD","SFC"]

LOCATIONDATATYPES = {"X" : ["BOOL"],
                     "B" : ["SINT", "USINT", "BYTE", "STRING"],
                     "W" : ["INT", "UINT", "WORD", "WSTRING"],
                     "D" : ["DINT", "UDINT", "REAL", "DWORD"],
                     "L" : ["LINT", "ULINT", "LREAL", "LWORD"]} 

_ = lambda x:x

#-------------------------------------------------------------------------------
#                        Function Block Types definitions
#-------------------------------------------------------------------------------

ScriptDirectory = os.path.split(os.path.realpath(__file__))[0]

StdBlockLibrary, error = LoadProject(
    os.path.join(ScriptDirectory, "Standard_Function_Blocks.xml"))
AddnlBlockLibrary, error = LoadProject(
    os.path.join(ScriptDirectory, "Additional_Function_Blocks.xml"))

StdBlockComments = {
    "SR": _("SR bistable\nThe SR bistable is a latch where the Set dominates."),
    "RS": _("RS bistable\nThe RS bistable is a latch where the Reset dominates."),
    "SEMA": _("Semaphore\nThe semaphore provides a mechanism to allow software elements mutually exclusive access to certain ressources."),
    "R_TRIG": _("Rising edge detector\nThe output produces a single pulse when a rising edge is detected."),
    "F_TRIG": _("Falling edge detector\nThe output produces a single pulse when a falling edge is detected."),
    "CTU": _("Up-counter\nThe up-counter can be used to signal when a count has reached a maximum value."),
    "CTD": _("Down-counter\nThe down-counter can be used to signal when a count has reached zero, on counting down from a preset value."),
    "CTUD": _("Up-down counter\nThe up-down counter has two inputs CU and CD. It can be used to both count up on one input and down on the other."),
    "TP": _("Pulse timer\nThe pulse timer can be used to generate output pulses of a given time duration."),
    "TON": _("On-delay timer\nThe on-delay timer can be used to delay setting an output true, for fixed period after an input becomes true."),
    "TOF": _("Off-delay timer\nThe off-delay timer can be used to delay setting an output false, for fixed period after input goes false."),
    "RTC": _("Real time clock\nThe real time clock has many uses including time stamping, setting dates and times of day in batch reports, in alarm messages and so on."),
    "INTEGRAL": _("Integral\nThe integral function block integrates the value of input XIN over time."),
    "DERIVATIVE": _("Derivative\nThe derivative function block produces an output XOUT proportional to the rate of change of the input XIN."),
    "PID": _("PID\nThe PID (proportional, Integral, Derivative) function block provides the classical three term controller for closed loop control."),
    "RAMP": _("Ramp\nThe RAMP function block is modelled on example given in the standard."),
    "HYSTERESIS": _("Hysteresis\nThe hysteresis function block provides a hysteresis boolean output driven by the difference of two floating point (REAL) inputs XIN1 and XIN2."),
}

for block_type in ["CTU", "CTD", "CTUD"]:
    for return_type in ["DINT", "LINT", "UDINT", "ULINT"]:
        StdBlockComments["%s_%s" % (block_type, return_type)] = StdBlockComments[block_type]

def GetBlockInfos(pou):
    infos = pou.getblockInfos()
    infos["comment"] = StdBlockComments[infos["name"]]
    infos["inputs"] = [
        (var_name, var_type, "rising")
        if var_name in ["CU", "CD"]
        else (var_name, var_type, var_modifier)
        for var_name, var_type, var_modifier in infos["inputs"]]
    return infos

"""
Ordored list of common Function Blocks defined in the IEC 61131-3
Each block have this attributes:
    - "name" : The block name
    - "type" : The block type. It can be "function", "functionBlock" or "program"
    - "extensible" : Boolean that define if the block is extensible
    - "inputs" : List of the block inputs
    - "outputs" : List of the block outputs
    - "comment" : Comment that will be displayed in the block popup
    - "generate" : Method that generator will call for generating ST block code
Inputs and outputs are a tuple of characteristics that are in order:
    - The name
    - The data type
    - The default modifier which can be "none", "negated", "rising" or "falling"
"""

StdBlckLst = [{"name" : _("Standard function blocks"), "list":
               [GetBlockInfos(pou) for pou in StdBlockLibrary.getpous()]},
              {"name" : _("Additional function blocks"), "list":
               [GetBlockInfos(pou) for pou in AddnlBlockLibrary.getpous()]},
             ]


#-------------------------------------------------------------------------------
#                           Data Types definitions
#-------------------------------------------------------------------------------

"""
Ordored list of common data types defined in the IEC 61131-3
Each type is associated to his direct parent type. It defines then a hierarchy
between type that permits to make a comparison of two types
"""
TypeHierarchy_list = [
    ("ANY", None),
    ("ANY_DERIVED", "ANY"),
    ("ANY_ELEMENTARY", "ANY"),
    ("ANY_MAGNITUDE", "ANY_ELEMENTARY"),
    ("ANY_BIT", "ANY_ELEMENTARY"),
    ("ANY_NBIT", "ANY_BIT"),
    ("ANY_STRING", "ANY_ELEMENTARY"),
    ("ANY_DATE", "ANY_ELEMENTARY"),
    ("ANY_NUM", "ANY_MAGNITUDE"),
    ("ANY_REAL", "ANY_NUM"),
    ("ANY_INT", "ANY_NUM"),
    ("ANY_SINT", "ANY_INT"),
    ("ANY_UINT", "ANY_INT"),
    ("BOOL", "ANY_BIT"),
    ("SINT", "ANY_SINT"),
    ("INT", "ANY_SINT"),
    ("DINT", "ANY_SINT"),
    ("LINT", "ANY_SINT"),
    ("USINT", "ANY_UINT"),
    ("UINT", "ANY_UINT"),
    ("UDINT", "ANY_UINT"),
    ("ULINT", "ANY_UINT"),
    ("REAL", "ANY_REAL"),
    ("LREAL", "ANY_REAL"),
    ("TIME", "ANY_MAGNITUDE"),
    ("DATE", "ANY_DATE"),
    ("TOD", "ANY_DATE"),
    ("DT", "ANY_DATE"),
    ("STRING", "ANY_STRING"),
    ("BYTE", "ANY_NBIT"),
    ("WORD", "ANY_NBIT"),
    ("DWORD", "ANY_NBIT"),
    ("LWORD", "ANY_NBIT")
    #("WSTRING", "ANY_STRING") # TODO
]

TypeHierarchy = dict(TypeHierarchy_list)

"""
returns true if the given data type is the same that "reference" meta-type or one of its types.
"""
def IsOfType(type, reference):
    if reference is None:
        return True
    elif type == reference:
        return True
    else:
        parent_type = TypeHierarchy[type]
        if parent_type is not None:
            return IsOfType(parent_type, reference)
    return False

"""
returns list of all types that correspont to the ANY* meta type
"""
def GetSubTypes(type):
    return [typename for typename, parenttype in TypeHierarchy.items() if not typename.startswith("ANY") and IsOfType(typename, type)]


DataTypeRange_list = [
    ("SINT", (-2**7, 2**7 - 1)),
    ("INT", (-2**15, 2**15 - 1)),
    ("DINT", (-2**31, 2**31 - 1)),
    ("LINT", (-2**31, 2**31 - 1)),
    ("USINT", (0, 2**8 - 1)),
    ("UINT", (0, 2**16 - 1)),
    ("UDINT", (0, 2**31 - 1)),
    ("ULINT", (0, 2**31 - 1))
]

DataTypeRange = dict(DataTypeRange_list)



#-------------------------------------------------------------------------------
#                             Test identifier
#-------------------------------------------------------------------------------

IDENTIFIER_MODEL = re.compile(
    "(?:%(letter)s|_(?:%(letter)s|%(digit)s))(?:_?(?:%(letter)s|%(digit)s))*$" %
    {"letter": "[a-zA-Z]", "digit": "[0-9]"})

# Test if identifier is valid
def TestIdentifier(identifier):
     return IDENTIFIER_MODEL.match(identifier) is not None

#-------------------------------------------------------------------------------
#                        Standard functions list generation
#-------------------------------------------------------------------------------


"""
take a .csv file and translate it it a "csv_table"
"""            
def csv_file_to_table(file):
    return [ map(string.strip,line.split(';')) for line in file.xreadlines()]

"""
seek into the csv table to a section ( section_name match 1st field )
return the matching row without first field
"""
def find_section(section_name, table):
    fields = [None]
    while(fields[0] != section_name):
        fields = table.pop(0)
    return fields[1:]

"""
extract the standard functions standard parameter names and types...
return a { ParameterName: Type, ...}
"""
def get_standard_funtions_input_variables(table):
    variables = find_section("Standard_functions_variables_types", table)
    standard_funtions_input_variables = {}
    fields = [True,True]
    while(fields[1]):
        fields = table.pop(0)
        variable_from_csv = dict([(champ, val) for champ, val in zip(variables, fields[1:]) if champ!=''])
        standard_funtions_input_variables[variable_from_csv['name']] = variable_from_csv['type']
    return standard_funtions_input_variables
    
"""
translate .csv file input declaration into PLCOpenEditor interessting values
in : "(ANY_NUM, ANY_NUM)" and { ParameterName: Type, ...}
return [("IN1","ANY_NUM","none"),("IN2","ANY_NUM","none")] 
"""
def csv_input_translate(str_decl, variables, base):
    decl = str_decl.replace('(','').replace(')','').replace(' ','').split(',')
    params = []
    
    len_of_not_predifined_variable = len([True for param_type in decl if param_type not in variables])
    
    for param_type in decl:
        if param_type in variables.keys():
            param_name = param_type
            param_type = variables[param_type]
        elif len_of_not_predifined_variable > 1:
            param_name = "IN%d"%base
            base += 1
        else:
            param_name = "IN"
        params.append((param_name, param_type, "none"))
    return params


ANY_TO_ANY_LIST=[
        # simple type conv are let as C cast
        (("ANY_INT","ANY_BIT"),("ANY_NUM","ANY_BIT"), ("return_type", "__move_", "IN_type")),
        (("ANY_REAL",),("ANY_REAL",), ("return_type", "__move_", "IN_type")),
        # REAL_TO_INT
        (("ANY_REAL",),("ANY_SINT",), ("return_type", "__real_to_sint", None)),
        (("ANY_REAL",),("ANY_UINT",), ("return_type", "__real_to_uint", None)),
        (("ANY_REAL",),("ANY_BIT",), ("return_type", "__real_to_bit", None)),
        # TO_TIME
        (("ANY_INT","ANY_BIT"),("ANY_DATE","TIME"), ("return_type", "__int_to_time", None)),
        (("ANY_REAL",),("ANY_DATE","TIME"), ("return_type", "__real_to_time", None)),
        (("ANY_STRING",), ("ANY_DATE","TIME"), ("return_type", "__string_to_time", None)),
        # FROM_TIME
        (("ANY_DATE","TIME"), ("ANY_REAL",), ("return_type", "__time_to_real", None)),
        (("ANY_DATE","TIME"), ("ANY_INT","ANY_NBIT"), ("return_type", "__time_to_int", None)),
        (("TIME",), ("ANY_STRING",), ("return_type", "__time_to_string", None)),
        (("DATE",), ("ANY_STRING",), ("return_type", "__date_to_string", None)),
        (("TOD",), ("ANY_STRING",), ("return_type", "__tod_to_string", None)),
        (("DT",), ("ANY_STRING",), ("return_type", "__dt_to_string", None)),
        # TO_STRING
        (("BOOL",), ("ANY_STRING",), ("return_type", "__bool_to_string", None)),
        (("ANY_BIT",), ("ANY_STRING",), ("return_type", "__bit_to_string", None)),
        (("ANY_REAL",), ("ANY_STRING",), ("return_type", "__real_to_string", None)),
        (("ANY_SINT",), ("ANY_STRING",), ("return_type", "__sint_to_string", None)),
        (("ANY_UINT",), ("ANY_STRING",), ("return_type", "__uint_to_string", None)),
        # FROM_STRING
        (("ANY_STRING",), ("BOOL",), ("return_type", "__string_to_bool", None)),
        (("ANY_STRING",), ("ANY_BIT",), ("return_type", "__string_to_bit", None)),
        (("ANY_STRING",), ("ANY_SINT",), ("return_type", "__string_to_sint", None)),
        (("ANY_STRING",), ("ANY_UINT",), ("return_type", "__string_to_uint", None)),
        (("ANY_STRING",), ("ANY_REAL",), ("return_type", "__string_to_real", None))]


BCD_TO_ANY_LIST=[
        (("BYTE",),("USINT",), ("return_type", "__bcd_to_uint", None)),
        (("WORD",),("UINT",), ("return_type", "__bcd_to_uint", None)),
        (("DWORD",),("UDINT",), ("return_type", "__bcd_to_uint", None)),
        (("LWORD",),("ULINT",), ("return_type", "__bcd_to_uint", None))]


ANY_TO_BCD_LIST=[
        (("USINT",),("BYTE",), ("return_type", "__uint_to_bcd", None)),
        (("UINT",),("WORD",), ("return_type", "__uint_to_bcd", None)),
        (("UDINT",),("DWORD",), ("return_type", "__uint_to_bcd", None)),
        (("ULINT",),("LWORD",), ("return_type", "__uint_to_bcd", None))]


def ANY_TO_ANY_FORMAT_GEN(any_to_any_list, fdecl):

    for (InTypes, OutTypes, Format) in any_to_any_list:
        outs = reduce(lambda a,b: a or b, map(lambda testtype : IsOfType(fdecl["outputs"][0][1],testtype), OutTypes))
        inps = reduce(lambda a,b: a or b, map(lambda testtype : IsOfType(fdecl["inputs"][0][1],testtype), InTypes))
        if inps and outs and fdecl["outputs"][0][1] != fdecl["inputs"][0][1]:
             return Format
    
    return None


"""
Returns this kind of declaration for all standard functions

            [{"name" : "Numerical", 'list': [   {   
                'baseinputnumber': 1,
                'comment': 'Addition',
                'extensible': True,
                'inputs': [   ('IN1', 'ANY_NUM', 'none'),
                              ('IN2', 'ANY_NUM', 'none')],
                'name': 'ADD',
                'outputs': [('OUT', 'ANY_NUM', 'none')],
                'type': 'function'}, ...... ] },.....]
"""
def get_standard_funtions(table):
    
    variables = get_standard_funtions_input_variables(table)
    
    fonctions = find_section("Standard_functions_type",table)

    Standard_Functions_Decl = []
    Current_section = None
    
    translate = {
            "extensible" : lambda x: {"yes":True, "no":False}[x],
            "inputs" : lambda x:csv_input_translate(x,variables,baseinputnumber),
            "outputs":lambda x:[("OUT",x,"none")]}
    
    for fields in table:
        if fields[1]:
            # If function section name given
            if fields[0]:
                words = fields[0].split('"')
                if len(words) > 1:
                    section_name = words[1]
                else:
                    section_name = fields[0]
                Current_section = {"name" : section_name, "list" : []}
                Standard_Functions_Decl.append(Current_section)
                Function_decl_list = []
            if Current_section:
                Function_decl = dict([(champ, val) for champ, val in zip(fonctions, fields[1:]) if champ])
                baseinputnumber = int(Function_decl.get("baseinputnumber",1))
                Function_decl["baseinputnumber"] = baseinputnumber
                for param, value in Function_decl.iteritems():
                    if param in translate:
                        Function_decl[param] = translate[param](value)
                Function_decl["type"] = "function"
                
                if Function_decl["name"].startswith('*') or Function_decl["name"].endswith('*') :
                    input_ovrloading_types = GetSubTypes(Function_decl["inputs"][0][1])
                    output_types = GetSubTypes(Function_decl["outputs"][0][1])
                else:
                    input_ovrloading_types = [None]
                    output_types = [None]
                
                funcdeclname_orig = Function_decl["name"]
                funcdeclname = Function_decl["name"].strip('*_')
                fdc = Function_decl["inputs"][:]
                for intype in input_ovrloading_types:
                    if intype != None:
                        Function_decl["inputs"] = []
                        for decl_tpl in fdc:
                            if IsOfType(intype, decl_tpl[1]):
                                Function_decl["inputs"] += [(decl_tpl[0], intype, decl_tpl[2])]
                            else:
                                Function_decl["inputs"] += [(decl_tpl)]
                            
                            if funcdeclname_orig.startswith('*'):
                                funcdeclin = intype + '_' + funcdeclname 
                            else:
                                funcdeclin = funcdeclname
                    else:
                        funcdeclin = funcdeclname
                        
                    for outype in output_types:
                        if outype != None:
                            decl_tpl = Function_decl["outputs"][0]
                            Function_decl["outputs"] = [ (decl_tpl[0] , outype,  decl_tpl[2])]
                            if funcdeclname_orig.endswith('*'):
                                funcdeclout =  funcdeclin + '_' + outype
                            else:
                                funcdeclout =  funcdeclin
                        else:
                            funcdeclout =  funcdeclin
                        Function_decl["name"] = funcdeclout


                        fdecl = Function_decl
                        res = eval(Function_decl["python_eval_c_code_format"])

                        if res != None :
                            # create the copy of decl dict to be appended to section
                            Function_decl_copy = Function_decl.copy()
                            Current_section["list"].append(Function_decl_copy)
            else:
                raise "First function must be in a category"
    
    return Standard_Functions_Decl

std_decl = get_standard_funtions(csv_file_to_table(open(os.path.join(ScriptDirectory,"iec_std.csv"))))#, True)

StdBlckLst.extend(std_decl)

# Dictionary to speedup block type fetching by name
StdBlckDct = OrderedDict()

for section in StdBlckLst:
    for desc in section["list"]:
        words = desc["comment"].split('"')
        if len(words) > 1:
            desc["comment"] = words[1]
        desc["usage"] = ("\n (%s) => (%s)" % 
            (", ".join(["%s:%s" % (input[1], input[0]) 
                        for input in desc["inputs"]]),
             ", ".join(["%s:%s" % (output[1], output[0]) 
                        for output in desc["outputs"]])))
        BlkLst = StdBlckDct.setdefault(desc["name"],[])
        BlkLst.append((section["name"], desc))

#-------------------------------------------------------------------------------
#                            Languages Keywords
#-------------------------------------------------------------------------------


# Keywords for Pou Declaration
POU_BLOCK_START_KEYWORDS = ["FUNCTION", "FUNCTION_BLOCK", "PROGRAM"]
POU_BLOCK_END_KEYWORDS = ["END_FUNCTION", "END_FUNCTION_BLOCK", "END_PROGRAM"]
POU_KEYWORDS = ["EN", "ENO", "F_EDGE", "R_EDGE"] + POU_BLOCK_START_KEYWORDS + POU_BLOCK_END_KEYWORDS
for category in StdBlckLst:
    for block in category["list"]:
        if block["name"] not in POU_KEYWORDS:
            POU_KEYWORDS.append(block["name"])


# Keywords for Type Declaration
TYPE_BLOCK_START_KEYWORDS = ["TYPE", "STRUCT"]
TYPE_BLOCK_END_KEYWORDS = ["END_TYPE", "END_STRUCT"]
TYPE_KEYWORDS = ["ARRAY", "OF", "T", "D", "TIME_OF_DAY", "DATE_AND_TIME"] + TYPE_BLOCK_START_KEYWORDS + TYPE_BLOCK_END_KEYWORDS
TYPE_KEYWORDS.extend([keyword for keyword in TypeHierarchy.keys() if keyword not in TYPE_KEYWORDS])


# Keywords for Variable Declaration
VAR_BLOCK_START_KEYWORDS = ["VAR", "VAR_INPUT", "VAR_OUTPUT", "VAR_IN_OUT", "VAR_TEMP", "VAR_EXTERNAL"]
VAR_BLOCK_END_KEYWORDS = ["END_VAR"]
VAR_KEYWORDS = ["AT", "CONSTANT", "RETAIN", "NON_RETAIN"] + VAR_BLOCK_START_KEYWORDS + VAR_BLOCK_END_KEYWORDS


# Keywords for Configuration Declaration
CONFIG_BLOCK_START_KEYWORDS = ["CONFIGURATION", "RESOURCE", "VAR_ACCESS", "VAR_CONFIG", "VAR_GLOBAL"]
CONFIG_BLOCK_END_KEYWORDS = ["END_CONFIGURATION", "END_RESOURCE", "END_VAR"]
CONFIG_KEYWORDS = ["ON", "PROGRAM", "WITH", "READ_ONLY", "READ_WRITE", "TASK"] + CONFIG_BLOCK_START_KEYWORDS + CONFIG_BLOCK_END_KEYWORDS

# Keywords for Structured Function Chart
SFC_BLOCK_START_KEYWORDS = ["ACTION", "INITIAL_STEP", "STEP", "TRANSITION"]
SFC_BLOCK_END_KEYWORDS = ["END_ACTION", "END_STEP", "END_TRANSITION"]
SFC_KEYWORDS = ["FROM", "TO"] + SFC_BLOCK_START_KEYWORDS + SFC_BLOCK_END_KEYWORDS


# Keywords for Instruction List
IL_KEYWORDS = ["TRUE", "FALSE", "LD", "LDN", "ST", "STN", "S", "R", "AND", "ANDN", "OR", "ORN",
 "XOR", "XORN", "NOT", "ADD", "SUB", "MUL", "DIV", "MOD", "GT", "GE", "EQ", "NE",
 "LE", "LT", "JMP", "JMPC", "JMPCN", "CAL", "CALC", "CALCN", "RET", "RETC", "RETCN"]


# Keywords for Structured Text
ST_BLOCK_START_KEYWORDS = ["IF", "ELSIF", "ELSE", "CASE", "FOR", "WHILE", "REPEAT"]
ST_BLOCK_END_KEYWORDS = ["END_IF", "END_CASE", "END_FOR", "END_WHILE", "END_REPEAT"]
ST_KEYWORDS = ["TRUE", "FALSE", "THEN", "OF", "TO", "BY", "DO", "DO", "UNTIL", "EXIT", 
 "RETURN", "NOT", "MOD", "AND", "XOR", "OR"] + ST_BLOCK_START_KEYWORDS + ST_BLOCK_END_KEYWORDS

# All the keywords of IEC
IEC_BLOCK_START_KEYWORDS = []
IEC_BLOCK_END_KEYWORDS = []
IEC_KEYWORDS = ["E", "TRUE", "FALSE"]
for all_keywords, keywords_list in [(IEC_BLOCK_START_KEYWORDS, [POU_BLOCK_START_KEYWORDS, TYPE_BLOCK_START_KEYWORDS,
                                                                VAR_BLOCK_START_KEYWORDS, CONFIG_BLOCK_START_KEYWORDS,
                                                                SFC_BLOCK_START_KEYWORDS, ST_BLOCK_START_KEYWORDS]),
                                    (IEC_BLOCK_END_KEYWORDS, [POU_BLOCK_END_KEYWORDS, TYPE_BLOCK_END_KEYWORDS,
                                                              VAR_BLOCK_END_KEYWORDS, CONFIG_BLOCK_END_KEYWORDS,
                                                              SFC_BLOCK_END_KEYWORDS, ST_BLOCK_END_KEYWORDS]),
                                    (IEC_KEYWORDS, [POU_KEYWORDS, TYPE_KEYWORDS, VAR_KEYWORDS, CONFIG_KEYWORDS,
                                                    SFC_KEYWORDS, IL_KEYWORDS, ST_KEYWORDS])]:
    for keywords in keywords_list:
        all_keywords.extend([keyword for keyword in keywords if keyword not in all_keywords])

