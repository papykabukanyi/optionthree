from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
@app.route('/index.html')
def home():
    return render_template('index.html')

@app.route("/services")
@app.route("/services.html")
def services():
    return render_template("services.html")

@app.route("/contact")
@app.route("/contact.html")
def contact():
    return render_template("contact.html")

@app.route("/blog")
@app.route("/blog.html")
def blog():
    return render_template("blog.html")

@app.route("/blogs")
@app.route("/blogs.html")
def blogs():
    return render_template("blogs.html")

@app.route("/about")
@app.route("/about.html")
def about():
    return render_template("about.html")

if __name__ == '__main__':
    app.run(debug=True)
