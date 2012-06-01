# csv2dict2011.py
# -*- coding: utf-8 -*-
"""Reformat a dicom dictionary csv file (from e.g. standards docs) to Python syntax

   Write the DICOM dictionary elements as:
   tag: (VR, VM, description, keyword, is_retired)
   in python format
   
   Also write the repeating groups or elements (e.g. group "50xx")
   as masks that can be tested later for tag lookups that didn't work
"""
#
# Copyright 2011-2012, Darcy Mason
# This file is part of pydicom, released under an MIT licence.
# See license.txt file for more details.

csv_filename = "dict_2011.csv"
pydict_filename = "_dicom_dict.py"
main_dict_name = "DicomDictionary"
mask_dict_name = "RepeatersDictionary"

def write_dict(f, dict_name, attributes, tagIsString):
    if tagIsString:
        entry_format = """'%s': ('%s', '%s', "%s", '%s', '%s')"""
    else:
        entry_format = """%s: ('%s', '%s', "%s", '%s', '%s')"""
    f.write("\n%s = {\n" % dict_name)
    f.write(",\n".join(entry_format % attribute for attribute in attributes))
    f.write("}\n")

if __name__ == "__main__":
    import csv  # comma-separated value module

    csv_reader = csv.reader(file(csv_filename, 'rb'))

    main_attributes = []
    mask_attributes = []
    for row in csv_reader:
        tag, description, keyword, VR, VM, is_retired  = row
        if tag == '' or tag == "Tag":
            continue 
        tag = tag.strip()   # at least one item has extra blank on end
        VR = VR.strip()     # similarly, some VRs have extra blank
        keyword = keyword.strip()  # just in case
        group, elem = tag[1:-1].split(",")
        if is_retired.strip() == 'RET':
            is_retired = 'Retired'
        if VR == "see note": # used with some delimiter tags
            VR = "NONE"      # to be same as '08 dict in pydicom
        
        # Handle one case "(0020,3100 to 31FF)" by converting to mask
        # Do in general way in case others like this come in future standards
        if " to " in elem:
            from_elem, to_elem = elem.split(" to ")
            if from_elem.endswith("00") and to_elem.endswith("FF"):
                elem = from_elem[:2] + "xx"
            else:
                raise NotImplementedError, "Cannot mask '%s'" % elem
        
        if description.endswith(" "):
            description = description.rstrip()

        description = description.replace("’", "'") # non-ascii apostrophe
        description = description.replace("‑", "-") # non-ascii dash used, shows in utf-8 as this a character
        description = description.replace("µ", "u") # replace micro symbol
		
        # If blank (e.g. (0018,9445) and (0028,0020)), then add dummy vals
        if VR == '' and VM == '' and is_retired:
            VR = 'OB'
            VM = '1'
            description = "Retired-blank"
        
        # One odd tag in '11 standard (0028,3006)
        if VR == 'US  or OW':  # extra space
           VR = 'US or OW'
        # Handle retired "repeating group" tags e.g. group "50xx"
        if "x" in group or "x" in elem:
            tag = group + elem # simple concatenation
            mask_attributes.append((tag, VR, VM, description, is_retired, keyword))
        else:
            tag = "0x%s%s" % (group, elem)
            main_attributes.append((tag, VR, VM, description, is_retired, keyword))

    py_file = file(pydict_filename, "w")
    py_file.write("# %s\n" % pydict_filename)
    py_file.write('"""DICOM data dictionary auto-generated by %s"""\n' % __file__)
    write_dict(py_file, main_dict_name, main_attributes, tagIsString=False)
    write_dict(py_file, mask_dict_name, mask_attributes, tagIsString=True)

    py_file.close()

    print "Finished creating python file %s containing the dicom dictionary" % pydict_filename
    print "Wrote %d tags" % (len(main_attributes)+len(mask_attributes))
