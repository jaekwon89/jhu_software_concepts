from flask import Flask, render_template

app = Flask(__name__)

# Route for the homepage ('/')
@app.route('/')
def home():
    return render_template('index.html', active_page='home')

# Route for the contact page ('/contact')
@app.route('/contact')
def contact():
    return render_template('contact.html', active_page='contact')

# Route for the projects page ('/projects')
@app.route('/projects')
def projects():
    return render_template('projects.html', active_page='projects')


if __name__ == '__main__':
    # The app runs on localhost at port 8080, as required
    app.run(host='0.0.0.0', port=8080, debug=True)
