
from __future__ import print_function
import httplib2
import os
import argparse
import re

from sys import argv
from apiclient import discovery
from apiclient import errors

from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from collections import Counter
# ...

import base64
import email
from email.mime.text import MIMEText



# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
#SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
SCOPES = 'https://mail.google.com/'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Gmail API Python Quickstart 2'

myEmailAddress = '4156120251@txt.att.net'

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None


"""Get Message with given ID.
"""
def GetMessage(service, user_id, msg_id):
  """Get a Message with given ID.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    msg_id: The ID of the Message required.

  Returns:
    A Message.
  """
  try:
    message = service.users().messages().get(userId=user_id, id=msg_id).execute()

    return message
  except errors.HttpError, error:
    print ('An error occurred: %s' % error)


def GetMimeMessage(service, user_id, msg_id):
  """Get a Message and use it to create a MIME Message.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    msg_id: The ID of the Message required.

  Returns:
    A MIME Message, consisting of data from Message.
  """
  try:
    message = service.users().messages().get(userId=user_id, id=msg_id,
                                             format='raw').execute()

    msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
    mime_msg = email.message_from_string(msg_str)

#    print("\n ****** MIME BODY ****** \n", mime_msg)

    return mime_msg
  except errors.HttpError, error:
    print ('An error occurred: %s' % error)


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials



def ListMessages(service, user, query=''):
  """Gets a list of messages.

  Args:
    service: Authorized Gmail API service instance.
    user: The email address of the account.
    query: String used to filter messages returned.
           Eg.- 'label:UNREAD' for unread Messages only.

  Returns:
    List of messages that match the criteria of the query. Note that the
    returned list contains Message IDs, you must use get with the
    appropriate id to get the details of a Message.
  """
  try:
    response = service.users().messages().list(userId=user, q=query).execute()
    messages = response['messages']

    while 'nextPageToken' in response:
      page_token = response['nextPageToken']
      response = service.users().messages().list(userId=user, q=query,
                                         pageToken=page_token).execute()
      messages.extend(response['messages'])
    return messages
  except errors.Http, error:
    print ("An error occurred: %s " % error)
    if error.resp.status == 401:
      # Credentials have been revoked.
      # TODO: Redirect the user to the authorization URL.
      raise NotImplementedError()


def ListMessagesWithLabels(service, user_id, label_ids=[], query=''):
  """List all Messages of the user's mailbox with label_ids applied.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    label_ids: Only return Messages with these labelIds applied.

  Returns:
    List of Messages that have all required Labels applied. Note that the
    returned list contains Message IDs, you must use get with the
    appropriate id to get the details of a Message.
  """
  try:
    response = service.users().messages().list(userId=user_id,
                                               labelIds=label_ids, q=query).execute()
    messages = []
    if 'messages' in response:
      messages.extend(response['messages'])

    while 'nextPageToken' in response:
      page_token = response['nextPageToken']
      response = service.users().messages().list(userId=user_id,
                                                 labelIds=label_ids,
                                                 q=query,
                                                 pageToken=page_token).execute()
      messages.extend(response['messages'])

    return messages
  except errors.HttpError, error:
    print ('An error occurred: %s' % error)


"""Get history from 'sinceHistoryId' to present.
"""

def ListHistory(service, user_id, start_history_id='1'):
  """List History of all changes to the user's mailbox.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    start_history_id: Only return Histories at or after start_history_id.

  Returns:
    A list of mailbox changes that occurred after the start_history_id.
  """
  try:
    history = (service.users().history().list(userId=user_id,
                                              startHistoryId=start_history_id)
               .execute())
    changes = history['history'] if 'history' in history else []
    while 'nextPageToken' in history:
      page_token = history['nextPageToken']
      history = (service.users().history().list(userId=user_id,
                                        startHistoryId=start_history_id,
                                        pageToken=page_token).execute())
      changes.extend(history['history'])

    return changes
  except errors.HttpError, error:
    print ('An error occurred: %s' % error)


