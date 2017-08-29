import socket
import urllib.request
import json
from time import sleep

# meekbot files/classes
import viewer
import dbshell
import settings
import stream_command


class twitchStream(object):
    """
    This class is the driver for a specific stream.  All stream activity will
    be handled inside of this class.
    
    Variables:
    stream_id = id number of the stream from meekbot.stream
    stream_name = The name of the stream to which the object is connecting
    stream_socket = The socket used to sending/recieving info from the stream's chat
    stream_db = database object used to pass data to/from meekbot database
    
    viwerlist = dictionary of viewers in the channel.  Filled with viewer objects from viewer.py
    last_active_list = list of users that were active the last time the 
                       viewerlist was refreshed
    command_list = list of all commands for the stream.  Filled with command objects from command.py
    """
    def __init__(self, stream_name):
        self.stream_name = stream_name
        self.stream_socket = socket.socket()
        self.viewerlist = {}
        self.command_list = {}
        self.last_active_list = []
        
        # connects to the database to grab the streamer stream id or enter
        # streamer into the database
        self.stream_db = dbshell.database()
        self.stream_id = self.stream_db.check_stream(self.stream_name)
        if self.stream_id > 0:
            print('Found the streamer!')
        else:
            self.stream_id = self.stream_db.add_stream(self.stream_name)

        self._get_command_list()

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
                
        # self.send_message("Hi @Tazman_85 .")
            
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

        split_msg = message.split(" ")

        # if user not in viewerlist initiate them
        if user not in self.viewerlist:
            self._init_viewer(user, "viewer")

        # if a user is tagged call the functions to get the user and then in
        # crease the tag count used for stream engagement algorithm
        if "@" in message:
            taggedUser = self._get_tagged_user(message)
            if taggedUser[0] != "None":
                for n in range(0, len(taggedUser)):
                    if taggedUser[n] != user:
                        self.viewerlist[user].tag_cnt += 1

        # !mb will be a reserved command for mods to handle meekbot work
        if split_msg[0] == '!mb':
            self._mb_command(user, split_msg)
        # TODO: Add Viewer level for permission evaluation
        elif split_msg[0] in self.command_list:
            self.send_message(self.command_list[split_msg[0]].build_output(" ".join(split_msg[1:])))

        # THIS IS ONLY DURING DESIGN/BUILD
        if (user == "meekus1212"
              and "Exit" in message
              ):
            # self.send_message("That's all folks!")
            self.close_socket()
            keep_running_flg = False

        # set the chat count to the existing chat count plus 1
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
                    data = json.loads(response)
                    
                    sleep(5)    # add a small delay for data to fully populate
                    self.last_active_list.clear()    
                    # loop through and add each viewer into the dictionary
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

            except:
                'do nothing'
            
            self._remove_departed_viewers()
            # print(self.viewerlist)
            
            sleep(10) # only look at list every 30 seconds
    
    def _remove_departed_viewers(self):
        """Removes departed viewers from the active viewer list"""
        
        departedViewers = list(set(list(self.viewerlist))-set(self.last_active_list))

        for n in range(1,len(departedViewers)):
            if departedViewers[n] in self.viewerlist:
                # make sure to update database values for user
                # print("Removing " + departedViewers[n])
                del self.viewerlist[departedViewers[n]]
        
    # Initialize a viewer in the viewer dictionary
    def _init_viewer(self, user, viewlvl):

        if user == self.stream_name:    # if the viewer is the streamer set to a streamer relationship
            streamReltn = 'streamer'
        else:
            streamReltn = viewlvl

        if user in self.viewerlist: # if the viewer is already in the list make sure the relationships line up
            # update viewer level if it has changed
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

    # Gets the user(s) tagged in the message.
    def _get_tagged_user(self, message):
        userTotalCnt = 0
        taggedUser = []
        
        split_line = message.split(" ")

        for word in split_line:
            if word[0] == "@":
                taggedUser.append(word[1:])
                userTotalCnt += 1
        
        # default to none
        if userTotalCnt == 0:
            taggedUser.append("None")
        
        return taggedUser

    # returns the user's view level (mod/staff/admin/viewer/etc...)
    def getUserLevel(self,user):    
        if user in self.viewerlist:
            userLevel = self.viewerlist[user].view_lvl
        else:
            userLevel = "viewer"  # if user isn't found send back viewer since it has the least privs
        
        return userLevel

    def _get_command_list(self):
        """ Gets a list of commands for the stream and places them in a list of command objects.  Each command object
            contains the details of the command in the form of variables/counters/etc...

        :return: Nothing
        """
        cmd_tuple = self.stream_db.get_stream_commands(self.stream_id)
        for i in range(len(cmd_tuple)):
            print(cmd_tuple[i])
            temp_list = list(cmd_tuple[i])
            command_id = temp_list[0]
            command_name = temp_list[1]
            command_text = temp_list[2]
            command_type = temp_list[3]
            command_cooldown_dur = temp_list[4]
            command_cooldown_dur_unit = temp_list[5]
            command_reltn_lvl = temp_list[6]
            detail_seq = temp_list[7]
            detail_name = temp_list[8]
            detail_text = temp_list[9]
            detail_num = temp_list[10]
            detail_type = temp_list[11]
            detail_id = temp_list[12]

            # if the command is already in the list get the new details added
            if command_name not in self.command_list:
                self.command_list[command_name] = stream_command.cmd(self.stream_id, command_name, command_id)
                self.command_list[command_name].command_text = command_text
                self.command_list[command_name].command_type = command_type
                self.command_list[command_name].cooldown_dur = command_cooldown_dur
                self.command_list[command_name].cooldown_dur_unit = command_cooldown_dur_unit
                self.command_list[command_name].command_req_permissions = command_reltn_lvl

            if detail_seq is not None:
                self.command_list[command_name].add_detail(detail_seq
                                                           , detail_id
                                                           , detail_name
                                                           , detail_text
                                                           , detail_num
                                                           , detail_type)
                print('COMMAND NAME = ' + command_name)
                print('DETAIL SEQ = ' + str(detail_seq))
                self.command_list[command_name].print()

    def _mb_command(self, user, cmd_msg):

        cmd_name = cmd_msg[2]

        # look through mb command list to see where it is
        if cmd_msg[1] == 'addcmd':
            cmd_params = self._get_cmd_params(cmd_msg)
            # Build the command message.
            cmd_txt = " ".join(cmd_msg[cmd_params['ptr']:])
            print('cmd_text = ' + cmd_txt)
            self._mb_set_command(user, cmd_params['cmd_priv'], cmd_params['cooldown'], cmd_name, cmd_txt, 'Add')

        elif cmd_msg[1] == 'setvar':
            cmd_txt = " ".join(cmd_msg[3:])
            self._mb_set_var(cmd_name, cmd_txt)

        elif cmd_msg[1] == 'delcmd':
            del_success = self.stream_db.inactivate_command(self.command_list[cmd_name].command_id)
            if del_success:
                del(self.command_list[cmd_name])
                self.send_message('@' + user + ', Command ' + cmd_name + ' has been successfully deleted.')
            else:
                self.send_message('@' + user + ', Unable to delete command ' + cmd_name)

        elif cmd_msg[1] == 'editcmd':
            cmd_params = self._get_cmd_params(cmd_msg)
            # Build the command message.
            cmd_txt = " ".join(cmd_msg[cmd_params['ptr']:])
            print('cmd_text = ' + cmd_txt)
            self._mb_set_command(user, cmd_params['cmd_priv'], cmd_params['cooldown'], cmd_name, cmd_txt, 'Edit')
            print('Edit command, ' + cmd_name + ', new text = ' + cmd_txt)

    def _mb_set_var(self, cmd_name, cmd_txt):
        # Parses the command text looking for variables.  For example $[var] and $[count]
        var_ptr = cmd_txt.find('$[', 0)
        while var_ptr >= 0:
            var_end_ptr = cmd_txt.find(']', var_ptr)
            if var_end_ptr >= 0:
                seq = int(cmd_txt[var_ptr+2:var_end_ptr])
                var_ptr = cmd_txt.find('$[', var_ptr + 2)

                if var_ptr > 0:
                    value = cmd_txt[var_end_ptr+1:var_ptr]
                else:
                    value = cmd_txt[var_end_ptr + 1:]

                # Get detail type to determine what type of value is being set
                dtl_type = self.command_list[cmd_name].get_detail_type(seq)
                text_val = ''
                num_val = 0.0
                if dtl_type.upper() == 'TEXT':
                    self.command_list[cmd_name].set_detail_text(seq, value)
                    text_val = value
                elif dtl_type.upper() == 'NUM':
                    self.command_list[cmd_name].set_detail_num(seq, value)
                    num_val = float(value)

                dtl_added = self.stream_db.set_command_var(self.command_list[cmd_name].command_id
                                               , seq
                                               , self.command_list[cmd_name].get_detail_type(seq).upper()
                                               , text_val
                                               , num_val)
                if dtl_added:
                    self.send_message('Detail Updated')
                else:
                    self.send_message('Detail failed to update')

                #TODO - Else throw error

    def _get_cmd_params(self, cmd_msg):

        cmd_params = {}
        # Set default values in case they aren't entered into the command
        cmd_params['cooldown'] = 0
        cmd_params['cmd_priv'] = 'viewer'
        cmd_params['type'] = "TEXTOUTPUT"

        param_loop_flg = True
        msg_ptr = 3  # default this to 2 so it skips '!mb', command,  and the command name

        while param_loop_flg:
            if cmd_msg[msg_ptr][0] == '-':
                if cmd_msg[msg_ptr][:3] == '-cd':
                    cmd_params['cooldown'] = cmd_msg[msg_ptr][4:]
                elif cmd_msg[msg_ptr][:3] == '-ul':
                    cmd_params['cmd_priv'] = cmd_msg[msg_ptr][4:]
                elif cmd_msg[msg_ptr][:5] == '-type':
                    cmd_params['type'] = cmd_msg[msg_ptr][6:]

                msg_ptr += 1
            else:
                param_loop_flg = False

        cmd_params['ptr'] = msg_ptr # used to reference and capture cmd_txt from _mb_command

        return cmd_params

    def _get_cmd_details(self, cmd_txt):
        var_ptr = 0
        cmd_details = []

        # Parses the command text looking for variables.  For example $[var] and $[count]
        while var_ptr >= 0:
            var_ptr = cmd_txt.find('$[', var_ptr + 2)
            if(var_ptr >= 0):
                var_end_ptr = cmd_txt.find(']', var_ptr)
                if var_end_ptr >= 0:
                    detail_type = cmd_txt[var_ptr+2:var_end_ptr]
                    cmd_details.append(detail_type)
                #TODO - Else throw error

        return cmd_details

    def _mb_set_command(self, user, cmd_priv, cooldown_val, cmd_name, cmd_txt, call_type):

        #TODO - Update to pull in "cmd_params" dictionary instead of specific variables
        #TODO - Will allow using -type and setting the detail type

        cmd_details = self._get_cmd_details(cmd_txt)

        cmd_id = self.stream_db.set_stream_cmd(self.stream_id, cmd_priv, cooldown_val, cmd_name, cmd_txt, call_type)

        if cmd_id == -1 and call_type == 'Add':
            self.send_message('The command, ' + cmd_name + ', already exists.')
        else:
            # Add command to the cached command list
            if call_type == 'Add':
                self.command_list[cmd_name] = stream_command.cmd(self.stream_id, cmd_name, cmd_id)
            self.command_list[cmd_name].command_text = cmd_txt
            self.command_list[cmd_name].command_type = 'TEXTOUTPUT'
            self.command_list[cmd_name].cooldown_dur = cooldown_val
            self.command_list[cmd_name].cooldown_dur_unit = 'sec'
            self.command_list[cmd_name].command_req_permissions = cmd_priv

            # Add command details to the database and the command object
            for i, val in enumerate(cmd_details):
                detail_id = self.stream_db.add_command_detail(cmd_id, val.upper(), i + 1)

                self.command_list[cmd_name].add_detail(i+1
                                                       , detail_id
                                                       , 'TEMP'
                                                       , ''
                                                       , 0
                                                       , val.upper())
            # TODO - Add in error checking

            if call_type == 'Add':
                self.send_message('@' + user + ',the command ' + cmd_name + ' has been added!')
            elif call_type == 'Edit':
                success = self.stream_db.inactivate_command_dtls(cmd_id, len(cmd_details))
                if success:
                    self.send_message('@' + user + ',the command ' + cmd_name + ' has been updated!')
