import os
import sys
import sqlite3
import requests
from bs4 import BeautifulSoup

# Retrieve environment variables set in GitHub Secrets
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
MPSC_URL = "https://mpsc.gov.in"

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("Error: Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID secret!")
    sys.exit(1)

def init_db():
    """Create database table if it doesn't exist."""
    conn = sqlite3.connect("seen_notices.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link TEXT UNIQUE,
            title TEXT
        )
    """)
    conn.commit()
    conn.close()

def is_already_notified(link):
    """Check if link has already been sent to Telegram."""
    conn = sqlite3.connect("seen_notices.db")
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM notices WHERE link = ?", (link,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def save_notice(link, title):
    """Save notified link to database."""
    conn = sqlite3.connect("seen_notices.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO notices (link, title) VALUES (?, ?)", (link, title))
    conn.commit()
    conn.close()

def send_telegram_alert(title, link):
    """Send message to Telegram."""
    message = f"🚨 *New MPSC Notification* 🚨\n\n📌 *{title}*\n\n🔗 [View Details]({link})"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, data=payload)

def scrape_mpsc():
    """Scrape MPSC website for updates."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(MPSC_URL, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        links = soup.find_all("a", href=True)
        
        for a_tag in links:
            href = a_tag["href"].strip()
            title = a_tag.get_text(strip=True)
            
            if title and len(title) > 10 and (".pdf" in href.lower() or "advertisment" in href.lower()):
                full_url = href if href.startswith("http") else f"{MPSC_URL}/{href.lstrip('/')}"
                
                if not is_already_notified(full_url):
                    send_telegram_alert(title, full_url)
                    save_notice(full_url, title)
                    print(f"Alert sent for: {title}")
                    
    except Exception as e:
        print(f"Scraper error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_db()
    scrape_mpsc()
send_telegram_alert("Test Notification: Bot setup successful!", "https://mpsc.gov.in")