"""Get a list of Labels from the user's mailbox.
"""
def ListLabels(service, user_id):
  """Get a list all labels in the user's mailbox.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.

  Returns:
    A list all Labels in the user's mailbox.
  """
  try:
    response = service.users().labels().list(userId=user_id).execute()
    labels = response['labels']
    for label in labels:
      print('Label id: %s ,\t\t  Label name: %s' % (label['id'], label['name']))
    return labels
  except errors.HttpError, error:
    print('An error occurred: %s' % error)


def SendMessage(service, user_id, message):
  """Send an email message.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    message: Message to be sent.

  Returns:
    Sent Message.
  """
  try:

    # Decoding all the fields inside the dict
    for key in message:
      message[key] = message[key].decode()

    message = (service.users().messages().send(userId=user_id, body=message)
               .execute())
    print( 'Message Id: %s' % message['id'] )
    return message

  except errors.HttpError as error:
    print('An error occurred: %s' % error)


def CreateMessage(sender, to, subject, message_text):
  """Create a message for an email.

  Args:
    sender: Email address of the sender.
    to: Email address of the receiver.
    subject: The subject of the email message.
    message_text: The text of the email message.

  Returns:
    An object containing a base64url encoded email object.
  """
  message = MIMEText(message_text)
  message['to'] = to
  message['from'] = sender
  message['subject'] = subject
  return {'raw': base64.urlsafe_b64encode( message.as_string().encode() )}



pclient = ['Elauwit', 'Black Box', 'VITAL','Level 10', 'Spencer', 'AST', 'Maintech', 'Granite']


def isPreferredClient(message_text):
  """" checks if the message contains a preferred client
  Args:
    message_text : the text of the email message

  Returns:
    boolean: true if yes, false if no preferred client is matched
  """
  ############# PREFERRED CLIENTS ############# 

  matchSuccess = False

  comboRegex = ""  ## combined regex of all preferred clients
  for pname in pclient:
    comboRegex = comboRegex + "(" + pname + ")|"

#  print("regex combination:", comboRegex)

  if len(pclient) > 0:
    combined = "(" + ")|(".join(pclient) + ")"
    if re.search(combined, message_text):
      print ("MATCH - PREFERRED CLIENT FOUND")
      matchSuccess = True
    else: 
      print("NO MATCH - PREFERRED CLIENT  \n\n") 
  else: 
    print("preferred list is zero in length")

  return matchSuccess


def sendMatchMsg(subject_text, msg_text, http):
      #### SENDING EMAIL 
    service = discovery.build('gmail', 'v1', http=http)
    sender = 'me'
    to = myEmailAddress
    subject = subject_text
    message_text = msg_text

    # Creating message
    message = CreateMessage( sender, to, subject, message_text )
    print("Sending Text Msg")   
    #print("Sending Text Msg:", message)
    
    # Sending message
    #SendMessage( service, "me", message )


############# ZIPCODES ############# 
# home base is fruitvale at 94601
zipcodes21mi = [94601,94606,94613,94602,94619,94610,94621,94502,94617,94501,94603,94604,94614,94620,94622,94623,94624,94649,94659,94660,94661,94666,94605,94612,94615,94611,94516,94609,94618,94577,94607,94662,94608,94546,94705,94563,94570,94575,94578,94704,94703,94579,94720,94702,94701,94712,94556,94709,94580,94710,94708,94130,94706,94707,94158,94124,94107,94105,94549,94111,94541,94104,94595,94540,94543,94557,94108,94530,94103,94102,94133,94119,94120,94125,94126,94137,94139,94140,94141,94142,94143,94144,94145,94146,94147,94151,94159,94160,94161,94163,94164,94172,94177,94188,94110,94134,94109,94545,94583,94115,94123,94526,94114,94804,94117,94597,94131,94596,94005,94805,94112,94802,94808,94542,94850,94544,94803,94118,94507,94083,94127,94014,94129,94807,94128,94552,94080,94553,94016,94523,94820,94528,94122,94116,94598,94401,94132,94121,94587,94801,94017,94806,94920,94564,94011,94404,94966,94015,94497,94030,94518,94547,94066,94582,94010,94506,94065,94403,94568,94522,94524,94527,94529,94555,94402,94572,94965,94588,94044,94520,94569,94974,94002,94525,94063,94964,94519,94925,94536,94521,94070,94976,94560,94942,94064,94537,94939,94517,94977,94901,94941]

