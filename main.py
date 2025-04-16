import imaplib
import email
from email.header import decode_header
import os
import re
from dotenv import load_dotenv

# Load credentials
load_dotenv()
EMAIL = os.getenv("EMAIL_ADDRESS")
PASSWORD = os.getenv("EMAIL_PASSWORD")

# Keywords to detect importance
KEYWORDS = ["invoice", "meeting", "urgent", "deadline", "payment", "project", "schedule"]

def clean_text(text):
    return re.sub(r'\s+', ' ', text.strip())

def get_summary(body, max_sentences=2):
    sentences = re.split(r'(?<=[.!?]) +', body)
    important_sentences = [s for s in sentences if len(s.split()) > 3]
    return ' '.join(important_sentences[:max_sentences])

def score_email(body, keywords):
    score = 0
    for keyword in keywords:
        score += body.lower().count(keyword.lower())
    return score

def fetch_emails(n=20):
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    imap.login(EMAIL, PASSWORD)
    imap.select("inbox")

    status, messages = imap.search(None, 'ALL')
    email_ids = messages[0].split()
    emails = []

    for i in email_ids[-n:]:  # last N emails
        _, msg_data = imap.fetch(i, "(RFC822)")
        for part in msg_data:
            if isinstance(part, tuple):
                msg = email.message_from_bytes(part[1])
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or "utf-8", errors="ignore")

                from_ = msg.get("From")

                # Get plain text email body
                body = ""
                if msg.is_multipart():
                    for subpart in msg.walk():
                        if subpart.get_content_type() == "text/plain" and "attachment" not in str(subpart.get("Content-Disposition", "")):
                            try:
                                body = subpart.get_payload(decode=True).decode()
                                break
                            except:
                                continue
                else:
                    try:
                        body = msg.get_payload(decode=True).decode()
                    except:
                        continue

                clean_body = clean_text(body)
                summary = get_summary(clean_body)
                score = score_email(clean_body, KEYWORDS)

                emails.append({
                    "from": from_,
                    "subject": subject,
                    "summary": summary,
                    "score": score
                })

    imap.logout()
    return sorted(emails, key=lambda x: x["score"], reverse=True)

if __name__ == "__main__":
    top_emails = fetch_emails(20)

    print("\n🔍 Top Relevant Emails:\n")
    for email_data in top_emails[:5]:
        print(f"From: {email_data['from']}")
        print(f"Subject: {email_data['subject']}")
        print(f"Summary: {email_data['summary']}")
        print(f"Keyword Score: {email_data['score']}")
        print("-" * 50)

