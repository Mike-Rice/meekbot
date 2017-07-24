import socket
import string
import settings
import viewer
import urllib.request, json
import time, _thread
from time import sleep, time
import dbshell #database shell built for this bot

class twitchStream(object):
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
    _reward_name = name of the rewards for this particular stream
    _reward_rate = rate of reward accrual
    _reward_time_dur = duration of time between accrual
    _reward_dur_unit = time unit of reward accural (sec/min/hour/day)
                        if seconds chosen, minimum of 30 seconds required
    _30_sec_tick = the number of times 30 seconds has passed between sleeps
    _max_tick = number of ticks before resetting _30_sec_tick
    _db_tick_cnt = number of ticks since the database was last updated. Used
                   to cache changes and update the database every 5 minutes
    _db_max_tick = max number of ticks before the cached info is pushed to the
                   database
    """
    def __init__(self, stream_name):
        self.stream_name = stream_name
        self.stream_socket = socket.socket()
        self.viewerlist = {}
        self.last_active_list = []
        
        #reward system vars
        self._reward_name = "none"
        self._reward_rate = 1
        self._reward_time_dur = 30
        self._reward_dur_unit = 'Seconds'
        self._30_sec_tick = 0
        self._max_tick = 0 #default to 0 to ignore if stream opts out
        self._db_tick_cnt = 0
        self._db_max_tick = 10 #updates the database every 5 minutes
        
        #connects to the database to grab the streamer stream id or enter 
        #streamer into the database
        self.stream_db = dbshell.database()
        self.stream_id = self.stream_db.check_stream(self.stream_name)
        if self.stream_id > 0:
            print('Found the streamer!')
            
            #Get Stream reward info from database
            rewards= self.stream_db.get_stream_reward_info(self.stream_id)
            if rewards != "None":
                self._reward_name = rewards[0]
                self._reward_rate = rewards[1]
                self._reward_time_dur = rewards[2]
                self._reward_time_dur_unit = rewards[3]
                
                #sets reward time duration to seconds
                #TODO - CHANGE THIS SO THAT IT IS STORED IN SECONDS WHEN
                #ENTERED FROM FRONT END.  NEED TO BUILD FRONT END
                if self._reward_time_dur_unit == 'Minute':
                    self._reward_time_dur = self._reward_time_dur * 60
                    self._reward_time_dur_unit = 'Second'
                elif self._reward_time_dur_unit == 'Hour':
                    self._reward_time_dur = self._reward_time_dur * 3600
                    self._reward_time_dur_unit = 'Second'
                elif self._reward_time_dur_unit == 'Day':
                    self._reward_time_dur = self._reward_time_dur * 86400
                    self._reward_time_dur_unit = 'Second'
                
                self._max_tick = self._reward_time_dur / 30
        else:
            self.stream_id = self.stream_db.add_stream(self.stream_name)
    
    def open_socket(self):
        """ Opens connection to the channel given to the class on init"""
        
        self.stream_socket.connect((settings.HOST, settings.PORT))
        self.stream_socket.send("PASS {}\r\n".format(settings.PASS).encode("utf-8"))
        self.stream_socket.send("NICK {}\r\n".format(settings.IDENT).encode("utf-8"))
        self.stream_socket.send("JOIN #{}\r\n".format(self.stream_name).encode("utf-8"))
        
        self._join_room()

    def close_socket(self):
        print("Closing connection to: " + self.stream_name)
        self.stream_socket.send("QUIT".encode("utf-8"))

    def _join_room(self):
        """ Reads through all the returned text when a Twitch stream's 
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
        """ Returns whether or not the socket has received the last bit of text
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
        
        message_temp = "PRIVMSG #" + self.stream_name + " :" + message + "\r\n"
        self.stream_socket.send(message_temp.encode("utf-8"))
        print("Sent: " + message_temp)

    def get_user(self, line):
        """Gets the username for the person who submitted a line to chat
           
            Parameters:
                line - The last line read into the buffer
              
            Return:
                user - the username of who submitted the message
        """
        separate = line.split(":", 2)
        user = separate[1].split("!", 1)[0]
        return user

    def get_message(self, line):
        """Gets the message submitted to chat
           
            Parameters:
                line - The last line read into the buffer
              
            Return:
                message - the message submitted to chat
        """
        separate = line.split(":", 2)
        message = separate[2]
        return message

    def eval_message(self, user, message):
        """Evaluates the message being passed in along with who submitted
           
            Parameters:
                user - username of the person who sent the message
                message - the message submitted to chat
              
            Return:
                keep_running_flg - Flag to keep the bot running
        """
        keep_running_flg = True

        #if user not in viewerlist initiate them
        if user not in self.viewerlist:
            self._init_viewer(user, "viewer")

        #if a user is tagged call the functions to get the user and then in
        #crease the tag count used for stream engagement algorithm
        if "@" in message:
            taggedUser = self._get_tagged_user(message)
            if taggedUser[0] != "None":
                for n in range(0, len(taggedUser)):
                    if taggedUser[n] != user:
                        self.viewerlist[user].tag_cnt += 1
                
        #TODO - CHANGE THIS TO EVALUATE COMMANDS FROM THE DATABASE
        if "You Suck" in message:
            self.send_message("No, you suck.")

        elif "taquitos" in message:
            self.send_message("Taquitos are a delicious after pushup snack")

        #CHANGE THIS LATER TO PULL CHANNEL OWNER
        elif (
               (   
                   self.get_user_level(user) == "mod" 
                or user == "meekus1212"
               ) 
              and "Exit" in message
              ):
            #self.send_message("That's all folks!")
            self.close_socket()
            keep_running_flg = False

        #set the chat count to the existing chat count plus 1
        self.viewerlist[user].chat_cnt += 1
        
        return keep_running_flg       
    
    def thread_fill_viewerList(self):
        """Manages the active viewer list, viewer level, and ensures viewers
           are in the database with the appropriate stream relationship and
           relationship type.
           
           Runs in a seperate thread.
        """
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
                        self._init_viewer(p, "mod")
                        self.last_active_list.append(p)
                    for p in data["chatters"]["global_mods"]:
                        self._init_viewer(p, "global_mod")
                        self.last_active_list.append(p)
                    for p in data["chatters"]["admins"]:
                        self._init_viewer(p, "admin")
                        self.last_active_list.append(p)
                    for p in data["chatters"]["staff"]:
                        self._init_viewer(p, "staff")
                        self.last_active_list.append(p)
                    for p in data["chatters"]["viewers"]:
                        self._init_viewer(p, "viewer")
                        self.last_active_list.append(p)  
                        
                    #Go through viewers and get their person_id or add them to the database with the appropriate relation
                         
            except:
                'do nothing'
            
            self._remove_departed_viewers()
            #print(self.viewerlist)
            self._db_tick_cnt += 1
            
            if(self._db_tick_cnt == self._db_max_tick):
                self._db_tick_cnt = 0 #reset tick count
                for user in self.viewerlist:
                    self.stream_db.update_user_rewards(self.stream_id, 
                                                       self.viewerlist[user].person_id, 
                                                       self.viewerlist[user].reward_points)
            
            sleep(10) #only look at list every 10 seconds
    
    def _remove_departed_viewers(self):
        """Removes departed viewers from the active viewer list"""
        
        departedViewers = list(set(list(self.viewerlist))-set(self.last_active_list))

        for n in range(1,len(departedViewers)):
            if departedViewers[n] in self.viewerlist:
                #make sure to update database values for user
                #print("Removing " + departedViewers[n])
                self.stream_db.update_user_rewards(self.stream_id, 
                                                   self.viewerlist[departedViewers[n]].person_id, 
                                                   self.viewerlist[departedViewers[n]].reward_points)
                del self.viewerlist[departedViewers[n]]
        
    def _init_viewer(self, user, viewlvl):
        """Initializes the viewer and puts the viewer object into viewerlist.
        
           If the viewer doesn't have a relationship with the stream one is
           created. If the viewer relationship is different than what is in the database
           it is updated.
           
           Since this is called for each iteration of the viewerlist population
           the rewards counter is increased in this function as well.
           
           Parameters:
               user = Username of the viewer
               viewlvl = The permission level of the viewer
        
        """

        if user == self.stream_name:    #if the viewer is the streamer set to a streamer relationship
            streamReltn = 'streamer'
        else:
            streamReltn = viewlvl
            
        if user in self.viewerlist: #if the viewer is already in the list make sure the relationships line up
            
            #No rewards for stream
            if self._max_tick != 0:
                #Updates the viewer's reward tick count as well as reward points if
                #they meet the threshhold
                if ((self.viewerlist[user].reward_ticks + 1) == self._max_tick):
                    self.viewerlist[user].reward_ticks = 0
                    self.viewerlist[user].reward_points += self._reward_rate
                else:
                    self.viewerlist[user].reward_ticks += 1
            
            #update viewer level if it has changed
            if streamReltn != self.viewerlist[user].view_lvl:
                self.viewerlist[user].view_lvl = streamReltn
                self.stream_db.update_person_stream_reltn(self.viewerlist[user].person_id, self.stream_id, streamReltn)
  
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
            
            self.viewerlist[user] = viewer.viewer(personID, user, streamReltn)
            
            #get number of reward points for user in stream
            self.viewerlist[user].reward_points = self.stream_db.get_person_stream_rewards(self.stream_id, personID)

    def _get_tagged_user(self, message):
        """Parses out the message to determine which viewers were tagged.
        
           Parameters:
               - message = The message being parsed
           
           Returns: A list of tagged users
        """
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

    #returns the user's view level (mod/staff/admin/viewer/etc...)
    def get_user_level(self,user):    
        if user in self.viewerlist:
            userLevel = self.viewerlist[user].view_lvl#['viewlvl']
        else:
            userLevel = "viewer" #if user isn't found send back viewer since it has the least privs
        
        return userLevel
