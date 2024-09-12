# 🤖 AI Product Hack - Case  #12
___

## 🛠️ Installing the requirements
```
apt install make
python3 -m venv venv
. ./venv/bin/activate
pip install -r requirements.txt
```

## 🔑 Sample for .env file
```
APP_TITLE=case-12
APP_HOST=0.0.0.0
APP_PORT=8888
APP_ORIGINS=["*"]

TRANSLATOR_KEY=
TRANSLATOR_ID=
TRANSLATOR_FOLDER=
```
## ⭐️ Run the app
1. Before running you should install requirements and create filled `.env` file in the root directory.
2. Activate virtual environment using
```
. ./venv/bin/activate
```
3. Run `src/main.py`:
```
python3 -m src.main
```
Or via `make` util:
```
make run
```
