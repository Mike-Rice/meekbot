import dbshell

class cmd(object):
    '''
    This will end up being a container class.  Used to store information
    on each command for a channel.

    Will need its own dbshell reference

    Includes usage metrics for later usage
    '''

    def __init__(self, stream_id, command_name, command_id):
        '''
        Constructor
        '''
        self.stream_id = stream_id
        self.command_id = command_id
        self.command_name = command_name
        self.command_type = 'Unknown'
        self.command_text = ''
        self.cooldown_dur = 0
        self.cooldown_dur_unit = 'sec'
        self.command_req_permissions = ''  # 0  # Only the streamer can use it at 0

        # The variable list for the command which is pulled from meekbot.command_detail
        self.command_vars = {}

        # set defaults for all values
        self.gaming_tags = []  # list since it could be multiple services
        self.use_cnt = 0

    def print(self):
        # print('Stream ID: ' + str(self.stream_id))
        # print('Command ID: ' + str(self.command_id))
        # print('Command Name: ' + self.command_name)
        # print('Command Type: ' + self.command_type)
        # print('Command Text: ' + self.command_text)
        # print('Cooldown Duration: ' + str(self.cooldown_dur))
        # print('Cooldown Duration Unit: ' + self.cooldown_dur_unit)
        # print('Req Permissions: ' + self.command_req_permissions)
        print(self.command_vars)

    def add_detail(self, seq, det_id, name, text, num, det_type):
        self.command_vars[seq] = {}
        self.command_vars[seq]['id'] = det_id
        self.command_vars[seq]['name'] = name
        self.command_vars[seq]['text'] = text
        self.command_vars[seq]['num'] = num
        self.command_vars[seq]['type'] = det_type

    def get_detail_name(self, seq):
        return self.command_vars[seq]['name']

    def get_detail_num(self, seq):
        return self.command_vars[seq]['num']

    def get_detail_text(self, seq):
        return self.command_vars[seq]['text']

    def get_detail_type(self, seq):
        return self.command_vars[seq]['type']

    def set_detail_name(self, seq, val):
        self.command_vars[seq]['name'] = val

    def set_detail_num(self, seq, val):
        self.command_vars[seq]['num'] = float(val)

    def set_detail_text(self, seq, val):
        self.command_vars[seq]['text'] = val

    def set_detail_type(self, seq, val):
        self.command_vars[seq]['type'] = val.upper()


    # Function to build output string
    def build_output(self, message):
        # TODO: Split out variables and replace them in the message

        # TODO: Split out command details, i.e. counters/multi values
        if len(self.command_vars) > 0:
            print('Review command details')

        output_string = self.command_text

        return output_string

    # Function to increase count and store it int the database

    # Function to reset counter

    # Function to build and store multistream

    # Function to edit the command

    # Function to delete the command
