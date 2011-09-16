#!/usr/bin/env python
# Based on Google's official Python documentation
#import cgi

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app, login_required
import gdata.gauth
import gdata.docs.client


# From upload.py
import collection
import glims
glims = reload(glims)


# From http://code.google.com/appengine/articles/python/retrieving_gdata_feeds.html
# Constants included for ease of understanding. It is a more common
# and reliable practice to create a helper for reading a Consumer Key
# and Secret from a config file. You may have different consumer keys
# and secrets for different environments, and you also may not want to
# check these values into your source code repository.
SETTINGS = {
    'APP_NAME': 'birgdata',
    'CONSUMER_KEY': 'birgdata.appspot.com',
    'CONSUMER_SECRET': 'VAeTG4YvQYlmcYS8xwK7V2d6',
    'SCOPES': ['https://docs.google.com/feeds/']
    }

#credfile = open(".credentials.info")
#credentials = credfile.readlines()
#credfile.close()
#if credentials.count() > 1:
#    SETTINGS['CONSUMER_KEY'] = credentials[0]
#    SETTINGS['CONSUMER_SECRET'] = credentials[1]

# From http://code.google.com/appengine/articles/python/retrieving_gdata_feeds.html
# Create an instance of the DocsService to make API calls
gdocs = gdata.docs.client.DocsClient(source = SETTINGS['APP_NAME'])


class NoCollectionWithIDException(Exception):
    def __init__(self,value):
        self.specific_msg = value

    def __str__(self):
        return repr(self.specific_msg)


class CopyingHandler(webapp.RequestHandler):
    def post(self):
        current_user = users.get_current_user()

        if current_user:
            
            name = self.request.POST['birgun'];
            password = self.request.POST['birgpass'];
            cid = self.request.POST['birgcolid'];
            study_name = self.request.POST['gdRootCol'];
            
            c = collection.Collection()
            r = c.get_collection(cid,name,password)

            if r.status != 200:
                raise NoCollectionWithIDException('Failed to get the collection from BiRG')

            #email = 'glims.test@gmail.com' #raw_input('Google E-mail: ')
            #password = 'birglab1' #raw_input("Password: ") #getpass.getpass('Password: ') 
            #study_name = 'ANIT' #raw_input("Study name: ")

            # Assign the files to folders
            #helper = glims.Helper(email,password)
            
            helper = glims.Helper()
            potential_study_collections = helper.get_collections(study_name)

            if len(potential_study_collections) > 0:
                # Assume it is the one and only return (later this will have to be dynamic)
                study = glims.Study(helper,potential_study_collections[0]['entry'])
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
            self.redirect('https://%s/' % self.request.host)


class DownloadHandler(webapp.RequestHandler):

    @login_required
    def post(self):
        current_user = users.get_current_user()

        if current_user:
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
            self.redirect('https://%s/' % self.request.host)


class FileSendHandler(webapp.RequestHandler):

    @login_required
    def post(self):
        current_user = users.get_current_user()

        if current_user:
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
            self.redirect('https://%s/' % self.request.host)


class FrontendHandler(webapp.RequestHandler):

    @login_required
    def get(self):
        current_user = users.get_current_user()
        
        if current_user:
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
            self.redirect('https://%s/' % self.request.host)


# Based on Fetcher class from
# http://code.google.com/appengine/articles/python/retrieving_gdata_feeds.html
class MainHandler(webapp.RequestHandler):

    @login_required
    def get(self):
        """This handler is responsible for fetching an initial OAuth
        request token and redirecting the user to the approval page."""

        current_user = users.get_current_user()

        # We need to first get a unique token for the user to
        # promote.
        #
        # We provide the callback URL. This is where we want the
        # user to be sent after they have granted us
        # access. Sometimes, developers generate different URLs
        # based on the environment. You want to set this value to
        # "http://localhost:8080/step2" if you are running the
        # development server locally.
        #
        # We also provide the data scope(s). In general, we want
        # to limit the scope as much as possible. For this
        # example, we just ask for access to all feeds.
        scopes = SETTINGS['SCOPES']
        oauth_callback = 'https://%s/staging' % self.request.host
        consumer_key = SETTINGS['CONSUMER_KEY']
        consumer_secret = SETTINGS['CONSUMER_SECRET']
        request_token = gdocs.get_oauth_token(scopes, oauth_callback,
                                              consumer_key, consumer_secret)

        # Persist this token in the datastore.
        request_token_key = 'request_token_%s' % current_user.user_id()
        gdata.gauth.ae_save(request_token, request_token_key)

        # Generate the authorization URL.
        approval_page_url = request_token.generate_authorization_url()

        message = """<a href="%s">
Request token for the Google Documents Scope</a>"""
        self.response.out.write(message % approval_page_url)


# Based on RequestTokenCallback class from
# http://code.google.com/appengine/articles/python/retrieving_gdata_feeds.html
class OAuthStagingHandler(webapp.RequestHandler):

    @login_required
    def get(self):
        """When the user grants access, they are redirected back to this
        handler where their authorized request token is exchanged for a
        long-lived access token."""

        current_user = users.get_current_user()

        # Remember the token that we stashed? Let's get it back from
        # datastore now and adds information to allow it to become an
        # access token.
        request_token_key = 'request_token_%s' % current_user.user_id()
        request_token = gdata.gauth.ae_load(request_token_key)
        gdata.gauth.authorize_request_token(request_token, self.request.uri)

        # We can now upgrade our authorized token to a long-lived
        # access token by associating it with gdocs client, and
        # calling the get_access_token method.
        gdocs.auth_token = gdocs.get_access_token(request_token)

        # Note that we want to keep the access token around, as it
        # will be valid for all API calls in the future until a user
        # revokes our access. For example, it could be populated later
        # from reading from the datastore or some other persistence
        # mechanism.
        access_token_key = 'access_token_%s' % current_user.user_id()
        gdata.gauth.ae_save(request_token, access_token_key)

        # -- DCW: Redirect the user to the main menu.
        self.response.out.write("""<!DOCTYPE HTML>
<html>
    <head>
        <title>Google Authentication Complete</title>
        <meta http-equiv="refresh" content="5;url=/mainmenu" />
    </head>
    <body>
        <p>Authentication with Google servers was successful!<br />
            <a href="/mainmenu">Click this link if you are not redirected in 5 seconds.</a>
        </p>
    </body>
</html>
""")


class TransferHandler(webapp.RequestHandler):

    @login_required
    def post(self):
        current_user = users.get_current_user()

        if current_user:
            helper = glims.Helper()
            potential_studies = helper.get_studies()
            
            option_string = ""
            for one_study_name in potential_studies:
                option_string = option_string + '\n                <option>' + one_study_name + '</option>';
            
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
            <p>Google Data Study Name:</p>
            <div><select name="gdRootCol" size="5">""" + option_string + """
            </select></div>
            <div><input type="submit" value="Initiate Transfer"></div>
        </form>
    </body>
</html>
""")

        else:
            self.redirect('https://%s/' % self.request.host)


class UploadHandler(webapp.RequestHandler):

    @login_required
    def post(self):
        current_user = users.get_current_user()

        if current_user:
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
            self.redirect('https://%s/' % self.request.host)


def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/staging', OAuthStagingHandler),
                                          ('/mainmenu', FrontendHandler),
                                          ('/upload', UploadHandler),
                                          ('/download', DownloadHandler),
                                          ('/xfer', TransferHandler),
                                          ('/cpdata', CopyingHandler),
                                          ('/filesent', FileSendHandler)],
                                      debug=True)
    run_wsgi_app(application)


if __name__ == '__main__':
    main()
