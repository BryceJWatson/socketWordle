from ast import Bytes
from pickle import FALSE
import socket
import threading
import sys
import random
import time
from turtle import position
from Crypto.Cipher import AES
import binascii, os

#Message size
HEADER = 64
#Port is provided by shellscript argument
PORT= int(sys.argv[1])
#Get ip address of current machine
HOST = "0.0.0.0"
#Assign tuple with this machine's ip address and desired port number
ADDRESS = (HOST, PORT)
#Character encoding format
FORMAT = 'utf-8'
#Message for users to disconnect from the server
DISCONNECT_MESSAGE = "DISCONNECT"
#Message to start game
STARTGAME_MESSAGE = "START GAME"
#Message to end game
GAMEOVER_MESSAGE = "GAME OVER"
#Create socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#Bind the socket to the address
server.bind(ADDRESS)

#Read in target words
TARGET_WORD_LIST = []
WORD_FILE = open("target.txt")
for word in WORD_FILE:
    TARGET_WORD_LIST.append(word.strip())
#Read in guess words
GUESS_WORD_LIST = []
WORD_FILE = open("guess.txt")
for word in WORD_FILE:
    GUESS_WORD_LIST.append(word.strip())

#Shared encryption key with client
key = b"Sixteen byte key"

#Function to encrypt messages
def encrypt(data, key, iv):
    plaintext = data
    plaintext += b' ' * (16 - len(plaintext) % 16)

    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.encrypt(plaintext)

#Function to decrypt messages
def decrypt(data, key, iv):

    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.decrypt(data)

#Function to handle the client once connected to the server
def handle_client(connection, address):
    print(f"[NEW CONNECTION] {address} connected.")
    target = random.choice(TARGET_WORD_LIST)
    hint = '_____'
    valid_guesses = 0
    connected = True

    #Run forever as long as this client remains connected
    while connected:
        iv = connection.recv(16)
       
        #If we have recieved the initialization vector
        if iv:
            #Setting expected size of messages
            msg_length = connection.recv(HEADER).decode(FORMAT)
            #If there is a message
            if msg_length:
                #Establish protocol- expect messages of size 16 bytes, decrypt and decode them, then convert to uppercase
                msg_length = int(msg_length)
                msg = connection.recv(16)
                msg = decrypt(msg, key, iv)
                msg = msg.decode(FORMAT).strip()
                msg = msg.upper()
                #If the server recieves a disconnect message for whatever reason, send it back and close the connection
                if msg == DISCONNECT_MESSAGE:
                    message = DISCONNECT_MESSAGE.encode(FORMAT)
                    connection.send(encrypt(message, key, iv))
                    connected = False
                    connection.close
                    print(f"[CLIENT DISCONNECTED] {address} Disconnected.")
                #If all goes well then the client sends the startgame message and the wordle game begins.
                elif msg == STARTGAME_MESSAGE:
                    print(f"[GAME START] {address} started a game.")
                    #print(f"Their word is: {target}")
                    message = "OK".encode(FORMAT)
                    connection.send(encrypt(message, key, iv))
                    time.sleep(0.1)
                    hint = hint.encode(FORMAT)
                    connection.send(encrypt(hint, key, iv))
                #Any other messages are treated as guesses from the client.
                else:
                    #If the word is an invalid guess, meaning its not a 5 character string and/or isn't in the guess word list
                    if not msg in GUESS_WORD_LIST:                    
                        print(f"[CLIENT] {address} guessed invalid word {msg}")
                        message = "INVALID GUESS".encode(FORMAT)
                        connection.send(encrypt(message, key, iv))
                    #If the word is a valid guess, but its not the target word
                    elif (msg in GUESS_WORD_LIST) & (not msg == target):
                        #Make hint an empty string
                        hint = ''
                        print(f"[CLIENT] {address} guessed {msg}")
                        #Create a new hint for the user, depending on their previous guess
                        for i in range(len(msg)):
                            if msg[i] == target[i]:
                                hint += msg[i]
                            elif msg[i] in target:
                                hint += msg[i].lower()
                            else:
                                hint += '_'
                        #increment the number of valid guesses to later drop the bombshell that they suck at wordle after they finally win
                        valid_guesses += 1
                        message = "VALID GUESS".encode(FORMAT)
                        connection.send(encrypt(message, key, iv))
                        #Sleep so theres a buffer between messages. This avoids the client getting confused when recieving more than one message at a time. This is a bad solution for a real server for obvious reasons
                        time.sleep(0.1)
                        hint = hint.encode(FORMAT)
                        connection.send(encrypt(hint, key, iv))
                    #Otherwise, if the word is the target word, then obviously the game is over and the user wins. Send appropriate messages and then close the connection.
                    elif (msg == target):
                        print(f"[CLIENT] {address} guessed {msg}")
                        valid_guesses += 1
                        valid_guesses = str(valid_guesses)
                        message = GAMEOVER_MESSAGE.encode(FORMAT)
                        connection.send(encrypt(message, key, iv))
                        time.sleep(0.1)
                        valid_guesses = valid_guesses.encode(FORMAT)
                        connection.send(encrypt(valid_guesses, key, iv))
                        connected = FALSE
                        connection.close
                        print(f"[GAME COMPLETED] {address} has finished their game.")
                        print(f"[CLIENT DISCONNECTED] {address} Disconnected.")



#Function that starts the server, listens for new connections, accepts them and then passes them to handle_client()
def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {HOST}")
    print("To close the server, press Ctrl+C")
    while True:
        connection, address = server.accept()
        thread = threading.Thread(target=handle_client, args=(connection, address))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")


print("[STARTING] Server is starting...")
start()