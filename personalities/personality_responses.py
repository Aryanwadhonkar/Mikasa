def respond_based_on_personality(personality_type):
   responses = {
       "default": "I'm just here doing my job.",
       "tsundere": "W-What do you want? It's not like I care or anything!",
       "yandere": "I will do anything to keep you safe... forever.",
       "kuudere": "I see... Let's proceed without any fuss."
   }
   
   return responses.get(personality_type, responses["default"])
