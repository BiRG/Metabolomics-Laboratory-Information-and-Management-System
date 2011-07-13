import httplib, urllib, tempfile, os
from elementtree.ElementTree import fromstring

import gdata.docs.data
import gdata.docs.client

import sys
import getpass

class Collection:
    def get_collection(self,cid,name,password):
        self.cid = cid
        params = urllib.urlencode({'name': name, 'password': password})
        headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
        conn = httplib.HTTPConnection("birg.cs.wright.edu")
        conn.request("GET","/omics_analysis/spectra_collections/" + str(cid) + ".xml",params,headers)
        r = conn.getresponse()
        #print r1.status, r1.reason
        if r.status != 200:
            return r
        
        f = tempfile.TemporaryFile()
        data = r.read()
        e = fromstring(data)
        data_e = e.find("data")
        f.write(data_e.text)
        conn.close()

        f.seek(0)
        data_start = False
        for line in f:
            fields = line.rstrip().split("\t")
            if fields[0] == 'X' or fields[0] == 'x':
                data_start = True
                self.x = []
                self.Y = []
                for i in range(0,len(fields)-1):
                    self.Y.append([])
            elif data_start:
                self.x.append(float(fields[0]))
                for i in range(0,len(fields)-1):
                    self.Y[i].append(float(fields[i+1]))

        f.seek(0)
        self.metadata = {}
        for line in f:
            fields = line.rstrip().split("\t")
            if fields[0] == 'X' or fields[0] == 'x':
                break
            else:
                # Try to convert to numbers
                values = []
                for i in range(0,len(self.Y)):
                    values.append(None)
                all_empty = True
                try:
                    for i in range(1,len(fields)):
                        if fields[i] != None:
                            all_empty = False
                        v1 = int(fields[i])
                        v2 = float(fields[i])
                        if v1 == v2:
                            values[i-1] = v1
                        else:
                            values[i-1] = v2
                except ValueError:
                    values = [] # Has at least one string
                if len(values) == 0 and len(fields) > 1:
                    values = fields[1:len(fields)+1]

                self.metadata[fields[0]] = values
        f.close()        

        return r

c = Collection()
r = c.get_collection(1571,"Paul Anderson","birglab")
if r.status == 200:
    email = raw_input('E-mail: ')
    password = getpass.getpass('Password: ') 

    client = gdata.docs.client.DocsClient(source='yourCo-yourAppName-v1')
    client.ssl = True  # Force all API requests through HTTPS
    client.http_client.debug = False  # Set to True for debugging HTTP requests
    client.ClientLogin(email, password, client.source);

    new_spreadsheets = []
    for i in range(0,len(c.Y)):
        fd, path = tempfile.mkstemp()
        s = []
        for j in range(0,len(c.x)):
            s.append(str(c.x[j])+","+str(c.Y[i][j])+"\n")
        os.write(fd,''.join(s))
        os.close(fd)
        print path
        while True:
            try:
                ms = gdata.data.MediaSource(file_path=path, content_type=gdata.docs.data.MIMETYPES['CSV'])
                new_spreadsheets.append(client.Upload(ms, 'XY'))
                break
            except:
                print "Upload error"
        print "Finished"
        #os.remove(path)
        
    new_folder = client.Create(gdata.docs.data.FOLDER_LABEL, 'Sample Study')
    for doc in new_spreadsheets:
        while True:
            try:
                client.Move(doc,new_folder)
                break
            except:
                print "Move error"
        
    for k, values in c.metadata.iteritems():
        try:
            while True:
                sub_folder = client.Create(gdata.docs.data.FOLDER_LABEL, k, folder_or_id=new_folder)
                break
        except:
            print "Create folder error"
            
        for doc in new_spreadsheets:
            while True:
                try:
                    client.Move(doc,sub_folder)
                    break
                except:
                    print "Move error"
                    
        if isinstance(values,list):
            tmp = {}
            for i in range(0,len(values)):
                if tmp.has_key(values[i]) == False:
                    while True:
                        try:
                            sub_folder2 = client.Create(gdata.docs.data.FOLDER_LABEL, str(values[i]), folder_or_id=sub_folder)
                            tmp[values[i]] = sub_folder2
                            break
                        except:
                            print "Create folder error"
                else:
                    sub_folder2 = tmp[values[i]]
                while True:
                    try:
                        client.Move(new_spreadsheets[i],sub_folder2)
                        break
                    except:
                        print "Move error"
        else:
            while True:
                try:
                    sub_folder2 = client.Create(gdata.docs.data.FOLDER_LABEL, str(values), folder_or_id=sub_folder)
                    break
                except:
                    print "Create folder error"
                    
            for doc in new_spreadsheets:
                while True:
                    try:
                        client.Move(doc,sub_folder2)
                        break
                    except:
                        print "Move error"
                
        
