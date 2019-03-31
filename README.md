# pyenv
Provides persistent environment for Python 3 scripts

# Installation

```
python3.6 -m pip install py_env
```
Or
```
git clone https://github.com/hanayashiki/pyenv.git
cd pyenv
python3.6 setup.py install
```

# Introduction

You have a host python environment `py_env.host` for your code.
You execute in it and the side-effects of your code will persist on that environtment.      
This is helpful when you are loading big files, which you definitely would not like to wait for it each time you start your script.

+ How to start the host environment
```
python3.6 -m py_env.host
```
+ How to send your code to the host environment
```
python3.6 -m py_env.client -c "py_env.set('shit', 'happens')"

python3.6 -m py_env.client -c "print(py_env.keys())"
dict_keys(['shit'])

python3.6 -m py_env.client -c "py_env.get('shit')"
happens
```
