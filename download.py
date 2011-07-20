# -*- coding: utf-8 -*-
"""
Created on Mon Jul 18 14:55:17 2011

@author: paul
"""
import glims

email = 'glims.test@gmail.com' #raw_input('Google E-mail: ')
password = 'birglab1' #raw_input("Password: ") #getpass.getpass('Password: ') 
study_name = 'ANIT' #raw_input("Study name: ")

helper = glims.Helper(email,password)
potential_studies = helper.get_collections(study_name)
if len(potential_studies) > 0:
    study = glims.Study(helper,potential_studies[0]['entry']) # Assume it is the one and only return (later this will have to be dynamic)
    files = study.get_files_by_value('Time','0')
    xY,sorted_keys = study.merge_xy_files(files)
    f = open('test.tab','w')
    for key in sorted_keys:
        f.write(str(key))
        f.write("\t")
        f.write("\t".join([str(y) for y in xY[key]]))
        f.write("\n")
    f.close()
    
print "Finished"