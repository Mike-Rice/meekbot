from botsocket import twitchStream
import time
import _thread
# from time import sleep
import logging


def main():
    """Primary function to execute meekbot"""    
    
    # TODO: Adjust once a web framework is setup to run the bot script
    streamName = 'meekus1212'  # input("Enter the stream name you wish to join: ")

    #set logging to include date/time and message
    logging.basicConfig(filename='exceptions.log',level=logging.DEBUG)
    logging.basicConfig(format='%(asctime)s %(message)s')
    logging.info("Started")
    
    readbuffer = ""  # instantiate the buffer
    
    streamCon = twitchStream(streamName)
    streamCon.open_socket()

    # populate viewer list into dictionary
    _thread.start_new_thread(streamCon.thread_fill_viewerList, ())
    
    runFlag = True  # escape variable to kill the bot at any time
    
    while runFlag:
        response = streamCon.stream_socket.recv(1024).decode("utf-8")
        if response == "PING :tmi.twitch.tv\r\n":
            streamCon.stream_socket.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
            print("Sent Pong")
        else:
            readbuffer = readbuffer + response
            temp = readbuffer.split("\r\n")
            readbuffer = temp.pop()
            
            for line in temp:
                try:
                    print(line.encode('utf-8'))
    
                    user = streamCon.get_user(line)                    
                    message = streamCon.get_message(line)
                    
                    print (user + " typed :" + message)

                    try:
                        runFlag = streamCon.eval_message(user,message)
                    except:
                        logging.debug("Message Eval Exception")
                        logging.debug(user + ":" + message)
                except:
                    # log this into the exceptions log file
                    print("Message exception")
                    logging.debug("Line Read Exception")
                    logging.debug(line.encode('utf-8'))
                    
        time.sleep(1)
    
    logging.info("Finished")

if __name__ == "__main__":
    main()