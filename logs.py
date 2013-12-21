import os
import psycopg2
import re
import db_config

IRC_USER_MESSAGE = 'irc_user_message'
CHANNEL_NOTIFICATION = 'channel_notification'
SAXJAX_NOTIFICATION = 'saxjax_notification'
SAXJAX_USER_MESSAGE = 'saxjax_user_message'

time_pattern = re.compile( "[0-9]{2}:[0-9]{2}:[0-9]{2}")
irc_user_pattern = re.compile("(?<=\<).*?(?=\>)")
saxjax_user_message_user_pattern = re.compile("(?<=\(C\)\s\[).*?(?=\])")
saxjax_notification_user_pattern = re.compile("(?<=\(C\)\s\*).*?(?=\s)")
channel_notification_user_pattern = re.compile("(?<=\s\*\*).*?(?=\s)")

def getDate(filename):
    return filename.replace('logs/',"").replace('_cemetech', '')

def getTime(line):
    try:
        return time_pattern.search(line).group(0)
    except:
        return None

def getType(line):
    if '] <saxjax> (C) [' in line:
        return SAXJAX_USER_MESSAGE
    elif '] <saxjax> (C) *' in line:
            return SAXJAX_NOTIFICATION
    elif '] **' in line:
        return CHANNEL_NOTIFICATION
    else:
        return IRC_USER_MESSAGE

def getUser(line):
    if line is None or line is '':
        return None

    try:
        type = getType(line)

        if type is IRC_USER_MESSAGE:
            return irc_user_pattern.search(line).group(0)
        elif type is SAXJAX_USER_MESSAGE:
            return saxjax_user_message_user_pattern.search(line).group(0)
        elif type is SAXJAX_NOTIFICATION:
            return saxjax_notification_user_pattern.search(line).group(0)
        elif type is CHANNEL_NOTIFICATION:
            return channel_notification_user_pattern.search(line).group(0)

    except:
            print "Couldn't get user for line:", line
            return None

def getMessage(line):
    type = getType(line)
    user = getUser(line)

    prefix = "[" + getTime(line) + "] "

    if type is IRC_USER_MESSAGE:
        prefix += "<" + user + ">"
    elif type is SAXJAX_USER_MESSAGE:
        prefix += '<saxjax> (C) [' + user + "]"
    elif type is SAXJAX_NOTIFICATION:
        prefix += '<saxjax> (C) *'+user
    elif type is CHANNEL_NOTIFICATION:
        prefix += '**' + user

    prefix += ' '

    return line.replace(prefix,"")

def getInsertSql(filename, line):
    sql = "INSERT INTO message (m_time, m_type, m_sender, m_message) VALUES ( %s, %s, %s, %s )"

    timestamp = getDate(filename + " " + getTime(line))
    data = (timestamp, getType(line), getUser(line), getMessage(line))

    return [sql, data]

CONN = psycopg2.connect(host=db_config.ENDPOINT, port=db_config.PORT, user=db_config.USER, password=db_config.PASSWORD, database=db_config.DB)

def executeInsert( sql, data ):
    cur = CONN.cursor();
    cur.execute(sql, data)
    CONN.commit()
    cur.close()


for filename in os.listdir("./logs"):
    f = open('./logs/'+filename)
    for line in f:
        line = line.replace("\n","")

        if line is None or line is '':
            pass
        else:
            print line
            print '\t', getTime(line)
            print '\t', getType(line)
            print '\t', getUser(line)
            print '\t', getMessage(line)

            sql = getInsertSql(filename, line)
            print '\t', sql
            executeInsert(sql[0], sql[1])

CONN.close()

