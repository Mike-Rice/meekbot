from botsocket import twitchStream
import time, _thread
from time import sleep
import logging
#import dbshell


def main():
    #select stream name
    streamName = input("Enter the stream name you wish to join: ")

    #set logging to include date/time and message
    logging.basicConfig(filename='exceptions.log',level=logging.DEBUG)
    logging.basicConfig(format='%(asctime)s %(message)s')
    logging.info("Started")
    
    readbuffer = "" #instantiate the buffer
    
    streamCon = twitchStream(streamName)
    streamCon.openSocket()
    #streamCon.joinRoom()

    #populate viewer list into dictionary
    _thread.start_new_thread(streamCon.threadFillViewerList, ())
    
    runFlag = True #escape variable to kill the bot at any time
    
    while runFlag:
        response = streamCon.s.recv(1024).decode("utf-8")
        if response == "PING :tmi.twitch.tv\r\n":
            streamCon.s.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
            print("Sent Pong")
        else:
            readbuffer = readbuffer + response
            temp = readbuffer.split("\r\n")
            readbuffer = temp.pop()
    		
            for line in temp:
                try:
                    print(line.encode('utf-8'))
    
                    user = streamCon.getUser(line)                    
                    message = streamCon.getMessage(line)
                    
                    print (user + " typed :" + message)

                    try:
                        runFlag = streamCon.evalMessage(user,message)
                    except:
                        logging.debug("Message Eval Exception")
                        logging.debug(user + ":" + message)
                except:
                    #log this into the exceptions log file
                    print("Message exception")
                    logging.debug("Line Read Exception")
                    logging.debug(line.encode('utf-8'))
                    
        time.sleep(1)
    
    logging.info("Finished")

if __name__ == "__main__":
    main()