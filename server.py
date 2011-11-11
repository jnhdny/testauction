import cherrypy,os.path
import sample
from mako.lookup import TemplateLookup
from decimal import *
current_dir = os.path.dirname(os.path.abspath(__file__))
CBN_ACCOUNT = "cbngov@cbn.gov"

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
    @cherrypy.tools.mako(filename="testindex.html")
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
    #@cherrypy.tools.mako(filename="login.html")
    @cherrypy.tools.mako(filename="test.html")
    def signin(self):
        return {}

    @cherrypy.expose
    @cherrypy.tools.mako(filename="testauction.html")
    def auction (self,id):
        '''Auction page shows details of auction and allows bid if auction is open'''
        email = authorized()
        aa = sample.auctionDetails(id)
        if not aa:
            return {'email':email,'exists':0}
        return {'email':email, 'auction': aa, 'exists':1}

    @cherrypy.expose
    def bid(self,id,amount,rate):
        email = authorized()
        if sample.bid(email,id,amount,rate):
            raise cherrypy.HTTPRedirect("/auction/%s"%id)
        else:
            return '''<html>Bid unsuccessful<br><a href="/auction/%s">Return to Auction</a></html>'''%id
    
    @cherrypy.tools.mako(filename="testaccount.html")
    @cherrypy.expose
    def account(self):
        email=authorized()
        aa = sample.userDetails(email)
        return {'user':aa}
	
    @cherrypy.tools.mako(filename="nairareload.html")
    @cherrypy.expose
    def refill(self):
        email = authorized()
        return {'email':email}
    
    @cherrypy.expose
    def nairareload(self,amount):
        '''Takes amount to add via POST. Also accepts negative numbers.'''
        email = authorized()
        if email != CBN_ACCOUNT and Decimal(amount) >= 0:
        	sample.nairaReload(email,amount)
        raise cherrypy.HTTPRedirect("/account")
    
    @cherrypy.expose
    def nairaremove(self,amount):
        email = authorized()
        if email == CBN_ACCOUNT and Decimal(amount)>= 0:
        	sample.nairaReload(email,-amount)
        raise cherrypy.HTTPRedirect("/account")
    
    @cherrypy.expose
    def dollarreload(self,amount):
        email=authorized()
        if email == CBN_ACCOUNT and Decimal(amount) >= 0:
            sample.dollarReload(email, amount)
        raise cherrypy.HTTPRedirect("/account")
    
    @cherrypy.expose
    def dollarremove(self,amount):
        email=authorized()
        if email != CBN_ACCOUNT and Decimal(amount) >=0:
            sample.dollarReload(email,-amount)
        raise cherrypy.HTTPRedirect("/account")
    
    @cherrypy.tools.mako(filename="testcreate.html")
    #@cherrypy.tools.mako(filename="createauction.html")
    @cherrypy.expose
    def createauction(self):
        email = authorized()
        return {'user': sample.userDetails(email)}

    @cherrypy.expose
    def create(self,amount,closedate):
        if not cherrypy.session.get('email'):
            raise cherrypy.HTTPRedirect("/signin")
        sample.createAuction(amount,closedate)
        raise cherrypy.HTTPRedirect("/createauction")
        
    @cherrypy.tools.mako(filename="testsignup.html")
    @cherrypy.expose
    def signup(self):
        return {}
    
    @cherrypy.expose
    def register(self,firstname,lastname,email,password,c_password):
    	if password == c_password:
    	#Will eventually validate email here as well
    	    if sample.createUser(firstname,lastname,email,password):
    	        self.login(email,password)
    	        raise cherrypy.HTTPRedirect("/")
    	    else:
    	        return '''Account with this email exists'''
    	else:
    	    return "User account creation failed"
    
    @cherrypy.tools.mako(filename="testpast.html")
    @cherrypy.expose
    def past(self):
        email=authorized()
        oldauctions = sample.oldAuctions()
        return {'email':email, 'oldauctions':oldauctions}



def defaulterror(status, message, traceback, version):
    return "An Error has occurred"
cherrypy.config.update({'error_page.default': defaulterror})

tconf = {'/':
	{'tools.staticdir.root':current_dir
	},
	'/static':{'tools.staticdir.on': True, 'tools.staticdir.dir': 'static'}
}
cherrypy.tree.mount(TestAuction(), "/", tconf)
cherrypy.engine.start()
cherrypy.engine.block()
#cherrypy.quickstart(TestAuction())

