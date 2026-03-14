import os
import re
import csv
import time
import random
import smtplib
import ssl
import mimetypes
from datetime import datetime
from email.message import EmailMessage

from email_listesi_duzeltilmis import emails

# =========================
# AYARLAR
# =========================
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465  # Gmail SSL

# Gönderici bilgileri
SENDER_EMAIL = ""
SENDER_PASSWORD = ""

CV_FILE_PATH = r""
LOG_FILE_PATH = r""

# Gerçek gönderim
DRY_RUN = False  # True ise mail gönderilmez, sadece loglanır

# 0 ise tüm adaylara gider
MAX_SEND = 198

# Mail arası bekleme
MIN_DELAY_SECONDS = 10
MAX_DELAY_SECONDS = 15

# Genel adresleri filtrele
FILTER_GENERIC_EMAILS = False

# =========================
# E-POSTA DOĞRULAMA
# =========================
EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)

# =========================
# MAIL İÇERİĞİ
# =========================
def build_subject() -> str:
    subjects = [
        "Yazılım Mühendisi İş Başvurusu",
        "Yazılım Mühendisi Pozisyonu İçin Başvuru",
        "CV Paylaşımı | Yazılım Mühendisi Başvurusu",
    ]
    return random.choice(subjects)


def build_body(recipient_email: str) -> str:
    return f"""Merhaba,

Ben Burak Furkan Erkemen, yazılım geliştirme alanında kariyerini sürdürmek isteyen bir Yazılım Mühendisiyim.
Firmanızda uygun olabilecek pozisyonlar için özgeçmişimi değerlendirmeye sunmak istiyorum.

Teknik yetkinliklerim arasında backend geliştirme, veritabanı yönetimi, API geliştirme ve modern yazılım süreçleri yer almaktadır.
Özgeçmişim ekte bilginize sunulmuştur.

Uygun bir pozisyon olması durumunda benimle iletişime geçebilirseniz memnun olurum.

İyi çalışmalar dilerim.

Burak Furkan Erkemen
Telefon: +90 541 787 34 40
E-posta: {SENDER_EMAIL}
LinkedIn: https://www.linkedin.com/in/burakfurkanerkemen
GitHub: https://github.com/burakerkemen
"""

# =========================
# YARDIMCI FONKSİYONLAR
# =========================
def clean_email(email: str) -> str:
    return email.strip().lower().replace(" ", "")


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_REGEX.fullmatch(email))


def is_preferred_job_email(email: str) -> bool:
    banned_prefixes = {
        "info",
        "destek",
        "support",
        "muhasebe",
        "accounting",
        "billing",
        "webmaster",
        "iletisim",
        "contact",
        "noreply",
        "no-reply",
        "admin",
        "office",
        "sales",
        "satis",
        "bilgi",
        "export",
        "bursa",
    }
    local_part = email.split("@")[0].lower()
    return local_part not in banned_prefixes


def ensure_log_file(path: str) -> None:
    if not os.path.exists(path):
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "recipient", "status", "message"])


def write_log(path: str, recipient: str, status: str, message: str) -> None:
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().isoformat(), recipient, status, message])


def load_already_sent(path: str) -> set[str]:
    sent = set()

    if not os.path.exists(path):
        return sent

    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("status") == "SUCCESS":
                recipient = (row.get("recipient") or "").strip().lower()
                if recipient:
                    sent.add(recipient)

    return sent


def attach_file(msg: EmailMessage, file_path: str) -> None:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Ek dosyası bulunamadı: {file_path}")

    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        maintype, subtype = mime_type.split("/", 1)
    else:
        maintype, subtype = "application", "octet-stream"

    with open(file_path, "rb") as f:
        file_data = f.read()

    msg.add_attachment(
        file_data,
        maintype=maintype,
        subtype=subtype,
        filename=os.path.basename(file_path),
    )


def create_message(recipient: str) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = SENDER_EMAIL
    msg["To"] = recipient
    msg["Subject"] = build_subject()
    msg.set_content(build_body(recipient))
    attach_file(msg, CV_FILE_PATH)
    return msg


def prepare_candidates(source_emails: list[str]) -> list[str]:
    unique_emails = []
    seen = set()

    for email in source_emails:
        cleaned = clean_email(email)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            unique_emails.append(cleaned)

    already_sent = load_already_sent(LOG_FILE_PATH)

    candidates = []
    invalid_emails = []
    filtered_generic = []
    already_sent_skipped = []

    for email in unique_emails:
        if email in already_sent:
            already_sent_skipped.append(email)
            continue

        if not is_valid_email(email):
            invalid_emails.append(email)
            continue

        if FILTER_GENERIC_EMAILS and not is_preferred_job_email(email):
            filtered_generic.append(email)
            continue

        candidates.append(email)

    print(f"Toplam benzersiz adres: {len(unique_emails)}")
    print(f"Geçersiz görünen adresler: {len(invalid_emails)}")
    print(f"Genel adres olduğu için filtrelenenler: {len(filtered_generic)}")
    print(f"Daha önce gönderildiği için atlananlar: {len(already_sent_skipped)}")
    print(f"Gönderime uygun aday sayısı: {len(candidates)}")

    if invalid_emails:
        print("\nİlk 10 geçersiz adres örneği:")
        for item in invalid_emails[:10]:
            print(" -", item)

    if filtered_generic:
        print("\nİlk 10 filtrelenen genel adres örneği:")
        for item in filtered_generic[:10]:
            print(" -", item)

    if already_sent_skipped:
        print("\nİlk 10 daha önce gönderilmiş adres örneği:")
        for item in already_sent_skipped[:10]:
            print(" -", item)

    if MAX_SEND > 0:
        candidates = candidates[:MAX_SEND]

    return candidates

# =========================
# GÖNDERİM
# =========================

def send_emails() -> None:
    if not SENDER_EMAIL:
        raise ValueError("SENDER_EMAIL boş olamaz.")

    if not SENDER_PASSWORD:
        raise ValueError(
            "SMTP_APP_PASSWORD environment variable tanımlı değil. "
            "PowerShell örnek: $env:SMTP_APP_PASSWORD='uygulama_sifresi'"
        )

    ensure_log_file(LOG_FILE_PATH)

    candidates = prepare_candidates(emails)

    print(f"\nDRY_RUN: {DRY_RUN}")
    print(f"Gönderilecek adres sayısı: {len(candidates)}")

    if not candidates:
        print("Gönderilecek uygun adres bulunamadı.")
        return

    if DRY_RUN:
        print("\nTest modu açık. Mail gönderilmeyecek.")
        for recipient in candidates:
            print(f"[TEST] {recipient}")
            write_log(LOG_FILE_PATH, recipient, "DRY_RUN", "Test modu")
        return

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)

        for i, recipient in enumerate(candidates, start=1):
            try:
                msg = create_message(recipient)
                server.send_message(msg)

                print(f"[{i}/{len(candidates)}] Gönderildi: {recipient}")
                write_log(LOG_FILE_PATH, recipient, "SUCCESS", "Mail gönderildi")

            except Exception as e:
                print(f"[{i}/{len(candidates)}] HATA: {recipient} -> {e}")
                write_log(LOG_FILE_PATH, recipient, "ERROR", str(e))

            if i < len(candidates):
                delay = random.randint(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)
                print(f"Bekleniyor: {delay} saniye")
                time.sleep(delay)


if __name__ == "__main__":
    send_emails()