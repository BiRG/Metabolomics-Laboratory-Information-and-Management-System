import httplib, urllib, tempfile
from elementtree.ElementTree import fromstring

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