#### FIELD NATION EMAILS ONLY ####
def isInZipcodeRangeFN(client_subject):
#  try:
    ##### string which is passed to test again zipcode array
    #sloc = "MANTECA CA 95336"
    zipcodeInRange = False

    if len(client_subject) > 0:
      sloc = client_subject
      #print("\n\nSloc :", sloc, ":")

      for sloc in sloc.split():
          if re.match(r'[0-9]{5}', sloc):
              zip = re.match(r'[0-9]{5}', sloc)
              target_zip = str(zip.group(0))
              print("EXTRACTED ZIP:", target_zip)
              for each_zip in zipcodes21mi:
                if int(each_zip) == int(target_zip):
                  zipcodeInRange = True

      print("----------------")

      return zipcodeInRange


 # except errors:
 #   print('An error occurred in isInZipcodeRange: %s' % error)


def handleFieldNationEmails(service, http, queryList):
    latesthistoryId = 0

    if len(queryList) > 0:
      for q in queryList:
        msg =  GetMessage(service, 'me', q['id'])
        currentHistoryId = msg['historyId']
        print("historyid ",currentHistoryId)
        if currentHistoryId > latesthistoryId:
          latesthistoryId = currentHistoryId


        print("------ ------ POTENTIAL CLIENT ------ ------ ")

        mime_msg = GetMimeMessage(service, 'me', q['id'])
        date = mime_msg['date']
        frm = mime_msg['from']
        subj = mime_msg['subject']

        print("MIME Date: ", date)
        print("MIME From: ", frm)
        print("MIME Subject: ", subj)
        print ("message ID" , mime_msg['historyId'], q['id'])

        # is zipcode in range, is TRUE, then parse message body and
        # test for preferred client
        if isInZipcodeRangeFN(subj): 
          print ("TARGET ZIPCODE MATCH")
        else: 
          print("NO TARGET ZIPCODE MATCH")

        ## parse message body - IS PREFERRED CLIENT?
        for part in mime_msg.walk():
          if part.get_content_type() == 'text/plain':
            rawtext = part.get_payload()
            if isPreferredClient(rawtext):
              sendMatchMsg(mime_msg['subject'], "", http)
          else:
            print("other multipart-mime - skipping")

        print ("\n")
    else: 
      print("Query Result list is Zero. Wait for next cycle")
    return latesthistoryId

def main():
    """Shows basic usage of the Gmail API.
    Creates a Gmail API service object and outputs a list of label names
    of the user's Gmail account.
    """
        # Label_1 : FN-NewWork
        # Label_3 : OF-NewWork
        # Label_2 : AssignedToYou

    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)

    print(" ------ ------ ------ ------ \n")
    queryList = ListMessagesWithLabels(service, 'me', ['Label_1'], 'is:unread newer_than:1d')
    print ('Field Nation Labeled Unread in last 1 hr: ', len(queryList), "\n")
    latestHistoryId = handleFieldNationEmails(service, http, queryList) 
    print("latest history id: " , latestHistoryId)
   

    print(" ------ ------ ------ ------ \n")


        # OFqueryList = ListMessagesWithLabels(service, 'me', ['Label_3'], 'is:unread newer_than:6h')
        # print ('OnForce Labeled  Unread in last hr :', len(OFqueryList))
        # print(" ------ ------ ------ ------ \n")


if __name__ == '__main__':
    main()


  
          ## TODO LIST
          ## retrieve old history id from file
          ## check each message in query List only if history id > previous history ID
              ## parse each message and push through filter criteria
              ## if pass, then forward on as a text message
          ## store this history id as the current history id and overwrite history id in file.

