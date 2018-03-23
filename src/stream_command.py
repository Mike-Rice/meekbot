import dbshell

class cmd(object):
    """
    This will end up being a container class.  Used to store information on each command for a channel.

    Includes usage metrics for later usage
    """

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
        """
        Add a stored variable/detail to the detail dictionary for this specific command

        :param seq: The Sequence number for the detail for output ordering
        :param det_id: Detail ID in meekbot.command_detail table
        :param name: Detail name, not currently used
        :param text: Text value if the detail is a text type
        :param num: Numeric Value (Float) of detail if numeric type
        :param det_type: Type of detail.  For example, text, number, count, date.  This is also the display_key value
                        from meekbot.code_value where meekbot.code_value.code_set = 4 (Command Detail Types)

        """
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
        """
        Builds the output which will end up being sent to the stream.  Replaces stored variables with the values stored
        in the database, also replaces input parameters with values entered by the user.

        :param message: Contains any input parameters for the command entered by the user.  For example:
                        <command_name> <input1> <input2>
        :return: The message which will end up being sent to the stream
        """
        split_text = self.command_text.split(" ")
        var_cnt = 1  # The current sequence when we need to replace a variable

        if len(message.strip()) == 0:
            no_params = True
        else:
            input_params = message.split(" ")
            param_cnt = 0  # Iterate through input parameters when command is called
            no_params = False

        for ptr, val in enumerate(split_text):
            if split_text[ptr][:2] == '$[':
                if self.get_detail_type(var_cnt).upper() == 'TEXT':
                    split_text[ptr] = self.get_detail_text(var_cnt)
                    var_cnt += 1
                elif ((self.get_detail_type(var_cnt).upper() == 'NUM')
                        or (self.get_detail_type(var_cnt).upper() == 'COUNT')):
                    split_text[ptr] = str(self.get_detail_num(var_cnt))
                    var_cnt += 1
            elif split_text[ptr][:2] == '$(':
                if no_params is True:
                    split_text[ptr] = ''
                else:
                    split_text[ptr] = input_params[param_cnt]
                    param_cnt += 1

        output_string = " ".join(split_text)

        return output_string

    # Function to increase count and store it int the database

    # Function to reset counter

    # Function to build and store multistream

    # Function to edit the command

    # Function to delete the command
