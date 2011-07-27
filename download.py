# -*- coding: utf-8 -*-
"""
Created on Mon Jul 18 14:55:17 2011

@author: paul
"""
import glims

email = 'glims.test@gmail.com' #raw_input('Google E-mail: ')
password = 'birglab1' #raw_input("Password: ") #getpass.getpass('Password: ') 
study_name = 'ANIT' #raw_input('Study name: ')
print 'Assigning runtime variables'
helper = glims.Helper(email,password)
print 'Fetching collections'
potential_studies = helper.get_collections(study_name)
if len(potential_studies) > 0:
    print 'Collections found; Fetching Study'
    # Assume it is the one and only return 
    # (later this will have to be dynamic)
    study = glims.Study(helper,potential_studies[0]['entry'])
    print 'Get all XY files associated with the study'
    files = study.get_files_by_value('Time','0')
    varCount = len(files);
    print 'Merge the Y variables'
    xY,sorted_keys = study.merge_xy_files(files)
    print 'Save the variables to a file'
    f = open('test.tab','w')
    f.write('X')
    for fileIndex in range(1,varCount+1):
        f.write('\tY'+str(fileIndex))
    f.write('\n')
    for key in sorted_keys:
        f.write(str(key))
        f.write('\t')
        f.write('\t'.join([str(y) for y in xY[key]]))
        f.write('\n')
    f.close()
    
print 'Finished'