import socket
import string
import settings
import urllib.request, json
import time, _thread
from time import sleep, time
import dbshell #database shell built for this bot

class twitchStream():
    """
    This class is the driver for a specific stream.  All stream activity will
    be handled inside of this class.
    
    Variables:
    stream_id = id number of the stream from meekbot.stream
    stream_name = The name of the stream to which the object is connecting
    stream_socket = The socket used to sending/recieving info from the stream's chat
    stream_db = database object used to pass data to/from meekbot database
    
    viwerlist = dictionary of viewers in the channel
    last_active_list = list of users that were active the last time the 
                       viewerlist was refreshed
    """
    def __init__(self, streamName):
        self.stream_name = streamName
        self.stream_socket = socket.socket()
        self.viewerlist = {}
        self.last_active_list = []
        
        #connects to the database to grab the streamer stream id or enter 
        #streamer into the database
        self.stream_db = dbshell.database()
        self.stream_id = self.stream_db.check_stream(self.stream_name)
        if self.stream_id > 0:
            print('Found the streamer!')
        else:
            self.stream_id = self.stream_db.add_stream(self.stream_name)
    
    #Opens connection to channel
    def open_socket(self):
        """Opens connection to the channel given to the class on init"""
        
        self.stream_socket.connect((settings.HOST, settings.PORT))
        self.stream_socket.send("PASS {}\r\n".format(settings.PASS).encode("utf-8"))
        self.stream_socket.send("NICK {}\r\n".format(settings.IDENT).encode("utf-8"))
        self.stream_socket.send("JOIN #{}\r\n".format(self.stream_name).encode("utf-8"))
        
        self._join_room()

    def close_socket(self):
        print("Closing connection to: " + self.stream_name)
        self.stream_socket.send("QUIT".encode("utf-8"))

    #joins a channel so that the content before user messages can be ignored
    def _join_room(self):
        """Reads through all the returned text when a Twitch stream's 
           room is joined."""
           
        readbuffer = ""
        loading_flg = True
        while loading_flg:
            readbuffer = readbuffer + self.stream_socket.recv(1024).decode("utf-8")
            temp =readbuffer.split("\r\n")
            readbuffer = temp.pop()
                    
            for line in temp:
                print(line)
                loading_flg = self._loading_complete(line)
                
        #self.send_message("Did someone say bot?.")
            
    def _loading_complete(self,line):
        """Returns whether or not the socket has received the last bit of text
           before starting to see viewer messages
           
           Parameters:
             line - Line of text read in by the socket to evaluate
        
           Returns: Boolean flag of whether this is the last line of room load
        """
           
        if("End of /NAMES list" in line):
            return False
        else:
            return True
          
    def send_message(self,message):
        """Sends a message to the channel to which the class is connected
        
           Parameters:
               message - The message to send to the chat
        """
        
        messageTemp = "PRIVMSG #" + self.stream_name + " :" + message + "\r\n"
        self.stream_socket.send(messageTemp.encode("utf-8"))
        print("Sent: " + messageTemp)

    #Method: getMessage
    #Returns the user whom submitted a line to chat
    #Paramenters:
        #line - The most recent line parsed from the buffer
    def getUser(self, line):
        separate = line.split(":", 2)
        user = separate[1].split("!", 1)[0]
        return user
        
    #Method: getMessage
    #Returns the message that a user submitted to chat
    #Paramenters:
        #line - The most recent line parsed from the buffer
    def getMessage(self, line):
        separate = line.split(":", 2)
        message = separate[2]
        return message

    #method to parse the incoming message to determine if there's a command in der
    #look at changing this in the future to pull from a database containing all commands
    def evalMessage(self, user, message):
        keepRunning = True
        
        #if a user is tagged call the functions to get the user and then increase the tag count
        if "@" in message:
            taggedUser = self.getTaggedUser(message)
            if taggedUser[0] != "None":
                for n in range(0, len(taggedUser)):
                    if taggedUser[n] != user:
                        self.setTagCount(taggedUser[n], self.getTagCount(taggedUser[n]) + 1)
                
        if "You Suck" in message:
            self.send_message("No, you suck.")

        elif "taquitos" in message:
            self.send_message("Taquitos are a delicious after pushup snack")

        #CHANGE THIS LATER TO PULL CHANNEL OWNER
        elif (self.getUserLevel(user) == "mod" or user == "meekus1212") and "Exit" in message:
            #self.send_message("That's all folks!")
            self.close_socket()
            keepRunning = False

        #set the chat count to the existing chat count plus 1
        self.setChatCount(user, self.getChatCount(user)+1)
        
        return keepRunning       
    
    # Function: threadFillViewerList
    # In a separate thread, fill up the op list
    def threadFillViewerList(self):
        while True:
            try:
                url = "http://tmi.twitch.tv/group/user/"+ self.stream_name + "/chatters"
                
                req = urllib.request.Request(url, headers={"accept": "*/*"})
                response = urllib.request.urlopen(req).read().decode('utf-8')

                if response.find("502 Bad Gateway") == -1:
                    #self.viewerlist.clear() #figure out when I want to clear this for memory management
                    data = json.loads(response)
                    
                    sleep(5)    #add a small delay for data to fully populate            
                    self.last_active_list.clear()    
                    #loop through and add each viewer into the dictionary
                    for p in data["chatters"]["moderators"]:
                        self.initViewer(p, "mod")
                        self.last_active_list.append(p)
                    for p in data["chatters"]["global_mods"]:
                        self.initViewer(p, "global_mod")
                        self.last_active_list.append(p)
                    for p in data["chatters"]["admins"]:
                        self.initViewer(p, "admin")
                        self.last_active_list.append(p)
                    for p in data["chatters"]["staff"]:
                        self.initViewer(p, "staff")
                        self.last_active_list.append(p)
                    for p in data["chatters"]["viewers"]:
                        self.initViewer(p, "viewer")
                        self.last_active_list.append(p)  
                        
                    #Go through viewers and get their person_id or add them to the database with the appropriate relation
                         
            except:
                'do nothing'
            
            self.removeDepartedViewers()
            #print(self.viewerlist)
            
            sleep(10) #only look at list every 30 seconds
    
    def removeDepartedViewers(self):
        departedViewers = list(set(list(self.viewerlist))-set(self.last_active_list))


        for n in range(1,len(departedViewers)):
            if departedViewers[n] in self.viewerlist:
                #make sure to update database values for user
                #print("Removing " + departedViewers[n])
                del self.viewerlist[departedViewers[n]]
        
    
    #returns the user's view level (mod/staff/admin/viewer/etc...)
    def getUserLevel(self,user):    
        if user in self.viewerlist:
            userLevel = self.viewerlist[user]['viewlvl']
        else:
            userLevel = "viewer" #if user isn't found send back viewer since it has the least privs
        
        return userLevel
    
    #Initialize a viewer in the viewer dictionary
    def initViewer(self, user, viewlvl):

        if user == self.stream_name:    #if the viewer is the streamer set to a streamer relationship
            streamReltn = 'streamer'
        else:
            streamReltn = viewlvl
            
            
        if user in self.viewerlist: #if the viewer is already in the list make sure the relationships line up
            #update viewer level if it has changed
            if streamReltn != self.viewerlist[user]['viewlvl']:
                self.viewerlist[user]['viewlvl'] = streamReltn
                self.stream_db.update_person_stream_reltn(self.viewerlist[user]['person_id'], self.stream_id, streamReltn)
                
        else:
            personID = self.stream_db.get_person_id(user)
            print('Caputred person_id = ' + str(personID))
            if personID < 0: #error in query
                print('ERROR GETTING PERSON_ID')
                personID = 0
            elif personID == 0:
                print('Add personID')
                personID = self.stream_db.add_person(user, self.stream_id, streamReltn)
                if personID < 0:
                    print('Error adding person')
                    personID = 0
            else:# personID > 0:
                self.stream_db.update_person_stream_reltn(personID, self.stream_id, streamReltn)
                print('Test')
            
            self.viewerlist[user] = {}
            self.viewerlist[user]['person_id'] = personID
            self.viewerlist[user]['viewlvl'] = streamReltn
            self.viewerlist[user]['chatCnt'] = 0
            self.viewerlist[user]['gamingTag'] = "none"
            self.viewerlist[user]['tagCnt'] = 0
            self.viewerlist[user]['begActiveDTTM'] = time()  #when viewer started watching stream
            self.viewerlist[user]['lastActiveDTTM'] = time() #default to initial time loaded
                                                             #so that I can clear inactive viewers from
                                                             #the list if they are no longer there
            
    #increases the number of messages submitted by a viewer.
    def setChatCount(self, user, chatCnt):
        #if user not in viewerlist initiate them
        if user not in self.viewerlist:
            self.initViewer(user, "viewer")
            
        self.viewerlist[user]['chatCnt'] = chatCnt
        self.setLastActiveDTTM(user, time()) #chat count updated, set last active date time for user
    
    def getChatCount(self, user):
        retval = 0 #default to 0
        
        if user in self.viewerlist:
            retval = self.viewerlist[user]['chatCnt']
        
        return retval

    #increases the number of messages submitted by a viewer.
    def setTagCount(self, user, tagCnt):

        #if user not in viewerlist don't worry about increasing tag count
        if user in self.viewerlist:
            self.viewerlist[user]['tagCnt'] = tagCnt
    
    
    def getTagCount(self, user):
        retval = 0 #default to 0
        
        if user in self.viewerlist:
            retval = self.viewerlist[user]['tagCnt']
                
        return retval

    def getLastActiveDTTM(self, user):
        retval = 0.0
        
        if user in self.viewerlist:
            retval = self.viewerlist[user]['lastActiveDTTM']
        
        return retval
    
    def setLastActiveDTTM(self, user, activeDTTM):
        
        if user in self.viewerlist:
            self.viewerlist[user]['lastActiveDTTM'] = activeDTTM
        
    #Gets the user(s) tagged in the message.
    def getTaggedUser(self, message):
        userTotalCnt = 0
        taggedUser = []
        
        split_line = message.split(" ")

        for word in split_line:
            if word[0] == "@":
                taggedUser.append(word[1:])
                userTotalCnt += 1
        
        #default to none
        if userTotalCnt == 0:
            taggedUser.append("None")
        
        return taggedUser
