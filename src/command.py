class command(object):
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
        self.command_req_permissions = 0 # Only the streamer can use it at 0

        # The variable list for the command which is pulled from meekbot.command_detail
        self.command_vars = []
        self.input_vars = []  # The input after the command is called from the chat

        # set defaults for all values
        self.gaming_tags = []  # list since it could be multiple services
        self.use_cnt = 0

    # Function to build output string

    # Function to increase count and store it int the database

    # Function to reset counter

    # Function to build and store multistream

    # Function to edit the command

    # Function to delete the command