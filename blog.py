import re
import jinja2
import os
import webapp2
import cgi
import hashlib
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
								autoescape = True)

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{6,20}$")
EMAIL_RE = re.compile(r'^[\S]+@[\S]+\.[\S]+$')

def hash_str(s):
	return hashlib.md5(s).hexdigest()

def make_secure_val(s):
	return "%s|%s" %(s,hash_str(s))

def check_secure_val(h):
	val = h.split("|")[0]
	if h == make_secure_val(val):
		return val

def blog_key(name = "default"):
	return db.Key.from_path("blogs", name)

def escape_html(s):
	return cgi.escape(s, quote = True)

def valid_username(username):
	return username and USER_RE.match(username)

def valid_email(email):
	return not email or EMAIL_RE.match(email)

def valid_password(password):
	return password and PASS_RE.match(password)

def render_str(template, **params):
	t = jinja_env.get_template(template)
	return t.render(params)

class BaseHandler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		return render_str(template, **params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

	def user_id(self):
		cookie = self.request.cookies.get("user_id")
		if cookie:
			user_id = check_secure_val(cookie)
			return user_id

	def get_user(self):
		user_id = self.user_id()
		if user_id:
			return User.get_by_id(int(user_id))


class Post(db.Model):
	subject = db.StringProperty(required = True)
	content = db.TextProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)
	last_modified = db.DateTimeProperty(auto_now_add = True)

	def render(self):
		self._render_text = self.content.replace("\n", "<br>")
		return render_str("blog_post.html", p = self)


class User(db.Model):
	username = db.StringProperty(required = True)
	password = db.StringProperty(required = True)
	email = db.StringProperty(required = False)


class BlogSignup(BaseHandler):
	def get(self):
		user = self.get_user()
		if not user:
			self.render("blog_signup.html")
		else:
			self.redirect("/blog/welcome")

	def post(self):
		have_error = False
		username = self.request.get("username")
		password = self.request.get("password")
		verify = self.request.get("verify")
		email = self.request.get("email")
		params = dict(username = username, email = email)
		if not valid_username(username):
			params["error_username"] = "Not a valid username!"
			have_error = True
		if not valid_password(password):
			params["error_password"] = "Not a valid password!"
			have_error = True
		elif password != verify:
			params["error_verify"] = "Passwords don't match!"
			have_error = True
		if not valid_email(email):
			params["error_email"] = "Not a valid e-mail!"
			have_error = True
		if have_error:
			self.render('blog_signup.html', **params)
		else:
			password = hash_str(password)
			user = User(username = username, password = password, email = email)
			user.put()
			user_id = user.key().id()
			sec_val = make_secure_val(str(user_id))
			self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % sec_val)
			self.redirect('/blog/welcome')


class BlogLogin(BaseHandler):
	def get(self):
		user = self.get_user()
		if not user:
			self.render("blog_login.html")
		else:
			self.redirect("/blog/welcome")

	def post(self):
		username = self.request.get("username")
		password = self.request.get("password")
		if password and username:
			password = hash_str(password)
		else:
			self.redirect("blog_login.html", username = username, error = "User or Pass can't be empty!")
			return
		users = db.GqlQuery("select * from User where username=:1 limit 1",username)
		user = users.get()
		if user and user.password:
			user_id = user.key().id()
			sec_val = make_secure_val(str(user_id))
			self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % sec_val)
			self.redirect('/blog/welcome')
		else:
			self.render("blog_login.html", username = username, error = "User and Pass dosen't match!")
			return


class BlogLogout(BaseHandler):
	def get(self):
		self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')
		self.redirect('/blog/signup')


class WelcomeHandler(BaseHandler):
	def get(self):
		user = self.get_user();
		if user:
			self.render('blog_welcome.html', username = user.username, user = user)
		else:
			self.redirect('/blog/signup')
			return


class BlogFront(BaseHandler):
	def get(self):
		posts = db.GqlQuery("select * from Post order by created desc limit 10")
		user = self.get_user()
		if user:
			self.render("blog_front.html", posts = posts, user = user)
		else:
			self.render("blog_front.html", posts = posts)


class BlogNewPost(BaseHandler):
	def get(self):
		user = self.get_user()
		if user:
			self.render("blog_newpost.html",user = user)
		else:
			self.redirect("/blog/login")

	def post(self):
		subject = self.request.get("subject")
		content = self.request.get("content")
		error = ""

		if not (subject and content):
			error = "You need a Subject and a Content!"
			self.render("blog_newpost.html", subject = subject, content = content, error = error)
		else:
			post = Post(subject = subject, content = content)
			post.put()
			self.redirect("/blog/%s" % str(post.key().id()))


class BlogPost(BaseHandler):
	def get(self, post_id):
		post = Post.get_by_id(int(post_id))
		if not post:
			self.redirect("/blog/newpost")
			return
		user = self.get_user()
		if user:
			self.render("blog_permalink.html", post = post, user = user)
		else:
			self.render("blog_permalink.html", post = post)
