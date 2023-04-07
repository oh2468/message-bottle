# Message Bottle

## Description

A lighweight message board website, without external JS/CSS dependencies/bloat, where you can leave messages either publicly or encrypted with a password that are stored in a database for others to view. The messages are available for a specified duration, 1-28 days, after which they are ignored when using the site. The messages can then be deleted based on a desired way either manually or with the use of scheduling (The deletion process in not implemented, the process for it is very variable depending on use case, the functionality is however there).

## Getting Started

Download all the dependecies, then run the app from a terminal e.g.: ```python app.py``` and visit the website with your browser at -> localhost:8080

### Dependencies

* Python (developed with v. 3.10.5)
* SQLite3 (developed with v. 2.6.0)
* Bottle (developed with v. 0.12.23)
* cryptography (developed with v. 39.0.1)
