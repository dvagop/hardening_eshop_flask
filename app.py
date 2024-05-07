from flask import Flask, render_template, jsonify

app = Flask(__name__)

JOBS = [
    {
        'id': 1,
        'title': 'Brotherhood of Steel',
        'location': 'The Hidden Valley',
        'salary': 'Euro. 1,000'
    },

    {
        'id': 2,
        'title': 'Vault Dweller',
        'location': 'The Vault',
        'salary': 'Euro. 10,000'
    },

    {   'id': 3,
        'title': 'The Ghoul',
        'location': 'The Wasteland',
        'salary': 'Euro. 100'
        
    },

    {    'id': 4,
         'title': 'The Rebel',
         'location': 'New California Republic',
         
    }
]

@app.route("/")
def index():
    return render_template('home.html', jobs=JOBS, owner='Fallout')

@app.route("/api/jobs")
def list_jobs():
    return jsonify(JOBS)

if __name__=="__main__":
    app.run(host='0.0.0.0', debug=True)
