import psycopg2
import psycopg2.pool as pool
import sys
import string
import time
from contextlib import contextmanager
import settings

class database():
    def __init__(self):
        #self.streamName = streamName
        
        #Define our connection string
        self._conn_string = "host='localhost' dbname='meekbot' user='postgres' password='" + settings.dbpassword + "'"

        # print the connection string we will use to connect
        print("Connecting to database\n    ->%s" % (self._conn_string))

        # get a connection pool, if a connect cannot be made an exception will be raised here
        self.db = pool.SimpleConnectionPool(1, 5, self._conn_string)

    # Get Cursor
    @contextmanager
    def get_cursor(self):
        self.con = self.db.getconn()
        try:
            yield self.con.cursor()
        finally:
            self.con.commit()
            self.db.putconn(self.con)
    
    def checkStream(self, streamName):
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

                print('GOTEEEEM')
        #finally:
        #    print('lol')
        except:
            print("Failed checking for stream in dbshell.checkStream")
            streamID = -1 #return a negative value so that the script knows that the query failed

        return streamID
    
    
    def addStream(self, streamName):
        streamID = 0
        try:
            sql = """INSERT INTO meekbot.stream(stream_name, create_dt_tm) VALUES ('{}', {}) RETURNING stream_id;"""
            #print(sql.format(streamName,'now()'))# value_list)
            
            with self.get_cursor() as cursor:
                cursor.execute(sql.format(streamName,'now()'))
                streamID = cursor.fetchone()[0]
                print('Stream ID = ' + str(streamID))
        #finally:
        #    print('lol')
        except:
            print("Failed adding new stream in dbshell.addStream")
            streamID = -1 #return a negative value so that the script knows that the query failed

        return streamID

    def getPersonID(self, viewerName):
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
        #finally:
        #    print('lol')
        except:
            print("Failed getting person_id in dbshell.getPersonID")
            personID = -1 #return a negative value so that the script knows that the query failed

        return personID
    
    def addPerson(self, viewerName, streamID, reltn):
        personID = 0
        try:
            sql = """SELECT * FROM meekbot.addperson('{}', {}, '{}')"""
            #<person_name text>, <streamid bigint>, <relation text>
            print(sql.format(viewerName,streamID, reltn.upper()))
            
            with self.get_cursor() as cursor:
                cursor.execute(sql.format(viewerName,streamID, reltn.upper()))
                personID = cursor.fetchone()[0]
                print('Person ID = ' + str(personID))
        #finally:
        #    print('lol')
        except:
            print("Failed adding person_id in dbshell.addPerson")
            personID = -1 #return a negative value so that the script knows that the query failed

        return personID
    
    def updatePersonStreamReltn(self, personID, streamID, reltn):
        sql = """SELECT * FROM meekbot.updatePersonStreamReltn({}, {}, '{}')"""
        print(sql.format(personID,streamID, reltn.upper()))    
    
        try:           
            with self.get_cursor() as cursor:
                cursor.execute(sql.format(personID,streamID, reltn.upper()))

        #finally:
            #print('lol')
        except:
            print("Failed updating relationship in dbshell.updatePersonStreamReltn")