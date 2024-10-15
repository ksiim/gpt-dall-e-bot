# ChatGPT + Dall-E bot

# commands
to start:
~~~
poetry init
~~~
then press enter a lot
then you need to enter command:
~~~
poetry shell
~~~
then to run your script:
~~~
python main.py
~~~
there we go

# command to generate requirements.txt from poetry:
~~~
poetry export --without-hashes --without-urls | awk '{ print $1 }' FS=';' > requirements.txt
~~~

# custom commands
to add new module in poetry:
~~~
poetry add 
~~~
and write module name after add
** you may write module names with space, for example:
```
poetry add aiogram sqlalchemy fastapi
```

to delete module in poetry:
~~~
poetry remove
~~~
and write module name after remove
