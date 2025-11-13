# How to run this project:

0. If no virtual environment is created, create one first
```bash
cd path/to/your/project
python -m venv <VENV_NAME>
```
Note: In the following case, the venv is named "venv"  
1. Activate the virtual environment
```bash
source venv/bin/activate
```
2. Install the requirements
```python
pip install -r requirements.txt
```
3. Run the server using manage.py
```python
python manage.py runserver
```

# How to build React Frontend
```js
cd path/to/your/react-project
npm run build
```

# How to push all changes made to Git Repo
```bash
git add .
git commit -m "COMMIT_MESSAGE"
GIT_SSL_NO_VERIFY=true git push -u origin <YOUR_BRANCH>
```

# Other requirements to be manually added
1. Add the following entry to your .env file, since this file is not being tracked by GIT
```bash
# Fernet Key
FERNET_KEY=dzi31zMj3HqfNuHYW2a8rU8g66Ahtzno-Lc6BZweTpg=
```