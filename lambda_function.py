import boto3
dynamodb = boto3.client('dynamodb')
import datetime
import pytz

TABLE_NAME = "KingOfTheRoom"

def lambda_handler(event, context):
    """Skill entrypoint"""
    request_type = event['request']['type']
    uid = event['session']['user']['userId']

    if request_type == "LaunchRequest":
        return handle_launch(event)
    elif request_type == "IntentRequest":
        return handle_intent(event, uid)
    elif request_type == "SessionEndedRequest":
        return handle_end(event)

def handle_launch(event):
    """Handles skill launch"""
    return build_response("welcome to king of the room. you may either ask who is king or make somebody else king.", "WELCOME", False)

def handle_intent(event, uid):
    """Handles skill intents"""
    intentType = event['request']['intent']['name']

    if intentType == "GetKing":
        return handle_get_king(uid)

    elif intentType == "SetKing":
        king = event['request']['intent']['slots']['Name']['value']
        return handle_set_king(uid, king)

    elif intentType == "AMAZON.CancelIntent":
        return handle_end()

    elif intentType == "AMAZON.HelpIntent":
        return build_response("ask who is king or make somebody else king", "HELP", False)

    elif intentType == "AMAZON.FallbackIntent":
        return build_response("ask who is king or make somebody else king", "HELP", False)

def handle_end(event):
    """Handles session end"""
    return build_response("goodbye", "GOODBYE", True)

def build_response(speech_text, card_text, should_end_session):
    """Alexa response"""
    
    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": speech_text
                
            },
            "card": {
                "content": card_text,
                "title": "ANNOUNCEMENT",
                "type": "Simple"
                
            },
            "reprompt": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": ""
                    
                }
                
            },
            "shouldEndSession": should_end_session
            
        },
        "sessionAttributes": {}
    }

def handle_get_king(uid):
    """Get current king"""
    
    try:
        item = dynamodb.get_item(TableName=TABLE_NAME, Key={'NameId':{'S':uid}})
        curr_king = item['Item']['CurrKing']['S']
        old_king = item['Item']['OldKing']['S']
        duration = formatDuration(datetime.timedelta(seconds=int(datetime.datetime.now().timestamp()) - int(item['Item']['StartTime']['N'])))
        start_date = datetime.datetime.fromtimestamp(
            int(item['Item']['StartTime']['N']),
            pytz.timezone('America/New_York')
        ).strftime("%B %d, %Y at %I:%M %p")
        return build_response(f"the reigning king is {curr_king} who has been on the throne for {duration} since usurping {old_king} on {start_date}", "get", False)
    except KeyError:
        return build_response("the throne is empty", "INQUIRY", False)

def handle_set_king(uid, king):
    """Set new king"""
    
    try:
        old_item = dynamodb.get_item(TableName=TABLE_NAME, Key={'NameId':{'S':uid}})
        old_king = old_item['Item']['CurrKing']['S']

        if king == old_king:
            return build_response(f"{old_king} is already in power", "INQUIRY", False)
        
    except KeyError:
        old_king = "nobody"
    
    dynamodb.put_item(TableName=TABLE_NAME,Item={
        'NameId':{'S':uid},
        'CurrKing':{'S':king},
        'OldKing':{'S':old_king},
        'StartTime':{'N':str(int(datetime.datetime.now().timestamp()))},
    })
    
    return build_response(f"{king} is now king", "USURP", False)

def formatDuration(dur):
    """Convert timedelta to duration string"""
    hours, minutes = divmod(dur.seconds, 3600)
    minutes, seconds = divmod(minutes, 60)
    return f"{dur.days} {pluralize(dur.days, 'day')} {hours} {pluralize(hours, 'hour')} {minutes} {pluralize(minutes, 'minute')} and {seconds} {pluralize(seconds, 'second')}"

def pluralize(n, s):
    """Naive pluralization"""
    return s+"s" if n != 1 else s
