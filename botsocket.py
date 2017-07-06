import socket
import string
#from settings import HOST, PORT, PASS, IDENT, CHANNEL
import settings
import urllib.request, json
import time, _thread
from time import sleep, time
import dbshell #database shell built for this bot

class twitchStream():
    def __init__(self, streamName):
        self.streamName = streamName
        self.s = socket.socket()
        self.viewerlist = {}
        self.lastActiveList = []
        self.newViewerListCnt = 0
        #connects to the database to grab the streamer stream id or enter streamer into the database
        self.streamDB = dbshell.database()
        self.streamID = self.streamDB.checkStream(self.streamName)
        if self.streamID > 0:
            print('Found the streamer!')
        else:
            self.streamID = self.streamDB.addStream(self.streamName)
    
    #Opens connection to channel
    def openSocket(self):
        self.s.connect((settings.HOST, settings.PORT))
        self.s.send("PASS {}\r\n".format(settings.PASS).encode("utf-8"))
        self.s.send("NICK {}\r\n".format(settings.IDENT).encode("utf-8"))
        self.s.send("JOIN #{}\r\n".format(self.streamName).encode("utf-8"))
        
        self.joinRoom()
            
        #return self.s
          
    def sendMessage(self,message):
            messageTemp = "PRIVMSG #" + self.streamName + " :" + message + "\r\n"
            self.s.send(messageTemp.encode("utf-8"))
            print("Sent: " + messageTemp)

    def closeSocket(self):
        print("Closing connection to: " + self.streamName)
        self.s.send("QUIT".encode("utf-8"))

    #joins a channel so that the content before user messages can be ignored
    def joinRoom(self):
        readbuffer = ""
        Loading = True
        while Loading:
            readbuffer = readbuffer + self.s.recv(1024).decode("utf-8")
            temp =readbuffer.split("\r\n")
            readbuffer = temp.pop()
                    
            for line in temp:
                print(line)
                Loading = self.loadingComplete(line)
                
        self.sendMessage("Beep Boop, I am a robot.")
            
    def loadingComplete(self,line):
            if("End of /NAMES list" in line):
                return False
            else:
                return True

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
            self.sendMessage("No, you suck.")

        elif "taquitos" in message:
            self.sendMessage("Taquitos are a delicious after pushup snack")

        #CHANGE THIS LATER TO PULL CHANNEL OWNER
        elif (self.getUserLevel(user) == "mod" or user == "meekus1212") and "Exit" in message:
            self.sendMessage("That's all folks!")
            self.closeSocket()
            keepRunning = False

        #set the chat count to the existing chat count plus 1
        self.setChatCount(user, self.getChatCount(user)+1)
        
        return keepRunning       
    
    # Function: threadFillViewerList
    # In a separate thread, fill up the op list
    def threadFillViewerList(self):
        while True:
            try:
                url = "http://tmi.twitch.tv/group/user/"+ self.streamName + "/chatters"
                
                req = urllib.request.Request(url, headers={"accept": "*/*"})
                response = urllib.request.urlopen(req).read().decode('utf-8')

                if response.find("502 Bad Gateway") == -1:
                    #self.viewerlist.clear() #figure out when I want to clear this for memory management
                    data = json.loads(response)
                    
                    sleep(5)    #add a small delay for data to fully populate            
                    self.lastActiveList.clear()    
                    #loop through and add each viewer into the dictionary
                    for p in data["chatters"]["moderators"]:
                        self.initViewer(p, "mod")
                        self.lastActiveList.append(p)
                    for p in data["chatters"]["global_mods"]:
                        self.initViewer(p, "global_mod")
                        self.lastActiveList.append(p)
                    for p in data["chatters"]["admins"]:
                        self.initViewer(p, "admin")
                        self.lastActiveList.append(p)
                    for p in data["chatters"]["staff"]:
                        self.initViewer(p, "staff")
                        self.lastActiveList.append(p)
                    for p in data["chatters"]["viewers"]:
                        self.initViewer(p, "viewer")
                        self.lastActiveList.append(p)  
                        
                    #Go through viewers and get their person_id or add them to the database with the appropriate relation
                         
            except:
                'do nothing'
            
            self.removeDepartedViewers()
            #print(self.viewerlist)
            
            sleep(10) #only look at list every 30 seconds
    
    def removeDepartedViewers(self):
        departedViewers = list(set(list(self.viewerlist))-set(self.lastActiveList))


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

        if user == self.streamName:    #if the viewer is the streamer set to a streamer relationship
            streamReltn = 'streamer'
        else:
            streamReltn = viewlvl
            
            
        if user in self.viewerlist: #if the viewer is already in the list make sure the relationships line up
            #update viewer level if it has changed
            if streamReltn != self.viewerlist[user]['viewlvl']:
                self.viewerlist[user]['viewlvl'] = streamReltn
                self.streamDB.updatePersonStreamReltn(self.viewerlist[user]['person_id'], self.streamID, streamReltn)
                
        else:
            personID = self.streamDB.getPersonID(user)
            print('Caputred person_id = ' + str(personID))
            if personID < 0: #error in query
                print('ERROR GETTING PERSON_ID')
                personID = 0
            elif personID == 0:
                print('Add personID')
                personID = self.streamDB.addPerson(user, self.streamID, streamReltn)
                if personID < 0:
                    print('Error adding person')
                    personID = 0
            else:# personID > 0:
                self.streamDB.updatePersonStreamReltn(personID, self.streamID, streamReltn)
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
