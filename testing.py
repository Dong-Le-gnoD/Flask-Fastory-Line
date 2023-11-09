from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Create a list of multiple-choice options
options = ["Option A", "Option B", "Option C", "Option D", "Option E", "Option F", "Option G", "Option H", "Option I"]

# Create a history list to store selected options
history = []

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        selected_choices = request.form.getlist('choices')
        history.insert(0, selected_choices)
    return render_template('index.html', options=options, history=history)

@app.route('/clear_history')
def clear_history():
    # Create a new route and function to clear the history and redirect to the index
    history.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
