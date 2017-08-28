#import psycopg2
#import sys
#import string
#import time

import psycopg2.pool as pool
from contextlib import contextmanager
import settings

class database(object):
    """
    This class is for the database connection and data management for the bot.
    
    _conn_string = the connection string used to connect to teh database.  
                   Pulls the password from the settings.py file
    db = the connection pool used by the cursors to query the database
    
    """
    def __init__(self):
        #Define our connection string
        self._conn_string = "host='localhost' dbname='meekbot' user='postgres' password='" + settings.dbpassword + "'"

        # print the connection string we will use to connect
        print("Connecting to database\n    ->%s" % (self._conn_string))

        # get a connection pool, if a connect cannot be made an exception will be raised here
        self.db = pool.SimpleConnectionPool(1, 5, self._conn_string)

    # Get Cursor
    @contextmanager
    def get_cursor(self):
        """Used in contexts inside of other functions to connect to the database,
        get the cursor, and commit changes and close the connection """
        
        self.con = self.db.getconn()
        try:
            yield self.con.cursor()
        finally:
            self.con.commit()
            self.db.putconn(self.con)
    
    def check_stream(self, streamName):
        """Checks to see if the stream already exists in the database.  If not
        a value in the database return a 0.
        
        Paramters:
            streamName - String value of the stream in the meekbot.stream table
        
        Return:
            streamID - ID value from meekbot.stream if exists.  If not return 0
                       -1 if error occured
                       0 if not found
        """
        streamID = 0
        try:
            sql = """SELECT stream_id, stream_name FROM meekbot.stream WHERE stream_name = '{}' and active_ind = true;"""
            print(sql.format(streamName))
            with self.get_cursor() as cursor:
                cursor.execute(sql.format(streamName))
                if cursor.rowcount > 0:
                    record = cursor.fetchone()
                    print(record)
                    streamID = record[0]
                    print(streamID)

        except:
            print("Failed checking for stream in dbshell.checkStream")
            streamID = -1 #return a negative value so that the script knows that the query failed

        return streamID
    
    
    def add_stream(self, streamName):
        """Adds a stream to the meekbot.stream table and returns the streams id
        
        Paramters:
            streamName - String value of stream being added to meekbot.stream
        
        Return:
            streamID - ID number generated during insert
                       -1 if an error occured
        """
        streamID = 0
        try:
            sql = """INSERT INTO meekbot.stream(stream_name, create_dt_tm) VALUES ('{}', {}) RETURNING stream_id;"""
            #print(sql.format(streamName,'now()'))# value_list)
            
            with self.get_cursor() as cursor:
                cursor.execute(sql.format(streamName,'now()'))
                streamID = cursor.fetchone()[0]
                print('Stream ID = ' + str(streamID))
        except:
            print("Failed adding new stream in dbshell.addStream")
            streamID = -1 #return a negative value so that the script knows that the query failed

        return streamID

    def get_person_id(self, viewerName):
        """Gets the viewer's person ID from meekbot.person table and returns it
        
        Paramters:
            viewerName - String value of viewer's username being pulled from meekbot.person
        
        Return:
            personID - ID number of the viewer if found in the datbase
                       -1 if an error occured
                       0 if not found
        """
        personID = 0
        try:
            sql = """SELECT person_id, username FROM meekbot.person WHERE username = '{}' and active_ind = true;"""
            #print(sql.format(viewerName))
            with self.get_cursor() as cursor:
                cursor.execute(sql.format(viewerName))
                if cursor.rowcount > 0:
                    record = cursor.fetchone()
                    print(record)
                    personID = record[0]
                    print(personID)
        except:
            print("Failed getting person_id in dbshell.getPersonID")
            personID = -1 #return a negative value so that the script knows that the query failed

        return personID
    
    def add_person(self, viewerName, streamID, reltn):
        """Adds a viewer to the meekbot.person table and returns the streams id
           Also adds an entry into the person_stream_reltn table containing the
           viewer's relationship to the stream (mod, viewer, admin, etc...).
           
           Use's a stored procedure inside of PostgreSQL to do the insertions.
        
        Paramters:
            viewerName - String of username being added to meekbot.person
            streamID - Stream ID of active stream from meekbot.stream table
            reltn - Viewer's relationship to the stream.  
                    reltn string value comes from meekbot.code_value table 
                    for person_stream_reltn type (code_set = 1)
                    
        
        Return:
            personID - ID number generated during insert
                       -1 if an error occured
        """
        personID = 0
        try:
            sql = """SELECT * FROM meekbot.addperson('{}', {}, '{}')"""
            print(sql.format(viewerName,streamID, reltn.upper()))
            
            with self.get_cursor() as cursor:
                cursor.execute(sql.format(viewerName,streamID, reltn.upper()))
                personID = cursor.fetchone()[0]
                print('Person ID = ' + str(personID))
        except:
            print("Failed adding person_id in dbshell.addPerson")
            personID = -1 #return a negative value so that the script knows that the query failed

        return personID
    
    def update_person_stream_reltn(self, personID, streamID, reltn):
        """Update's a viewer's relationship to the given stream.  Also will add
           a relationship if one does not already exist between person and
           stream
           
           Use's a stored procedure inside of PostgreSQL to do the 
           updates/insertions.
        
        Paramters:
            personID - Viewer's ID from meekbot.person
            streamID - Stream ID of active stream from meekbot.stream table
            reltn - Viewer's relationship to the stream.  
                    reltn string value comes from meekbot.code_value table 
                    for person_stream_reltn type (code_set = 1)
        """
        sql = """SELECT * FROM meekbot.updatePersonStreamReltn({}, {}, '{}')"""
    
        try:           
            with self.get_cursor() as cursor:
                cursor.execute(sql.format(personID,streamID, reltn.upper()))

        except:
            print("Failed updating relationship in dbshell.updatePersonStreamReltn")

    def get_stream_commands(self, stream_id):
        """Gets all commands for a specific stream

        Paramters:
            stream_id - Stream ID from meekbot.stream

        Return:
            cmd_list - List of commands containing:
                            - command_id
                            - command_name
                            - command_text
                            - parameters
        """
        cmd_list = []
        try:
            sql = """SELECT
                     commands.command_id
                    ,commands.command_name
                    ,commands.command_string
                    ,cv.description
                    ,commands.cooldown_dur
                    ,cv1.description
                    ,cv2.description
                    ,command_detail.seq
                    ,command_detail.detail_name
                    ,command_detail.detail_text
                    ,command_detail.detail_num
                    ,cv3.display_key
                    ,command_detail.command_detail_id
                FROM meekbot.commands
                    join meekbot.code_value cv on cv.code_value = meekbot.commands.command_type_cd
                    join meekbot.code_value cv1 on cv1.code_value = meekbot.commands.cooldown_dur_unit_cd
                    join meekbot.code_value cv2 on cv2.code_value = meekbot.commands.stream_reltn_cd
                    LEFT OUTER JOIN meekbot.command_detail on command_detail.command_id = meekbot.commands.command_id
                    LEFT OUTER JOIN meekbot.code_value cv3 on cv3.code_value = meekbot.command_detail.detail_type_cd
                
                WHERE commands.stream_id = {}
                  AND commands.active_ind = TRUE
                  AND cv.active_ind = TRUE
                  AND cv1.active_ind = TRUE
                  AND cv2.active_ind = TRUE
                  
                ORDER BY command_detail.seq;"""

            with self.get_cursor() as cursor:
                cursor.execute(sql.format(stream_id))
                if cursor.rowcount > 0:
                    records = cursor.fetchall()
                    cmd_list = records

        except:
            print("Failed getting command_list in dbshell.get_stream_commands")
            cmd_list[0] = -1  # return a negative value so that the script knows that the query failed

        return cmd_list



    def set_stream_cmd(self, stream_id, prm_lvl, cooldown, cmd_name, cmd_txt, call_type):

        cmd_id = 0
        try:
            sql = """SELECT * FROM meekbot.setStreamCmd({}, '{}', {}, '{}', '{}', '{}', '{}')"""
            print(sql.format(stream_id, prm_lvl, cooldown, cmd_name.lower(), cmd_txt, 'TEXTOUTPUT', call_type))

            with self.get_cursor() as cursor:
                cursor.execute(sql.format(stream_id
                                          , prm_lvl.upper()
                                          , cooldown
                                          , cmd_name.lower()
                                          , cmd_txt
                                          , 'TEXTOUTPUT'
                                          ,call_type))
                cmd_id = cursor.fetchone()[0]
                print('Command ID = ' + str(cmd_id))
        except:
            print("Failed adding command in dbshell.add_stream_cmd")
            cmd_id = -1  # return a negative value so that the script knows that the query failed

        return cmd_id

    def add_command_detail(self, cmd_id, detail_type, detail_seq):
        detail_id = 0
        try:
            sql = """SELECT * FROM meekbot.addCmdDtl({}, '{}', {})"""
            print(sql.format(cmd_id, detail_type.upper(), detail_seq))

            with self.get_cursor() as cursor:
                cursor.execute(sql.format(cmd_id, detail_type.upper(), detail_seq))
                detail_id = cursor.fetchone()[0]
                print('Detail ID = ' + str(detail_id))
        except:
            print("Failed adding detail in dbshell.add_command_detail")
            detail_id = -1  # return a negative value so that the script knows that the query failed

        return detail_id

    def set_command_var(self, cmd_id, seq, detail_type, text_val, num_val):
        query_flg = False
        try:
            sql = """SELECT * FROM meekbot.updatecmddtl({}, '{}', '{}', {}, {})"""
            print(sql.format(cmd_id, detail_type.upper(), text_val, num_val, seq))

            with self.get_cursor() as cursor:
                cursor.execute(sql.format(cmd_id, detail_type.upper(), text_val, num_val, seq))
                query_flg = cursor.fetchone()[0]

        except:
            print("Failed adding detail in dbshell.set_command_var")
            query_flg = False  # return a negative value so that the script knows that the query failed

        return query_flg

    def inactivate_command(self, cmd_id):

        try:
            sql = """UPDATE meekbot.commands SET updt_dt_tm = now()
                                                      , active_ind = FALSE
                     WHERE command_id = {};"""
            # print(sql.format(streamName,'now()'))# value_list)

            with self.get_cursor() as cursor:
                cursor.execute(sql.format(cmd_id))
                success_flg = True
        except:
            print("Failed inactivating command in dbshell.inactivate_command")
            success_flg = False

        if success_flg == True:
            try:
                sql = """UPDATE meekbot.command_detail SET updt_dt_tm = now()
                                                          , active_ind = FALSE
                         WHERE command_id = {};"""
                # print(sql.format(streamName,'now()'))# value_list)

                with self.get_cursor() as cursor:
                    cursor.execute(sql.format(cmd_id))
                    success_flg = True
            except:
                print("Failed inactivating command details in dbshell.inactivate_command")
                success_flg = False

        return success_flg

    def inactivate_command_dtls(self, cmd_id, max_seq):


        try:
            sql = """UPDATE meekbot.command_detail SET updt_dt_tm = now()
                                                      , active_ind = FALSE
                     WHERE command_id = {}
                       AND seq > {};"""
            # print(sql.format(streamName,'now()'))# value_list)

            with self.get_cursor() as cursor:
                cursor.execute(sql.format(cmd_id, max_seq))
                success_flg = True
        except:
            print("Failed inactivating command details in dbshell.inactivate_command_dtls")
            success_flg = False

        return success_flg
