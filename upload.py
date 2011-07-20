import getpass

import collection
import glims
glims = reload(glims)

c = collection.Collection()
name = raw_input("BiRG Username: ")
password = raw_input("Password: ") #getpass.getpass('Password: ')
cid = int(raw_input("Collection ID: "))
r = c.get_collection(cid,name,password)

if r.status != 200:
    raise "Failed to get the collection"

email = 'glims.test@gmail.com' #raw_input('Google E-mail: ')
password = 'birglab1' #raw_input("Password: ") #getpass.getpass('Password: ') 
study_name = 'ANIT' #raw_input("Study name: ")

# Assign the files to folders
helper = glims.Helper(email,password)
potential_studies = helper.get_collections(study_name)
if len(potential_studies) > 0:
    study = glims.Study(helper,potential_studies[0]['entry']) # Assume it is the one and only return (later this will have to be dynamic)
else:
    study = glims.Study(helper,study_name)

study.upload_files(c)

            
    
