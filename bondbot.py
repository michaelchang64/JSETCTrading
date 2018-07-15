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
# def get_hello_bonds(msg):
#     shares = {"AAPL": {"num": 0, "minsell": -1, "maxbuy": -1}, "GOOG": {"num": 0, "minsell": -1, "maxbuy": -1}, "MSFT": {"num": 0, "minsell": -1, "maxbuy": -1}}  # order is AAPL 0, GOOG 4, MSFT 5
#     if(msg["type"] == "hello"):
#         shares["AAPL"]["num"] = msg["symbols"][0]["position"]
#         shares["GOOG"]["num"] = msg["symbols"][4]["position"]
#         shares["MSFT"]["num"] = msg["symbols"][5]["position"]
#     return shares

def get_hello_bonds(msg):
    shares = 0
    if(msg["type"] == "hello" and len(msg) == 2):
        bonds = msg["symbols"][3]["position"]
    return shares

def absdiff(a, b):
    return abs(a - b)

def main():
    i = 0
    opShares = 0 # Shares to operate on
    company = "BOND"
    maxsell = 0
    minsell = 0

    exchange = connect()

    print(write_to_exchange(exchange, {"type": "hello", "team": team_name.upper()}))
    for j in range(0, 8):
        print("The exchange replied:", read_from_exchange(exchange), file=sys.stderr)

    msg = read_from_exchange(exchange)

    opShares = get_hello_bonds(msg)
    print(opShares)

    while(i < 10):
        if(msg["type"] == "book"):
            if(msg["symbol"] == company):
                buyarr = []
                sellarr = []
                for price, stock in msg["buy"]:
                    buyarr.append(price)
                maxbuy = max(buyarr)
                print("initial maxbuy: ", maxbuy)
                for price, stock in msg["sell"]:
                    sellarr.append(price)
                minsell = min(sellarr) - 1
                print("initial minsell: ", minsell)
                print(shares)
        else:
            print("missed the book")

        try:
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
        except:
            pass

    # A common mistake people make is to call write_to_exchange() > 1
    # time for every read_from_exchange() response.
    # Since many write messages generate marketdata, this will cause an
    # exponential explosion in pending messages. Please, don't do that
    print("The exchange replied:", read_from_exchange(exchange), file=sys.stderr)

if __name__ == "__main__":
    main()
