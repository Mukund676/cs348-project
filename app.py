from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# This prepares you for the SQL requirements in Stage 2/3
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.db'
#db = SQLAlchemy(app)

@app.route('/')
def hello_world():
    # This meets the 'hello world' page requirement
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)