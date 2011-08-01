#!/usr/bin/env python
# Based on Google's official Python documentation
import cgi
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

class MainHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()

        if user:
            self.response.out.write("""<!DOCTYPE HTML>
<html>
    <body>
        <form action="/upload" method="post">
            <div><input type="submit" value="Upload the Selected File"></div>
        </form>
        <form action="/download" method="post">
            <div><input type="submit" value="Download a File"></div>
        </form>
    </body>
</html>
""")
        else:
            self.redirect(users.create_login_url(self.request.uri))

class DownloadHandler(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()

        if user:
            self.response.out.write("""<!DOCTYPE HTML>
<html>
    <body>
        <a href="">Your file is ready.</a>
    </body>
</html>
""")
        else:
            self.redirect(users.create_login_url(self.request.uri))

class UploadHandler(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()

        if user:
            self.response.out.write("""<!DOCTYPE HTML>
<html>
    <body>
        <p>Your file is uploaded.</p>
    </body>
</html>
""")
        else:
            self.redirect(users.create_login_url(self.request.uri))

def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/upload', UploadHandler),
                                          ('/download', DownloadHandler)],
                                      debug=True)
    run_wsgi_app(application)


if __name__ == '__main__':
    main()
