import cherrypy
import sample
from mako.lookup import TemplateLookup

class MakoHandler(cherrypy.dispatch.LateParamPageHandler):
    """Callable which sets response.body."""
    
    def __init__(self, template, next_handler):
        self.template = template
        self.next_handler = next_handler
    
    def __call__(self):
        env = globals().copy()
        env.update(self.next_handler())
        return self.template.render(**env)

class MakoLoader(object):
    
    def __init__(self):
        self.lookups = {}
    
    def __call__(self, filename, directories, module_directory=None,
                 collection_size=-1):
        # Find the appropriate template lookup.
        key = (tuple(directories), module_directory)
        try:
            lookup = self.lookups[key]
        except KeyError:
            lookup = TemplateLookup(directories=directories,
                                    module_directory=module_directory,
                                    collection_size=collection_size,
                                    )
            self.lookups[key] = lookup
        cherrypy.request.lookup = lookup
        
        # Replace the current handler.
        cherrypy.request.template = t = lookup.get_template(filename)
        cherrypy.request.handler = MakoHandler(t, cherrypy.request.handler)

main = MakoLoader()
cherrypy.tools.mako = cherrypy.Tool('on_start_resource', main)

cherrypy.config.update({'tools.sessions.on':True, 'tools.mako.collection_size' :500, 'tools.mako.directories':"templates"})

def authorized():
    ''' Redirects to login page if not logged on, else returns logged on user email'''
    email = cherrypy.session.get('email')
    if not email:
        raise cherrypy.HTTPRedirect("/signin")
    return email

class TestAuction:
    @cherrypy.expose
    @cherrypy.tools.mako(filename="index.html")
    def index(self):
        email = authorized()
        openauctions = sample.runQuery('''select id, dollars, close_date from x_auction where status=0''',())
        return {'email' : email, 'openauctions' : openauctions}
    
#Login POST function
    @cherrypy.expose
    def login(self,email,password):
        d = cherrypy.request.headers
        if sample.login(email,password):
            cherrypy.session['email']=email
            raise cherrypy.HTTPRedirect("/")
        else:
            return "Login failed"

#Logout, redirects to home page and to Login page
    @cherrypy.expose
    def logout(self):
        cherrypy.session.delete()
        raise cherrypy.HTTPRedirect("/")

#Login page    
    @cherrypy.expose
    @cherrypy.tools.mako(filename="login.html")
    def signin(self):
        return {}

    @cherrypy.expose
    @cherrypy.tools.mako(filename="auction.html")
    def auction (self,id):
        '''Auction page shows details of auction and allows bid if auction is open'''
        email = authorized()
        aa = sample.auctionDetails(id)
        return {'email':email, 'auction': aa}

    @cherrypy.expose
    def bid(self,id,amount,rate):
        email = authorized()
        if sample.bid(email,id,amount,rate):
            raise cherrypy.HTTPRedirect("/auction/%s"%id)
        else:
            return '''<html>Bid unsuccessful<br><a href="/auction/%s">Return to Auction</a></html>'''%id
    
    @cherrypy.expose
    def account(self):
        if not cherrypy.session.get('email'):
            raise cherrypy.HTTPRedirect("/signin")
        email=cherrypy.session.get('email')
        aa = sample.userDetails(email)
        return '''<html>
<head>
<title>Your Account</title>
</head>
<body style="font-family: verdana, arial, sans-serif;">
<h3>Open Bids</h2>
<p>
</p>
<h3>Wallet</h3>
<table>
<tr>
<td>Naira:</td>
<td>%s<td>
<td><a href="/refill">Refill</a></td>
</tr>
<tr>
<td>Dollars</td>
<td>%s<td>
<td><a href="./#">Withdraw</a></td>
</tr>
<tr>
<td>Available naira:</td>
<td>%s<td>
<td></td>
</tr>
</table>
<p>Logged in as <a href="/account">%s</a> <a href="/logout">Logout</a></p>
</body>
</html>'''% (aa["nairabalance"], aa["dollarbalance"], aa["availablenaira"],email)

    @cherrypy.expose
    def refill(self):
        if not cherrypy.session.get('email'):
            raise cherrypy.HTTPRedirect("/signin")
        return '''<html>
<head>
<title>Reload Naira</title>
</head>
<body style="font-family: verdana, arial, sans-serif;">
<p>
<form method="POST" action="http://127.0.0.1:8080/nairareload">
<p>
Amount: <input  type="text" name="amount" size="20" /> <br>
<input type="submit" value="Reload" />
</p>
</form>
<p>Logged in as <a href="/account">%s</a> <a href="/logout">Logout</a></p>
</body>
</html>'''
    
    @cherrypy.expose
    def nairareload(self,amount):
        '''Takes amount to add via POST. Also accepts negative numbers.'''
        email = authorized()
        sample.nairaReload(email,amount)
        raise cherrypy.HTTPRedirect("/account")
    
    @cherrypy.expose
    def createauction(self):
        if not cherrypy.session.get('email'):
            raise cherrypy.HTTPRedirect("/signin")
        email=cherrypy.session.get('email')
        return'''<html>
<body>
<h2>Create Auction</h2>
<form method="POST" action="/create">
  <p>Dollars on sale: <input type="text" name="amount"></p>
  <p>Auction ends at: <input type="datetime" name="closedate"></p>
  <input type="submit" value="Create">
</form>
<p>Logged in as <a href="/account">%s</a> <a href="/logout">Logout</a></p>
</body>
</html>'''%(email,)

    @cherrypy.expose
    def create(self,amount,closedate):
        if not cherrypy.session.get('email'):
            raise cherrypy.HTTPRedirect("/signin")
        sample.createAuction(amount,closedate)
        raise cherrypy.HTTPRedirect("/")
 
cherrypy.quickstart(TestAuction())

