#!/usr/bin/env python
# Based on Google's official Python documentation
#import cgi

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

# From upload.py
import collection
import glims
glims = reload(glims)


class NoCollectionException(Exception):
    def __init__(self,value):
        self.specific_msg = value

    def __str__(self):
        return repr(self.specific_msg)


class CopyingHandler(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()

        if user:
            
            name = self.request.POST['birgun'];
            password = self.request.POST['birgpass'];
            cid = self.request.POST['birgcolid'];
            
            c = collection.Collection()
            r = c.get_collection(cid,name,password)

            if r.status != 200:
                raise NoCollectionException('Failed to get the collection')

            #email = 'glims.test@gmail.com' #raw_input('Google E-mail: ')
            #password = 'birglab1' #raw_input("Password: ") #getpass.getpass('Password: ') 
            #study_name = 'ANIT' #raw_input("Study name: ")

            # Assign the files to folders
            #helper = glims.Helper(email,password)
            helper = glims.Helper()
            potential_studies = helper.get_collections(study_name)

            if len(potential_studies) > 0:
                # Assume it is the one and only return (later this will have to be dynamic)
                study = glims.Study(helper,potential_studies[0]['entry'])
            else:
                study = glims.Study(helper,study_name)

            study.upload_files(c)
            
            # Report success.
            self.response.out.write("""<!DOCTYPE HTML>
<html>
    <head>
        <title></title>
    </head>
    <body>
        <!-- Username: %s -->
        <p>A copy of collection #%d has been transferred from BiRG to Google Docs.</p>
    </body>
</html>
""" % (name,cid))

        else:
            # TODO: Needs to redirect the logged in user back to the root.
            #self.redirect(users.create_login_url(self.request.uri))
            self.redirect("google.com")


class DownloadHandler(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()

        if user:
            self.response.out.write("""<!DOCTYPE HTML>
<html>
    <head>
        <title></title>
    </head>
    <body>
        <a href="">Your file is ready.</a>
    </body>
</html>
""")

        else:
            # TODO: Needs to redirect the logged in user back to the root.
            #self.redirect(users.create_login_url(self.request.uri))
            self.redirect("google.com")


class FileSendHandler(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()

        if user:
            collectionFile = self.request.POST['collectionFile'];
            
            # Assign the files to folders
            #helper = glims.Helper()
            #potential_studies = helper.get_collections(study_name)
            #if len(potential_studies) > 0:
            #    study = glims.Study(helper,potential_studies[0]['entry']) # Assume it is the one and only return (later this will have to be dynamic)
            #else:
            #    study = glims.Study(helper,study_name)
            #
            #study.upload_files(c)

            # Report success.
            self.response.out.write("""<!DOCTYPE HTML>
<html>
    <head>
        <title></title>
    </head>
    <body>
        <p>Your file is uploaded.</p>
    </body>
</html>
""")
        else:
            # TODO: Needs to redirect the logged in user back to the root.
            #self.redirect(users.create_login_url(self.request.uri))
            self.redirect("google.com")


class MainHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()

        if user:
            self.response.out.write("""<!DOCTYPE HTML>
<html>
    <head>
        <title></title>
    </head>
    <body>
        <form action="/upload" method="post">
            <div><input type="submit" value="Upload a Collection"></div>
        </form>
        <form action="/download" method="post">
            <div><input type="submit" value="Download a Collection"></div>
        </form>
        <form action="/xfer" method="post">
            <div><input type="submit" value="Transfer a Collection"></div>
        </form>
    </body>
</html>
""")
        else:
            self.redirect(users.create_login_url(self.request.uri))


class TransferHandler(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()

        if user:
            helper = glims.Helper()
            self.response.out.write("""<!DOCTYPE HTML>
<html>
    <head>
        <title></title>
    </head>
    <body>
        <p>Please enter your BiRG Metabolomics Management credentials & target collection ID.</p>
        <form action="/cpdata" method="post">
            <p>BiRG user name:</p>
            <div><input type="text" name="birgun"></div>
            <p>BiRG password:</p>
            <div><input type="text" name="birgpass"></div>
            <p>BiRG collection ID:</p>
            <div><input type="text" name="birgcolid"></div>
            <div><input type="submit" value="Initiate Transfer"></div>
        </form>
    </body>
</html>
""")

        else:
            # TODO: Needs to redirect the logged in user back to the root.
            #self.redirect(users.create_login_url(self.request.uri))
            self.redirect("google.com")


class UploadHandler(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()

        if user:
            self.response.out.write("""<!DOCTYPE HTML>
<html>
    <head>
        <title></title>
    </head>
    <body>
        <p>Please select the collection file to be uploaded:</p>
        <form action="/filesent" method="post">
            <input type="file" name="collectionFile" required="required">
            <div><input type="submit" value="Initiate Transfer"></div>
        </form>
    </body>
</html>
""")
            
        else:
            # TODO: Needs to redirect the logged in user back to the root.
            #self.redirect(users.create_login_url(self.request.uri))
            self.redirect("google.com")


def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/upload', UploadHandler),
                                          ('/download', DownloadHandler),
                                          ('/xfer', TransferHandler),
                                          ('/cpdata', CopyingHandler),
                                          ('/filesent', FileSendHandler)],
                                      debug=True)
    run_wsgi_app(application)


if __name__ == '__main__':
    main()
