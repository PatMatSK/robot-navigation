import os
import socket
import re
from _thread import *

global rest
global data
global actual
global max_len
global previous
global direction
# ---------------------------------SETTINGS-------------------------------------
host = ""
port = 2222
TIMEOUT = 1
TIMEOUT_RECHARGING = 5
data_size = 1024
keys = [[23019, 32037], [32037, 29295], [18789, 13603], [16443, 29533], [18189, 21952]]
# ---------------------------------CONSTANTS-------------------------------------
SERVER_MOVE = "102 MOVE\a\b"
SERVER_TURN_LEFT = "103 TURN LEFT\a\b"
SERVER_TURN_RIGHT = "104 TURN RIGHT\a\b"
SERVER_PICK_UP = "105 GET MESSAGE\a\b"
SERVER_LOGOUT = "106 LOGOUT\a\b"
SERVER_KEY_REQUEST = "107 KEY REQUEST\a\b"
SERVER_OK = "200 OK\a\b"
SERVER_LOGIN_FAILED = "300 LOGIN FAILED\a\b"
SERVER_SYNTAX_ERROR = "301 SYNTAX ERROR\a\b"
SERVER_LOGIC_ERROR = "302 LOGIC ERROR\a\b"
SERVER_KEY_OUT_OF_RANGE_ERROR = "303 KEY OUT OF RANGE\a\b"
CLIENT_RECHARGING = "RECHARGING\a\b"
CLIENT_FULL_POWER = "FULL POWER\a\b"
# ---------------------------SERVER-SOCKET--------------------------------------
ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ss.bind((host, port))
ss.listen()


# -------------------------------CODE--------------------------------------------
def createHash(name):
    sum = 0
    for i in name:
        sum += ord(i)

    hash = (sum * 1000) % 65536
    return hash


# -----------------------------------------------------------------------------
def finish(error):
    if error != "":
        client.sendall(error.encode())
    client.close()
    exit()


# -----------------------------------------------------------------------------
def optimalize(message):
    global max_len
    m = message.split("\a\b")
    if len(m[-1]) == max_len+1 and m[-1][-1] == '\a':
        m.pop(-1)
    for i in m:
        if len(i) > max_len:
            return False
    return True


# -----------------------------------------------------------------------------
def rechargeCheck(message):
    global rest
    m = message.split("\a\b")
    if m[-1] == '':
        m.pop(-1)
        rest = ""
    else:
        rest = m.pop(-1)

    if m[-1] == "RECHARGING":
        m.pop(-1)
        print("RECHARGING")
        client.settimeout(TIMEOUT_RECHARGING)
        con = getInput()

        if con[0] != "FULL POWER":
            finish(SERVER_LOGIC_ERROR)
        m += con
        print("FULL POWER")
        client.settimeout(TIMEOUT)
        m.remove("FULL POWER")
        if len(m) == 0:
            m += getInput()
    return m


# -----------------------------------------------------------------------------
def getInput():
    global rest, data
    message = ""
    try:
        message = rest + client.recv(data_size).decode()
    except socket.timeout:
        print("Too slow man!")
        finish("")
    if not optimalize(message):
        finish(SERVER_SYNTAX_ERROR)
    while "\a\b" not in message:
        try:
            message += client.recv(data_size).decode()
            if not optimalize(message):
                finish(SERVER_SYNTAX_ERROR)

        except socket.timeout:
            print("Too slow man!")
            finish("")

    return rechargeCheck(message)


# -----------------------------------------------------------------------------
def userNameCheck():
    global data
    uname = data.pop(0)
    if len(uname) > 18:
        finish(SERVER_SYNTAX_ERROR)
    return uname


# -----------------------------------------------------------------------------
def clientConfCheck(keyID):
    global data
    if len(data) == 0:
        data = getInput()
    if len(data) == 0:
        finish("")
    conf = data.pop(0)
    if not conf.isnumeric() or len(conf) > 5:
        finish(SERVER_SYNTAX_ERROR)
    return (int(conf) - keys[keyID][1]) % 65536


# -----------------------------------------------------------------------------
def isOK(coords):
    splitted = coords.split(' ')
    if len(splitted) != 3 or splitted[0] != "OK":
        return False
    if splitted[1].isnumeric() and splitted[2].isnumeric() and splitted[0] == "OK":
        return True
    result = [d for d in re.findall(r'-?\d+', coords)]
    compare = "OK " + " ".join(result)
    if coords != compare:
        return False
    return True


# -----------------------------------------------------------------------------
def coordinateCheck():
    global data
    if len(data) == 0:
        data = getInput()
    coords = data.pop(0)

    if not isOK(coords):
        finish(SERVER_SYNTAX_ERROR)
    if coords == "OK 0 0":
        getSecretMessage()
    return coords


# -----------------------------------------------------------------------------
def keyCheck():
    global data
    if len(data) == 0:
        data = getInput()
    if not data[0].isdigit():
        finish(SERVER_SYNTAX_ERROR)
    key = int(data.pop(0))
    if 0 > key or 4 < key:
        finish(SERVER_KEY_OUT_OF_RANGE_ERROR)
    return key


# -----------------------------------------------------------------------------
def secretCheck():
    global data, max_len
    max_len = 98
    if len(data) == 0:
        data = getInput()

    secret = data[0]
    if len(secret) > 98:
        finish(SERVER_SYNTAX_ERROR)
    return secret


# ----------------------------------------------------------------------------
def getSecretMessage():
    client.sendall(SERVER_PICK_UP.encode())
    secret = secretCheck()
    print("TOP SECRET:", secret)
    finish(SERVER_LOGOUT)


