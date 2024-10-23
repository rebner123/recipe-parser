from flask import Flask, render_template, request, jsonify
from recipe_parser import parse_recipe_url  # Import your parser

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/parse', methods=['POST'])
def parse():
    url = request.form['recipe_url']
    try:
        recipe = parse_recipe_url(url)
        return render_template('index.html', recipe=recipe)
    except Exception as e:
        return render_template('index.html', error=str(e))

if __name__ == "__main__":
    app.run(debug=True)
