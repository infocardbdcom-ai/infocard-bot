import os
from flask import Flask, request
import google.generativeai as genai
import requests
import traceback

app = Flask(__name__)

FACEBOOK_PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "my_secret_token_123")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# ১. প্রথমে কনফিগার করুন
genai.configure(api_key=GEMINI_API_KEY)

# ২. তারপর মডেল সেট করুন (একটি মাত্র মডেল থাকবে)
model = genai.GenerativeModel("gemini-1.5-flash")

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
                            prompt = f"You are a customer service AI for infocardbd.com. Reply in short and friendly manner in the customer's language (Bengali/English). Customer asks: {customer_message}"
                            response = model.generate_content(prompt)
                            bot_reply = response.text
                        except Exception as e:
                            print("ERROR DETECTED:")
                            traceback.print_exc() # এটি লগে আসল ভুলটি লিখে দেবে
                            bot_reply = "দুঃখিত, একটু কারিগরি সমস্যা হচ্ছে।"
                        
                        # Send reply
                        url = f"https://graph.facebook.com/v21.0/me/messages?access_token={FACEBOOK_PAGE_ACCESS_TOKEN}"
                        requests.post(url, json={"recipient": {"id": sender_id}, "message": {"text": bot_reply}})
        return "EVENT_RECEIVED", 200
    return "Not Found", 404

if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", 5000)), host="0.0.0.0")
