from typing import Dict, Text, Any, List, Union

from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction


class ValidateEventForm(FormValidationAction):
    """Example of a form validation action."""

    def name(self) -> Text:
        return "validate_event_form"

    @staticmethod
    def local_person_db() -> List[Text]:
        """Database of supported cuisines."""

        return [
            "本地人",
            "外地人",
        ]

    def validate_local_person(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validate cuisine value."""

        if value.lower() in self.local_person_db():
            # validation succeeded, set the value of the "cuisine" slot to value
            if value.lower() == "本地人":
                return {"local_person": value, "book": ""}
            else:
                return {"local_person": value}
        else:
            dispatcher.utter_message(template="utter_wrong_local_person")
            # validation failed, set this slot to None, meaning the
            # user will be asked for the slot again
            return {"local_person": None}

    def validate_person(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validate num_people value."""

        if value.lower() in ["本人", "委托人"]:
            return {"person": value}
        else:
            dispatcher.utter_message(template="utter_wrong_person")
            # validation failed, set slot to None
            return {"person": None}

    def validate_book(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validate outdoor_seating value."""

        if value.lower() in ["居住证", "户口本"]:
            return {"book": value}
        else:
            dispatcher.utter_message(template="utter_wrong_book")
            # validation failed, set slot to None
            return {"book": None}

    def validate_country_person(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validate outdoor_seating value."""

        if value.lower() in ["中国人", "外国人"]:
            return {"country_person": value}
        else:
            dispatcher.utter_message(template="utter_wrong_country_person")
            # validation failed, set slot to None
            return {"country_person": None}
