# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

import firebase_admin
from firebase_admin import firestore

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

class CustomFallbackAction(Action):
    def name(self) -> Text:
        return "action_default_fallback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message("I'm sorry, I didn't understand. Can you please rephrase your message?")
        return []
    

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
            slot1= SlotSet("score", score)
            slot2= SlotSet("name", name)
            slot3= SlotSet("change", change)
            return [slot1,slot2,slot3]
        else:
            dispatcher.utter_message(text="Sorry an error occured in the server. Try again.")
            return []
    

class ActionScore1(Action):

    def name(self) -> Text:
        return "action_score1"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        id = tracker.sender_id
        data = fetchDoc(id)
        if (data):
            updateDoc(id, "score" , data.get("score") +1)
        else:
            dispatcher.utter_message("Error")
        
        return []
    
class ActionScore2(Action):
    def name(self) -> Text:
        return "action_score2"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        id = tracker.sender_id
        data = fetchDoc(id)
        if (data):
            updateDoc(id, "score" , data.get("score") +2)
        else:
            dispatcher.utter_message("Error")
        
        return []

class ActionScore3(Action):
    def name(self) -> Text:
        return "action_score3"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        id = tracker.sender_id
        data = fetchDoc(id)
        if (data):
            updateDoc(id, "score" , data.get("score") +3)
        else:
            dispatcher.utter_message("Error")
        
        
        return []
    
class ActionFetchScore(Action):
    def name(self) -> Text:
        return "action_fetchScore"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        id = tracker.sender_id
        data = fetchDoc(id)
        if (data):
            dispatcher.utter_message(f'Score is {data.get("score")}')
        else:
            dispatcher.utter_message("Error")
        
        return []