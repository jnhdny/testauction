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
cherrypy.config.update({'tools.sessions.on':True, 'tools.mako.collection_size' :500, 'tools.mako.directories':"templates",'server.socket_host': '0.0.0.0','server.socket_port': 8080,})

def http_methods_allowed(methods=['GET', 'HEAD']):
	method = cherrypy.request.method.upper()
	if method not in methods:
		cherrypy.response.headers['Allow'] = ", ".join(methods)
		raise cherrypy.HTTPError(405)

cherrypy.tools.allow = cherrypy.Tool('on_start_resource', http_methods_allowed)

def authorized():
	''' Redirects to login page if not logged on, else returns logged on user email'''
	email = cherrypy.session.get('email')
	isvalid = cherrypy.session.get('isvalid')
	token = cherrypy.session.get('token')
	if not email:
		raise cherrypy.HTTPRedirect("/signin")
	if not isvalid:
		raise cherrypy.HTTPRedirect("/validate")
	if not token:
		token = cherrypy.session["token"] = sample.id_generator(12)
	return email,token

class TestAuction:
	@cherrypy.expose
	@cherrypy.tools.mako(filename="testindex.html")
	def index(self):
		email,token = authorized()
		openauctions = sample.runQuery('''select id, dollars, close_date from x_auction where status=0''',())
		return {'email' : email, 'openauctions' : openauctions}
	

	@cherrypy.tools.allow(methods=['POST'])
	@cherrypy.expose
	def login(self,email,password):
		valid_status = sample.login(email,password)
		if valid_status == 1:
			cherrypy.session['email']=email
			cherrypy.session['isvalid'] = 1
			raise cherrypy.HTTPRedirect("/")
		if valid_status == 2:
			cherrypy.session['email'] = email
			cherrypy.session['isvalid'] = 0
			raise cherrypy.HTTPRedirect("/validate")
		else:
			return "Login failed"

#Logout, redirects to home page and to Login page
	#@cherrypy.tools.allow(methods=['POST'])
	@cherrypy.expose
	def logout(self,ctoken):
		if ctoken != cherrypy.session.get('token'):
			return "Security violation"
		cherrypy.session.clear()
		raise cherrypy.HTTPRedirect("/")
	
	@cherrypy.expose
	@cherrypy.tools.mako(filename="test.html")
	def signin(self):
		return {}

	@cherrypy.expose
	@cherrypy.tools.mako(filename="testauction.html")
	def auction (self,id=1):
		'''Auction page shows details of auction and allows bid if auction is open'''
		email,token = authorized()
		aa = sample.auctionDetails(id)
		if not aa:
			return {'email':email,'exists':0}
		return {'email':email, 'auction': aa, 'exists':1, 'token':token}

	@cherrypy.tools.allow(methods=['POST'])
	@cherrypy.expose
	def bid(self,id,amount,rate,ctoken):
		if ctoken != cherrypy.session.get('token'):
			return "Security breach"
		email,token = authorized()
		if sample.bid(email,id,amount,rate):
			raise cherrypy.HTTPRedirect("/auction/%s"%id)
		else:
			return '''<html>Bid unsuccessful<br><a href="/auction/%s">Return to Auction</a></html>'''%id
	
	@cherrypy.tools.mako(filename="testaccount.html")
	@cherrypy.expose
	def account(self):
		email,token=authorized()
		aa = sample.userDetails(email)
		return {'user':aa, 'token':token}
	
	@cherrypy.tools.allow(methods=['POST'])
	@cherrypy.expose
	def nairareload(self,amount,ctoken):
		'''Takes amount to add via POST. Also accepts negative numbers.'''
		if ctoken != cherrypy.session.get('token'):
			return "Security breach"
		email,token = authorized()
		if email != CBN_ACCOUNT and Decimal(amount) >= 0:
			sample.nairaReload(email,amount)
		raise cherrypy.HTTPRedirect("/account")
	
	@cherrypy.tools.allow(methods=['POST'])
	@cherrypy.expose
	def nairaremove(self,amount,ctoken):
		if ctoken != cherrypy.session.get('token'):
			return "Security breach"
		email,token = authorized()
		if email == CBN_ACCOUNT and Decimal(amount)>= 0:
			sample.nairaRemove(email,amount)
		raise cherrypy.HTTPRedirect("/account")
	
	@cherrypy.tools.allow(methods=['POST'])
	@cherrypy.expose
	def dollarreload(self,amount,ctoken):
		if ctoken != cherrypy.session.get('token'):
			return "Security breach"
		email,token=authorized()
		if email == CBN_ACCOUNT and Decimal(amount) >= 0:
			sample.dollarReload(email, amount)
		raise cherrypy.HTTPRedirect("/account")
	
	@cherrypy.tools.allow(methods=['POST'])
	@cherrypy.expose
	def dollarremove(self,amount,ctoken):
		if ctoken != cherrypy.session.get('token'):
			return "Security breach"
		email,token=authorized()
		if email != CBN_ACCOUNT and Decimal(amount) >=0:
			sample.dollarRemove(email,amount)
		raise cherrypy.HTTPRedirect("/account")
	
	@cherrypy.tools.mako(filename="testcreate.html")
	#@cherrypy.tools.mako(filename="createauction.html")
	@cherrypy.expose
	def createauction(self):
		email,token = authorized()
		return {'user': sample.userDetails(email), 'token':token}

	@cherrypy.tools.allow(methods=['POST'])
	@cherrypy.expose
	def create(self,amount,closedate,ctoken):
		if ctoken != cherrypy.session.get('token'):
			return "Security breach"
		if not cherrypy.session.get('email'):
			raise cherrypy.HTTPRedirect("/signin")
		sample.createAuction(amount,closedate)
		raise cherrypy.HTTPRedirect("/createauction")
		
	@cherrypy.tools.mako(filename="testsignup.html")
	@cherrypy.expose
	def signup(self):
		cherrypy.session["token"]=sample.id_generator(12)
		return {'token':token}


