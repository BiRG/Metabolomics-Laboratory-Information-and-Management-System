import gdata.docs.data
import gdata.docs.client
import re, os
from collection import *

class Helper:
    def __init__(self, email, password):
        self.client = gdata.docs.client.DocsClient(source='helper-0r1')
        self.client.ssl = True  # Force all API requests through HTTPS
        self.client.http_client.debug = False  # Set to True for debugging HTTP requests
        self.client.ClientLogin(email, password, self.client.source)

    def get_collections(self, root_collection_name):
        res = []
        feed = self.client.GetDocList(uri='/feeds/default/private/full/-/folder?title='+root_collection_name+'&title-exact=true')
        for e in feed.entry:
            res.append({'entry': e, 'resource_id': e.resource_id.text, 'name': e.title.text})
        return res

    def get_sub_collections(self,e):
        res = []
        src = e.content.src
        if re.search('folder',src):
            children_feed = self.client.GetDocList(uri=src+'/-/folder?showfolders=true')
            for ce in children_feed.entry:
                if ce.GetDocumentType() == 'folder': #and ce.resource_id.text != e.resource_id.text:                    
                    #print 'Sub',ce.title.text
                    res.append({'entry': ce,'resource_id': ce.resource_id.text,'name': ce.title.text, 'sub': self.get_sub_collections(ce)})
        return res

class Study:
    def __init__(self,helper,root_collection):
        self.helper = helper
        self.metadata = {}
        self.entries = {}
        if isinstance(root_collection,str):
            self.root_entry = self.helper.client.Create(gdata.docs.data.FOLDER_LABEL, root_collection) 
        else:
            self.root_entry = root_collection
            res = helper.get_sub_collections(root_collection)

            for c in res:
                self.metadata[c['name']] = {}
                self.entries[c['name']] = c['entry']
                for sc in c['sub']:
                    self.metadata[c['name']][sc['name']] = sc['entry']

    # Creates a new metadata field called name, unless one already exists.
    def add_metadata_field(self,name):
        if not self.metadata.has_key(name):
            try:
                while True:
                    self.entries[name] = self.helper.client.Create(gdata.docs.data.FOLDER_LABEL, str(name), folder_or_id=self.root_entry)
                    self.metadata[name] = {}
                    break
            except:
                print "Create folder error. Retrying..."

    def add_metadata_value(self,name,value):
        if self.metadata[name].has_key(value) == False:
            while True:
                try:
                    self.metadata[name][value] = self.helper.client.Create(gdata.docs.data.FOLDER_LABEL, str(value), folder_or_id=self.entries[name])
                    break
                except:
                    print "Create folder error. Retrying..."        

    def move_into_folder(self,entries,folder):
        if not isinstance(entries,list):
            entries = [entries]
        # Move the spreadsheets into the root folder
        for doc in entries:
            while True:
                try:
                    self.helper.client.Move(doc,folder)
                    break
                except:
                    print "Move error. Retrying..."        

    def upload_files(self,c):
        # Upload the actual data files
        new_spreadsheets = []
        for i in range(0,len(c.Y)):
            fd, path = tempfile.mkstemp()
            s = []
            for j in range(0,len(c.x)):
                s.append(str(c.x[j])+","+str(c.Y[i][j])+"\n")
            os.write(fd,''.join(s))
            os.close(fd)
            while True:
                try:
                    ms = gdata.data.MediaSource(file_path=path, content_type=gdata.docs.data.MIMETYPES['CSV'])
                    new_spreadsheets.append(self.helper.client.Upload(ms, 'XY'))
                    break
                except:
                    print "Upload error. Retrying..."
            print "Finished",i+1,"out of",len(c.Y)

        self.move_into_folder(new_spreadsheets,self.root_entry)

        # Now move the metadata
        for name, values in c.metadata.iteritems():
            self.add_metadata_field(name)
            self.move_into_folder(new_spreadsheets,self.entries[name])
                        
            if isinstance(values,list):
                for i in range(0,len(values)):
                    self.add_metadata_value(name,str(values[i]))
                    self.move_into_folder(new_spreadsheets[i],self.metadata[name][str(values[i])])
            #else:
            #    self.add_metadata_value(name,str(values))
            #    self.move_into_folder(new_spreadsheets,self.metadata[name][str(values)])   
    

##
##potential_studies = helper.get_collections('Sample Study')
##for study in potential_studies:
##    print study['name']
##
##study = Study(helper,potential_studies[0]['entry'])
##print study.metadata
