import os
from dotenv import load_dotenv

load_dotenv()

# Upstage
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
UPSTAGE_CHAT_URL = "https://api.upstage.ai/v1/chat/completions"
UPSTAGE_MODEL = "solar-pro3"

# Airtable
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_PRESCRIPTIONS_TABLE = os.getenv("AIRTABLE_PRESCRIPTIONS_TABLE", "Prescriptions")
AIRTABLE_MEDICATIONS_TABLE = os.getenv("AIRTABLE_MEDICATIONS_TABLE", "Medications")
AIRTABLE_CHAT_TABLE = os.getenv("AIRTABLE_CHAT_TABLE", "Chat_Sessions")
AIRTABLE_ANALYSIS_TABLE = os.getenv("AIRTABLE_ANALYSIS_TABLE", "Analysis_Reports")

AIRTABLE_BASE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}"
