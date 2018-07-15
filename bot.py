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
test_mode = True

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
    shares = {"AAPL": {"num": 0, "minsell": -1, "maxbuy": -1}, "GOOG": {"num": 0, "minsell": -1, "maxbuy": -1}, "MSFT": {"num": 0, "minsell": -1, "maxbuy": -1}}  # order is AAPL 0, GOOG 4, MSFT 5
    if(msg["type"] == "hello"):
        shares["AAPL"]["num"] = msg["symbols"][0]["position"]
        shares["GOOG"]["num"] = msg["symbols"][4]["position"]
        shares["MSFT"]["num"] = msg["symbols"][5]["position"]
    return shares

def absdiff(a, b):
    return abs(a - b)

def main():
    i = 0
    opShares = 0 # Shares to operate on
    companies = ["AAPL", "GOOG", "MSFT"]
    company = ""

    exchange = connect()

    print(write_to_exchange(exchange, {"type": "hello", "team": team_name.upper()}))
    for j in range(0, 11):
        print("The exchange replied:", read_from_exchange(exchange), file=sys.stderr)

    msg = read_from_exchange(exchange)

    shares = get_hello_stocks(msg)
    print(shares)

    print("AAPL shares: ", shares["AAPL"]["num"], "\n")
    print("GOOG shares: ", shares["GOOG"]["num"], "\n")
    print("MSFT shares: ", shares["MSFT"]["num"], "\n")

    while(i < 30):
        for y in range(0, 3):
            if(msg["type"] == "book"):
                for k in range(0, 2):
                    if(msg["symbol"] == companies[k]):
                        buyarr = []
                        sellarr = []
                        for price, stock in msg["buy"]:
                            buyarr.append(price)
                        shares[companies[k]]["maxbuy"] = max(buyarr)
                        print("initial maxbuy for ", companies[k], ": ", shares[companies[k]]["maxbuy"])
                        for price, stock in msg["sell"]:
                            sellarr.append(price)
                        shares[companies[k]]["minsell"] = min(sellarr) - 1
                        print("initial minsell for ", companies[k], ": ", shares[companies[k]]["minsell"])
                        print(shares)
            else:
                print("missed the book")

        differences = {"AAPL": absdiff(shares["AAPL"]["minsell"], shares["AAPL"]["maxbuy"]), "GOOG": absdiff(shares["GOOG"]["minsell"], shares["GOOG"]["maxbuy"]), "MSFT": absdiff(shares["MSFT"]["minsell"], shares["MSFT"]["maxbuy"])}
        sorteddifferences = sorted(differences.items(), key=lambda kv: kv[1])
        company = sorteddifferences[2][0]
        print("the company winner is: ", company, "\n")
        print(shares)

        maxbuy = shares[company]["maxbuy"]
        minsell = shares[company]["minsell"]

        if(opShares < 1):
            print(write_to_exchange(exchange, {"type": "add", "order_id": i, "symbol": company, "dir": "BUY", "price": maxbuy, "size": 1}))
            print("maxbuy = ", maxbuy)
            print("The exchange replied:", read_from_exchange(exchange), file=sys.stderr)
            print("The exchange replied:", read_from_exchange(exchange), file=sys.stderr)
            opShares += 1
            i += 1
        else:
            print(write_to_exchange(exchange, {"type": "add", "order_id": i, "symbol": company, "dir": "BUY", "price": maxbuy, "size": 1}))
            print("maxbuy = ", maxbuy)
            print("The exchange replied:", read_from_exchange(exchange), file=sys.stderr)
            print("The exchange replied:", read_from_exchange(exchange), file=sys.stderr)
            print("The exchange replied:", read_from_exchange(exchange), file=sys.stderr)
            opShares -= 1
            i += 1
            print(write_to_exchange(exchange, {"type": "add", "order_id": i, "symbol": company, "dir": "SELL", "price": minsell, "size": 1}))
            print("minsell = ", minsell)
            print("The exchange replied:", read_from_exchange(exchange), file=sys.stderr)
            print("The exchange replied:", read_from_exchange(exchange), file=sys.stderr)
            print("The exchange replied:", read_from_exchange(exchange), file=sys.stderr)
            opShares += 1
            i += 1

    # A common mistake people make is to call write_to_exchange() > 1
    # time for every read_from_exchange() response.
    # Since many write messages generate marketdata, this will cause an
    # exponential explosion in pending messages. Please, don't do that
    print("The exchange replied:", read_from_exchange(exchange), file=sys.stderr)

if __name__ == "__main__":
    main()
