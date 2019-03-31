# pyenv
Provides persistent environment for Python 3 scripts

# Introduction

You have a host python environment `pyenv.host` for your code. 
You execute in it and the side-effects of your code will persist on that environtment.      
This is helpful when you are loading big files, which you definitely would not like to wait for it each time you start your script.

+ How to start the host environment
```
python3.6 -m pyenv.host
```
+ How to send your code to the host environment
```
python3.6 -m pyenv.client -c "pyenv.set('shit', 'happens')"

python3.6 -m pyenv.client -c "print(pyenv.keys())"
dict_keys(['shit'])

python3.6 -m pyenv.client -c "pyenv.get('shit')"
happens
```
