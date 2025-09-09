# run.py
from module_1 import create_app

app = create_app()

if __name__ == "__main__":
    # The app runs on localhost at port 8080, as required
    app.run(host="0.0.0.0", port=8080, debug=True)