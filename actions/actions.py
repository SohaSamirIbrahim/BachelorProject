# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, Restarted, UserUtteranceReverted, UserUttered, ActionExecuted

import firebase_admin
from firebase_admin import firestore

import os
from dotenv import load_dotenv

load_dotenv()

import requests


def newDoc (senderid, doc):
    db = firestore.client()
    collection_ref = db.collection('test')
    doc_ref = collection_ref.document(senderid)
    doc_ref.set(doc)

def fetchDoc(senderid):
    db = firestore.client()
    doc_ref = db.collection("test").document(senderid)
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
        return data
        
def updateDoc(senderid, field, value):
    db = firestore.client()
    doc_ref = db.collection("test").document(senderid)
    doc_ref.update({field: value})

class ActionRestart(Action):

  def name(self) -> Text:
      return "action_restart"

  async def run(self, dispatcher, 
            tracker: Tracker, 
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message("Conversation was restarted.")
        return [Restarted()]

class CustomFallbackAction(Action):
    def name(self) -> Text:
        return "action_default_fallback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message("I'm sorry, I didn't understand. Can you please rephrase your message?")
        return [UserUtteranceReverted()]

import requests


class ActionInitiateConversation(Action):
    def name(self) -> Text:
        return "action_initiate_conversation"

    def run(self, dispatcher: CollectingDispatcher, 
            tracker: Tracker, 
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        access_token = os.environ.get("FB_Page_Access_Token")
        user_id = "USER_FACEBOOK_MESSENGER_ID"
        message = "Hello, this is a message from the bot!"

        url = f"https://graph.facebook.com/v13.0/me/messages?access_token={access_token}"
        headers = {"Content-Type": "application/json"}

        payload = {
            "recipient": {"id": user_id},
            "message": {"text": message}
        }

        response = requests.post(url, headers=headers, json=payload)

        # # Retrieve the user's Facebook Messenger ID
        # user_id = tracker.sender_id

        # # Create the message payload
        # message = Text(text="Hello, this is your chatbot!")

        # # Create the Messenger client
        # client = MessengerClient(page_access_token=os.environ.get("FB_Page_Access_Token"))

        # # Send the message using the Messenger client
        # response = client.send(user_id=user_id, message=message)

        # # Handle the response
        # if response["success"]:
        #     dispatcher.utter_message(text="Message sent successfully!")
        # else:
        #     dispatcher.utter_message(text="Failed to send message.")

        return []

class ActionStart(Action):

    def name(self) -> Text:
        return "action_start"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # id = tracker.sender_id
        id = os.environ.get("TestID")
        data = fetchDoc(id)

        if(data) :
            name = data.get("name")
            change = data.get("change")
            score = data.get("score")
            slot1= SlotSet("score", score)
            slot2= SlotSet("name", name)
            slot3= SlotSet("change", change)
            if(change == 'sleep'):
                slot4 = SlotSet("sleep", True)
            else:
                slot4 = SlotSet("sleep", False)
            return [slot1,slot2,slot3,slot4]

        else:
            dispatcher.utter_message(text="Sorry an error occured in the server. Try again.")
            return []
        
class ActionScoreAdd(Action):
    def name(self) -> Text:
        return "action_scoreAdd"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        id = os.environ.get("TestID")
        value = tracker.get_slot("value")
        if (value == 0):
            return[] 
        data = fetchDoc(id)
        if (data):
            if(value == 1):
                updateDoc(id, "score" , data.get("score") +1)
            if(value == 2):
                updateDoc(id, "score" , data.get("score") +2)
            if(value == 3):
                updateDoc(id, "score" , data.get("score") +3)

        else:
            dispatcher.utter_message("Error")
        
        slot = SlotSet("value", 0)
        return [slot]
    
    
class ActionScoreCheck(Action):
    def name(self) -> Text:
        return "action_scoreCheck"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        id = os.environ.get("TestID")
        data = fetchDoc(id)
        if (data):
            score = data.get("score")
            change = data.get("change")
            if((score> 3 and change == "sleep") or (score > 5 and change == "activity") ):
                dataParse = {
                "intent": {
                    "name": "general",
                    "confidence": 1.0,
                    }
                }
                return [ActionExecuted("action_listen"),UserUttered(text="/general", parse_data=dataParse),]
            else:
                dataParse = {
                "intent": {
                    "name": "goodbye",
                    "confidence": 1.0,
                    }
                }
                return [ActionExecuted("action_listen"),UserUttered(text="/goodbye", parse_data=dataParse),]
        else:
            dispatcher.utter_message("Error")
        
        return []
    
class ActionScoreFinal(Action):
    def name(self) -> Text:
        return "action_scoreFinal"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        id = os.environ.get("TestID")
        data = fetchDoc(id)
        if (data):
            score = data.get("score")
            if(score > 8):
                # CALL API OF THERAPY BOT
                dataParse = {
                "intent": {
                    "name": "therapy",
                    "confidence": 1.0,
                    }
                }
                return [ActionExecuted("action_listen"),UserUttered(text="/therapy", parse_data=dataParse),]

            else:
                dataParse = {
                "intent": {
                    "name": "goodbye",
                    "confidence": 1.0,
                    }
                }
                return [ActionExecuted("action_listen"),UserUttered(text="/goodbye", parse_data=dataParse),]
        return []
