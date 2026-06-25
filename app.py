import os
from flask import Flask, request
import openai
import requests
import traceback

app = Flask(__name__)

# আপনার এনভায়রনমেন্ট ভেরিয়েবল সেট করুন
openai.api_key = os.environ.get("OPENAI_API_KEY")
FACEBOOK_PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "my_secret_token_123")

@app.route("/", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode and token == VERIFY_TOKEN:
        return challenge, 200
    return "Hello World", 200

@app.route("/", methods=["POST"])
def webhook_event():
    body = request.get_json()
    if body.get("object") == "page":
        for entry in body.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                if messaging_event.get("message") and not messaging_event.get("message").get("is_echo"):
                    sender_id = messaging_event["sender"]["id"]
                    customer_message = messaging_event["message"].get("text")
                    
                    if customer_message:
                        try:
                            # OpenAI কল করা হচ্ছে
                            client = openai.OpenAI(api_key=openai.api_key)
                            response = client.chat.completions.create(
                                model="gpt-4o-mini", # সাশ্রয়ী মডেল
                                messages=[
                                    {"role": "system", "content": "You are a friendly customer service AI for infocardbd.com. Reply in Bengali or English."},
                                    {"role": "user", "content": customer_message}
                                ]
                            )
                            bot_reply = response.choices[0].message.content
                        except Exception as e:
                            traceback.print_exc()
                            bot_reply = "দুঃখিত, এখন সার্ভারে সমস্যা হচ্ছে।"
                        
                        # ফেসবুকে রিপ্লাই পাঠানো
                        url = f"https://graph.facebook.com/v21.0/me/messages?access_token={FACEBOOK_PAGE_ACCESS_TOKEN}"
                        requests.post(url, json={"recipient": {"id": sender_id}, "message": {"text": bot_reply}})
        return "EVENT_RECEIVED", 200
    return "Not Found", 404

if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", 5000)), host="0.0.0.0")