# -----------------------------------------------------------------------------
def obeyObstacle():
    global data, previous, actual
    client.sendall(SERVER_TURN_RIGHT.encode())
    getInput()
    client.sendall(SERVER_MOVE.encode())
    previous = coordinateCheck()
    client.sendall(SERVER_TURN_LEFT.encode())
    getInput()
    client.sendall(SERVER_MOVE.encode())
    actual = coordinateCheck()


# -----------------------------------------------------------------------------
def turnDir(state):
    global direction
    if state:
        if direction == 'U':
            direction = 'R'
        elif direction == 'R':
            direction = 'D'
        elif direction == 'D':
            direction = 'L'
        elif direction == 'L':
            direction = 'U'
    else:
        if direction == 'U':
            direction = 'L'
        elif direction == 'R':
            direction = 'U'
        elif direction == 'D':
            direction = 'R'
        elif direction == 'L':
            direction = 'D'


# -----------------------------------------------------------------------------
def detectObstacle():
    global previous, actual, direction

    ax = int(actual.split()[1])
    ay = int(actual.split()[2])

    if ax == 0 or ay == 0:
        obeyObstacle()
        return 'I'

    if (direction == 'U' and ax > 0) or (direction == 'D' and ax < 0) or (direction == 'L' and ay > 0) or (
        direction == 'R' and ay < 0):
        client.sendall(SERVER_TURN_LEFT.encode())
        turnDir(False)

    else:
        client.sendall(SERVER_TURN_RIGHT.encode())
        turnDir(True)
    getInput()


# -----------------------------------------------------------------------------
def findDirection():
    global previous, actual
    ax = int(actual.split()[1])
    ay = int(actual.split()[2])
    px = int(previous.split()[1])
    py = int(previous.split()[2])

    if ax - px == py - ay == 0:
        print("-*-*-*-*-OBSTACLE-*-*-*-*-")
        client.sendall(SERVER_TURN_RIGHT.encode())
        getInput()
        client.sendall(SERVER_MOVE.encode())
        actual = coordinateCheck()
        ax = int(actual.split()[1])
        ay = int(actual.split()[2])
    if ay == py:
        if ax > px:
            return 'R'
        else:
            return 'L'
    elif ax == px:
        if ay > py:
            return 'U'
        else:
            return 'D'


# -----------------------------------------------------------------------------
def turn(ideal):
    global direction
    if (direction == 'D' and ideal == 'U') or (direction == 'U' and ideal == 'D') or (
        direction == 'L' and ideal == 'R') or (direction == 'R' and ideal == 'L'):
        client.sendall(SERVER_TURN_RIGHT.encode())
        getInput();turnDir(True)
        client.sendall(SERVER_TURN_RIGHT.encode())
        getInput();turnDir(True)
    elif (ideal == 'U' and direction == 'L') or (ideal == 'R' and direction == 'U') or (
        ideal == 'D' and direction == 'R') or (ideal == 'L' and direction == 'D'):
        client.sendall(SERVER_TURN_RIGHT.encode())
        getInput();turnDir(True)
    elif (ideal == 'L' and direction == 'U') or (ideal == 'D' and direction == 'L') or (
        ideal == 'R' and direction == 'D') or (ideal == 'U' and direction == 'R'):
        client.sendall(SERVER_TURN_LEFT.encode())
        getInput();turnDir(False)
    else:
        print("DIRECTION_ERROR")  # never should happen
        finish("")


# -----------------------------------------------------------------------------
def turnDecide():
    global actual, previous, direction

    ax = int(actual.split()[1])
    ay = int(actual.split()[2])

    if ax == 0:
        if ay < 0:
            ideal = 'U'
        else:
            ideal = 'D'
    else:
        if ax < 0:
            ideal = 'R'
        else:
            ideal = 'L'
    if actual == previous:
        detectObstacle()
        ideal = 'I'

    if ideal != direction and ideal != 'I':
        turn(ideal)
        direction = ideal


# -----------------------------------------------------------------------------
def Move():
    global previous, actual, direction
    client.sendall(SERVER_MOVE.encode())
    previous = coordinateCheck()
    client.sendall(SERVER_MOVE.encode())
    actual = coordinateCheck()
    direction = findDirection()

    print("----------starting-to-move----------")
    while True:
        client.sendall(SERVER_MOVE.encode())
        previous = actual
        actual = coordinateCheck()
        turnDecide()


# -----------------------------------------------------------------------------
def Autentization():
    global data, max_len
    data = getInput()
    CLIENT_USERNAME = userNameCheck()
    hash = createHash(CLIENT_USERNAME)
    print("USERNAME:", CLIENT_USERNAME)
    max_len = 10
    client.sendall(SERVER_KEY_REQUEST.encode())
    keyID = keyCheck()
    print("KEY ID:", keyID)

    SERVER_CONFIRM = str((hash + keys[keyID][0]) % 65536) + "\a\b"
    client.sendall(SERVER_CONFIRM.encode())
    
    client_hash = clientConfCheck(keyID)
    if client_hash == hash:
        print("****************MATCH*****************")
        client.sendall(SERVER_OK.encode())
    else:
        print("***************MISMATCH***************")
        finish(SERVER_LOGIN_FAILED)


# -----------------------------------------------------------------------------
while True:
    client, addrress = ss.accept()
    pid = os.fork()
    if pid == 0:
        client.close()
        continue
    print(f"Connected by {addrress}")
    data = []
    rest = ""
    actual = ""
    previous = ""
    direction = ''
    max_len = 18
    client.settimeout(TIMEOUT)
    Autentization()
    print("**************authentized**************")
    Move()
    getSecretMessage()
    finish("")

ss.close()
