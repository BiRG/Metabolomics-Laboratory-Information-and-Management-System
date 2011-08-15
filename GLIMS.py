#!/usr/bin/env python
from google.appengine.api import users
#from google.appengine.ext import webapp
import gdata.docs.data
import gdata.docs.client
import gdata.spreadsheet.service
#import logging

import re, os, tempfile, bisect
from collection import *

class Helper:
    #def __init__(self, email, password):
    def __init__(self):
        self.user = users.get_current_user()
        #logging.info('Logged in: '+user.email())
        self.client = gdata.docs.client.DocsClient(source='helper-0r1')
        self.client.ssl = True  # Force all API requests through HTTPS
        self.client.http_client.debug = False  # Set to True for debugging HTTP requests
        #self.client.ClientLogin(email, password, self.client.source)
        #self.client.GetAccessToken()
        self.spreadsheets_client = gdata.spreadsheet.service.SpreadsheetsService(source=self.client.source)
        #self.spreadsheets_client.ClientLogin(email, password, self.client.source)
    
    def get_studies(self):
        res = []
        feed = self.client.GetDocList(uri='/feeds/default/private/full/-/folder?title=BiRG%20Studies%20Data%20-%20DO%20NOT%20RENAME&title-exact=true')
        for e in feed.entry:
            res.append({'entry': e, 'resource_id': e.resource_id.text, 'name': e.title.text})
        return res

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
    
    def get_files_by_value(self,name,value):
        if self.metadata.has_key(name) == False:
            return None
        elif self.metadata[name].has_key(value) == False:
            return None
        else:
            src = self.metadata[name][value].content.src
            children_feed = self.helper.client.GetDocList(uri=src+'/-/contents')
            files = []
            for ce in children_feed.entry:
                if ce.GetDocumentType() == 'spreadsheet':
                    files.append(ce)
            return files
    
    def merge_xy_files(self,files):
        docs_token = self.helper.client.auth_token
        self.helper.client.auth_token = gdata.gauth.ClientLoginToken(self.helper.spreadsheets_client.GetClientLoginToken())
        xY = {}
        sorted_keys = []
        i = 0
        for file in files:
            fd, path = tempfile.mkstemp()
            self.helper.client.Export(file,path+'.csv')

            # Read and store for later
            xys = []
            f = open(path+'.csv','r')
            for line in f:
                xys.append(line.split(","))
            f.close()
            
            # Construct the x list from the first file
            if i == 0:
                for xy in xys:
                    x = float(xy[0])
                    xY[x] = []
                    sorted_keys.append(x)
                sorted_keys.reverse()
            
            # Initialize for this file
            for x in sorted_keys:
                xY[x].append(None)
                        
            for xy in xys:
                x = float(xy[0])
                y = float(xy[1])
                x_key = x
                if xY.has_key(x) == False: # Find the closest key
                    position = bisect.bisect(sorted_keys,x)
                    prev_x = None
                    x_key = None
                    if position > 0:
                        prev_x = sorted_keys[position-1]                    
                    next_x = None
                    if position < len(sorted_keys)-1:
                        next_x = sorted_keys[position + 1]
                    if prev_x == None and next_x == None:
                        raise("Something is incorrect")
                    elif prev_x == None:
                        x_key = next_x
                    elif next_x == None:
                        x_key = prev_x
                    else:
                        if abs(next_x - x) < abs(prev_x - x):
                            x_key = next_x
                        else:
                            x_key = prev_x
                if xY[x_key][i] == None: # Not yet added
                    xY[x_key][i] = y
                else: # Already added, so average
                    xY[x_key][i] = (xY[x_key][i] + y)/2

            i = i + 1
        
        self.helper.client.auth_token = docs_token
        sorted_keys.reverse()
        return xY,sorted_keys
    
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
            #self.move_into_folder(new_spreadsheets,self.entries[name])
            
            if isinstance(values,list):
                for i in range(0,len(values)):
                    self.add_metadata_value(name,str(values[i]))
                    self.move_into_folder(new_spreadsheets[i],self.metadata[name][str(values[i])])
            else:
                self.add_metadata_value(name,str(values))
                self.move_into_folder(new_spreadsheets,self.metadata[name][str(values)])   
    

##
##potential_studies = helper.get_collections('Sample Study')
##for study in potential_studies:
##    print study['name']
##
##study = Study(helper,potential_studies[0]['entry'])
##print study.metadata
