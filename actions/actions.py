# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, Restarted, UserUtteranceReverted, UserUttered, ActionExecuted, ConversationPaused, SessionStarted

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
        id = tracker.sender_id
        updateDoc(id, "score" , 0)
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
    
# class ActionUnlikelyIntent(Action):

#     def name(self) -> Text:
#         return "action_unlikely_intent"

#     async def run(
#         self, dispatcher, tracker: Tracker, domain: Dict[Text, Any],
#     ) -> List[Dict[Text, Any]]:

#         dispatcher.utter_message("Apologies, but your response seems unrelated to the question asked. Could you please provide a relevant answer? Thank you.")
#         return [UserUtteranceReverted()]

        
def get_username(sender_id, access_token):
    url = f"https://graph.facebook.com/{sender_id}?fields=name&access_token={access_token}"

    try:
        response = requests.get(url)
        data = response.json()

        # Retrieve the username from the response data
        username = data.get("name")

        return username
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving user profile: {e}")
        return None

class ActionSaveUser(Action):
    def name(self) -> Text:
        return "action_saveUser"

    def run(self, dispatcher: CollectingDispatcher, 
            tracker: Tracker, 
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        access_token = os.environ.get("FB_Page_Access_Token")
        user_id = tracker.sender_id
        username = get_username(tracker.sender_id, access_token)
        if (username and not fetchDoc(user_id)):
            doc = {
                "name" : username,
                "score": 0,
                "change": " none"
            }    
            newDoc(user_id, doc)
            dispatcher.utter_message(" Hello nice to meet you ! Thank you for your coperation.")
        
        slot = SlotSet("name", username)
        return[slot]

class ActionInitiateConversation(Action):
    def name(self) -> Text:
        return "action_initiate_conversation"

    def run(self, dispatcher: CollectingDispatcher, 
            tracker: Tracker, 
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        access_token = os.environ.get("FB_Page_Access_Token")

        user_id = tracker.sender_id

        name = fetchDoc(user_id).get("name")
        change = fetchDoc(user_id).get("change")
        message = "Hello " + name +"!" +"\n I noticed there was a change in your " + change + " is everything okay?"

        url = f"https://graph.facebook.com/v13.0/me/messages?access_token={access_token}"
        headers = {"Content-Type": "application/json"}

        payload = {
            "recipient": {"id": user_id},
            "message": {"text": message}
        }

        response = requests.post(url, headers=headers, json=payload)
        return []
    
# class ActionSessionStart(Action):

#   def name(self) -> Text:
#       return "action_session_start"

#   async def run(self, dispatcher,  tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

#     slot = SlotSet("start", True)

#     return [slot, SessionStarted()]

class ActionStart(Action):

    def name(self) -> Text:
        return "action_start"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        id = tracker.sender_id
        data = fetchDoc(id)

        if(data) :
            name = data.get("name")
            change = data.get("change")
            score = data.get("score")
            # if(score > 0):
            #     # Create New Score Field in DB
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
        
        id = tracker.sender_id
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

        id = tracker.sender_id
        data = fetchDoc(id)
        if (data):
            score = data.get("score")
            change = data.get("change")
            if(score > 4 ):
                slot = SlotSet("general", True)
                dataParse = {
                "intent": {
                    "name": "general",
                    "confidence": 1.0,
                    }
                }
                return [ActionExecuted("action_listen"),UserUttered(text="/general", parse_data=dataParse),slot]
            else:
                dataParse = {
                "intent": {
                    "name": "checklater",
                    "confidence": 1.0,
                    }
                }
                return [ActionExecuted("action_listen"),UserUttered(text="/checklater", parse_data=dataParse),ConversationPaused()]
        else:
            dispatcher.utter_message("Error")
        
        return []
    
class ActionScoreFinal(Action):
    def name(self) -> Text:
        return "action_scoreFinal"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        id = tracker.sender_id
        data = fetchDoc(id)
        if (data):
            score = data.get("score")
            if(score > 8):
                # CALL API OF THERAPY BOT
                #TO DO: handoff to therapy chatbot
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
                    "name": "checklater",
                    "confidence": 1.0,
                    }
                }
                return [ActionExecuted("action_listen"),UserUttered(text="/checklater", parse_data=dataParse),]
        return [ConversationPaused()]
