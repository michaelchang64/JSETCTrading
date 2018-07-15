#!/usr/bin/python

# ~~~~~==============   HOW TO RUN   ==============~~~~~
# 1) Configure things in CONFIGURATION section
# 2) Change permissions: chmod +x bot.py
# 3) Run in loop: while true; do ./bot.py; sleep 1; done

from __future__ import print_function

import sys
import socket
import json
import math

# ~~~~~============== CONFIGURATION  ==============~~~~~
# replace REPLACEME with your team name!
team_name="TEAMORANGE"
# This variable dictates whether or not the bot is connecting to the prod
# or test exchange. Be careful with this switch!
test_mode = False

# This setting changes which test exchange is connected to.
# 0 is prod-like
# 1 is slower
# 2 is empty
test_exchange_index=1
prod_exchange_hostname="production"

port=25000 + (test_exchange_index if test_mode else 0)
exchange_hostname = "test-exch-" + team_name if test_mode else prod_exchange_hostname

# ~~~~~============== NETWORKING CODE ==============~~~~~
def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((exchange_hostname, port))
    return s.makefile('rw', 1)

def write_to_exchange(exchange, obj):
    json.dump(obj, exchange)
    exchange.write("\n")

def read_from_exchange(exchange):
    return json.loads(exchange.readline())

# ~~~~~============== MAIN LOOP AND FUNCTIONS  ==============~~~~~
def get_hello_stocks(msg):
    shares = {"AAPL": {"num": 0, "minsell": -1, "maxbuy": -1}, "BOND": {"num": 0, "minsell": -1, "maxbuy": -1}, "GOOG": {"num": 0, "minsell": -1, "maxbuy": -1}, "MSFT": {"num": 0, "minsell": -1, "maxbuy": -1}}  # order is AAPL 0, BOND 3, GOOG 4, MSFT 5
    if(msg["type"] == "hello"):
        shares["AAPL"]["num"] = msg["symbols"][0]["position"]
        shares["BOND"]["num"] = msg["symbols"][3]["position"]
        shares["GOOG"]["num"] = msg["symbols"][4]["position"]
        shares["MSFT"]["num"] = msg["symbols"][5]["position"]
    return shares

def absdiff(a, b):
    return abs(a - b)

def no_negatives(shares):
    if(shares["AAPL"]["minsell"] == -1 or shares["BOND"]["minsell"] == -1 or shares["GOOG"]["minsell"] == -1 or shares["MSFT"]["minsell"] == -1 or shares["AAPL"]["maxbuy"] == -1 or shares["BOND"]["maxbuy"] == -1 or shares["GOOG"]["maxbuy"] == -1 or shares["MSFT"]["maxbuy"] == -1):
        return True
    else:
        return False

def main():
    i = 100
    opShares = 0 # Shares to operate on
    companies = ["AAPL", "BOND", "GOOG", "MSFT"]
    company = ""

    exchange = connect()

    write_to_exchange(exchange, {"type": "hello", "team": team_name.upper()})
    msg = read_from_exchange(exchange)
    print("\n", msg, "\n")

    shares = get_hello_stocks(msg)
    print(shares)

    print("AAPL shares: ", shares["AAPL"]["num"], "\n")
    print("BOND shares: ", shares["BOND"]["num"], "\n")
    print("GOOG shares: ", shares["GOOG"]["num"], "\n")
    print("MSFT shares: ", shares["MSFT"]["num"], "\n")


    while(no_negatives(shares)):
        msg = read_from_exchange(exchange)
        if(msg["type"] == "book"):
            for k in range(0, 4):
                if(msg["symbol"] == companies[k]):
                    buyarr = []
                    sellarr = []
                    for price, stock in msg["buy"]:
                        buyarr.append(price)
                    shares[companies[k]]["maxbuy"] = max(buyarr)
                    print("initial maxbuy for ", companies[k], ": ", shares[companies[k]]["maxbuy"])
                    for price, stock in msg["sell"]:
                        sellarr.append(price)
                    shares[companies[k]]["minsell"] = min(sellarr)
                    print("initial minsell for ", companies[k], ": ", shares[companies[k]]["minsell"])
                    print(shares)
                    print("\nentered through book cond\n")
        else:
            print("missed the book")

    differences = {"AAPL": absdiff(shares["AAPL"]["minsell"], shares["AAPL"]["maxbuy"]), "BOND": absdiff(shares["BOND"]["minsell"], shares["BOND"]["maxbuy"]), "GOOG": absdiff(shares["GOOG"]["minsell"], shares["GOOG"]["maxbuy"]), "MSFT": absdiff(shares["MSFT"]["minsell"], shares["MSFT"]["maxbuy"])}
    sorteddifferences = sorted(differences.items(), key=lambda kv: kv[1])
    company = sorteddifferences[3][0]
    print("the company winner is: ", company, "\n")
    print(shares)

    opShares = shares[company]["num"]
    maxbuy = shares[company]["maxbuy"]
    minsell = shares[company]["minsell"]

    try:
        if(opShares < 0): # to make opShares == 0 makes for massive shorting lmao
            write_to_exchange(exchange, {"type": "add", "order_id": i, "symbol": company, "dir": "BUY", "price": minsell, "size": 10})
            print("maxbuy = ", maxbuy)
            opShares += 10
            i += 1
            print("\nentered through buy cond\n")
        else:
            write_to_exchange(exchange, {"type": "add", "order_id": i, "symbol": company, "dir": "SELL", "price": maxbuy, "size": 10})
            print("minsell = ", minsell)
            opShares -= 10
            i += 1
            print("\nentered through buy/sell cond\n")
    except:
        pass

    # A common mistake people make is to call write_to_exchange() > 1
    # time for every read_from_exchange() response.
    # Since many write messages generate marketdata, this will cause an
    # exponential explosion in pending messages. Please, don't do that
if __name__ == "__main__":
    main()
