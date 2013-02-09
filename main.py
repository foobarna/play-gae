from blog import *

class MainPage(webapp2.RequestHandler):
	def get(self):
		self.response.out.write("Hello ma'friend!")
		self.response.out.write("""<br><a href="/blog">Blog</a>""")
		self.response.out.write("""<br><a href="/rot13">Rot13</a>""")


class Rot13Handler(BaseHandler):
	def render_str2(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def rot13(self, text=""):
		new_text = ""
		for c in text:
			ascii = ord(c);
			if (ascii >= 65 and ascii <= 90):
				ascii += 13
				if ascii > 90: ascii = 64 + ascii - 90
			if (ascii >= 97 and ascii <= 122):
				ascii += 13
				if ascii > 122: ascii = 96 + ascii - 122
			new_text = new_text + chr(ascii)
		return new_text

	def get(self):
		self.render('rot13-form.html')

	def post(self):
		rot13 = ""
		text1 = self.request.get("text")
		if text1:
			rot13 = self.rot13(text1)
		self.render('rot13-form.html', text = rot13 )



app = webapp2.WSGIApplication([('/', MainPage),
								("/blog", BlogFront),
								("/blog/([0-9]+)", BlogPost),
								("/blog/newpost", BlogNewPost),
								("/blog/signup", BlogSignup),
								("/blog/login", BlogLogin),
								("/blog/logout", BlogLogout),
								("/blog/welcome", BlogWelcome),
								("/rot13", Rot13Handler)],
								debug=True)
