class viewer(object):
    '''
    This will end up being a container class.  Used to store information
    on each viewer that is in a channel.
    '''
    
    def __init__(self, person_id, username, view_lvl):
        '''
        Constructor
        '''
        self.person_id = person_id
        self.username = username
        self.view_lvl = view_lvl
        self.bot_permissions = 5 # TODO - Add bot specific permissions in the DB
                                 # Streamer will be value 0, going up from there.
        
        #set defaults for all values
        self.gaming_tags = [] #list since it could be multiple services
        self.tag_cnt = 0
        self.chat_cnt = 0
        self.reward_pt_cnt = 0
        
        
    """
     COMMENTING OUT BECAUSE I'M NOT DOING ANYTHING SPECIAL SETTING/GETTING 
    @property
    def tag_cnt(self):
        return self.tag_cnt
     
    @tag_cnt:setter
    def tag_cnt(self, tag_cnt):
        self.tag_cnt = tag_cnt
        
    @property
    def chat_cnt(self):
        return self.chat_cnt
    
    @chat_cnt:setter
    def chat_cnt(self, chat_cnt):
        self.chat_cnt = chat_cnt
    
    @property
    def reward_pt_cnt(self):
        return self.reward_pt_cnt
    
    @reward_pt_cnt:setter
    def reward_pt_cnt(self, reward_pt_cnt):
        self.reward_pt_cnt = reward_pt_cnt
         """
    