#Receives POST data!!!!
	@cherrypy.tools.allow(methods=['POST'])
	@cherrypy.expose
	def register(self,firstname,lastname,email,password,c_password,ctoken):
		if ctoken != cherrypy.session.get('token'):
			return "Security breach"
		if password == c_password:
		#Will eventually validate email here as well
			if sample.createUser(firstname,lastname,email,password):
				self.login(email,password)
				raise cherrypy.HTTPRedirect("/validate")
			else:
				return '''Account with this email exists'''
		else:
			return "User account creation failed"
	
	@cherrypy.tools.mako(filename="testpast.html")
	@cherrypy.expose
	def past(self):
		email,token=authorized()
		oldauctions = sample.oldAuctions()
		return {'email':email, 'oldauctions':oldauctions, 'token':token}


#Receives POST data!!!!
	@cherrypy.tools.allow(methods=['POST'])
	@cherrypy.expose
	def xvalidate(self,validcode,ctoken):
		if ctoken != cherrypy.session.get('token'):
			return "Security breach"
		if cherrypy.session.get('email'):
			email = cherrypy.session.get('email')
			if not sample.validate(email,validcode):
				return "Invalid validation code"
			else:
				cherrypy.session['isvalid'] = 1
				raise cherrypy.HTTPRedirect("/")
		else:
			raise cherrypy.HTTPRedirect("/")
	
	@cherrypy.expose
	def emailvalidate(self,email,code):
		if email == cherrypy.session.get('email'):
			if not sample.validate(email,code):
				return "Invalid validation code"
			else:
				return '''Validation successful. Click <a href="/signin">here</a> to sign in.'''
		else:
			raise cherrypy.HTTPRedirect("/signin")

#Has a Form!!!!!	
	@cherrypy.tools.mako(filename="validate.html")
	@cherrypy.expose	
	def validate(self):
		email = cherrypy.session.get('email')
		isvalid = cherrypy.session.get('isvalid')
		return {'email':email,'isvalid':isvalid, 'token':token}

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