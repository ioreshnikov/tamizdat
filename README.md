Tamizdat
========

_Tamizdat refers to literature published abroad (там, tam, "there"),
often from smuggled manuscripts._

_[Wikipedia](https://en.wikipedia.org/wiki/Samizdat)_

Tamizdat is a telegram bot that allows you to search `flibusta.net`
library and to deliver the books you want from there to an email
address of your choice. The main use-case for that is to send the
books from the library to your Kindle device via an Amazon email
address.

Installation
------------

Please clone the repository first. In order to install the bot from source you need to update the settings stored inside `tamizdat/settings.py` and then use

    $ pip install .

from the project root to set up the environment and put the binary inside your search path.

Running the bot
---------------

To run the bot you first need to import the website catalog. You can get it at http://flibusta.is/catalog/catalog.zip. To import it you need to download it and extract it, for example with the help of the following commands

    $ wget http://flibusta.is/catalog/catalog.zip
    $ unzip catalog.zip

This will create a 60 megabyte text file called `catalog.txt` in you working directory. To import it simply run `tamizdat import catalog.txt`. The command will parse the catalog and put all the library information into an sqlite3 database with a search index of the library cards. You are now ready to start the bot. Simply launch

    $ tamizdat bot

and you are done.

Supported commands
------------------

Currently, the bot supports the following list of commands:

* **settings** -- Show the profile settings
* **setextension** -- Set preferred ebook extension
* **setemail** -- Set your email address
* **info** *000000* -- Show the book info given the id
* **download** *000000* -- Download the ebook
* **email** *000000* -- Send the ebook via email
