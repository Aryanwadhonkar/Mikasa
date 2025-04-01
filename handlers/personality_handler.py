from personalities.personality_responses import respond_based_on_personality

def set_personality(update, context):
   if len(context.args) == 0 or context.args[0] not in PERSONALITIES.keys():
       update.message.reply_text(f"Available personalities: {', '.join(PERSONALITIES.keys())}")
       return
   
   personality_type = context.args[0]
   
   response = respond_based_on_personality(personality_type)
   
   update.message.reply_text(response)
