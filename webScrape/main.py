import requests
from bs4 import BeautifulSoup
import pandas as pd
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.add_font("ArialUnicode", fname=r"D:\\Github\\webScrape\\arial-unicode-ms-regular_ufonts.com.ttf", uni=True)        
pdf.set_font("ArialUnicode", size=10)

firma_listesi = []

# Kayapa OSB
url = "https://www.kayapaosb.org.tr/kayapa-osb-firma-listesi/"
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

table = soup.find("table")
rows = table.find_all("tr")[1:]

for row in rows:
    cols = row.find_all("td")
    if len(cols) >= 7:
        firma = {
            "Kaynak": "Kayapa OSB",
            "Firma Adı": cols[1].get_text(strip=True),
            "Üretim Alanı": cols[2].get_text(strip=True),
            "Telefon": cols[3].get_text(strip=True),
            "Faks": cols[4].get_text(strip=True),
            "Adres": cols[5].get_text(strip=True),
            "E-posta": cols[6].get_text(strip=True)
        }
        firma_listesi.append(firma)

# Kestel OSB
for i in range(1, 11):
    url = f"https://www.kosab.org.tr/FIRMALAR/{i}/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    firma_links = soup.find_all("a", class_="firmalar")

    for link in firma_links:
        firma_url = link.get("href")
        firma_name = link.text.strip()

        firma_response = requests.get(firma_url)
        firma_soup = BeautifulSoup(firma_response.text, "html.parser")

        table = firma_soup.find("table")
        rows = table.find_all("tr")

        firma_data = {"Kaynak": "Kestel OSB", "Firma Adı": firma_name}

        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                key = cols[0].get_text(strip=True)
                value = cols[1].get_text(strip=True)
                firma_data[key] = value

        firma_listesi.append(firma_data)

# NOSAB (tüm kategoriler)
categories = [
    "ambalaj","elektrik-elektronik","gida","insaat","matbaa","kaucuk","kimya-boya",
    "koltuk","lojistik","mobilya","makina","metal","otomotiv","plastik","tekstil","temizlik"
]

base_url = "https://www.nosab.org.tr"

for cat in categories:
    url = f"{base_url}/{cat}/tr"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    firma_links = [a["href"] for a in soup.select("ul.sayfaUlList li a")]

    for firma_url in firma_links:
        firma_response = requests.get(firma_url)
        firma_soup = BeautifulSoup(firma_response.text, "html.parser")

        firma_name = firma_soup.select_one(".firmaDetayAlan .col-sm-9").get_text(strip=True)
        urunler = [li.get_text(strip=True) for li in firma_soup.select(".firmaDetayIcerik ul li")]
        detaylar = [div.get_text(strip=True) for div in firma_soup.select(".firmaDetayAdres")]

        firma_data = {
            "Kaynak": f"NOSAB - {cat.upper()}",
            "Firma Adı": firma_name,
            "Ürünler": ", ".join(urunler),
            "Detaylar": ", ".join(detaylar)
        }
        firma_listesi.append(firma_data)

# Firma verilerini PDF'e yazdır
for firma in firma_listesi:
    pdf.set_font("ArialUnicode", size=10)
    pdf.cell(0, 8, f"Kaynak: {firma.get('Kaynak','')}", ln=True)
    pdf.cell(0, 8, f"Firma Adı: {firma.get('Firma Adı','')}", ln=True)
    
    for key, value in firma.items():
        if key not in ["Kaynak", "Firma Adı"]:
            pdf.multi_cell(0, 6, f"{key}: {value}")
    pdf.ln(4)

pdf_file_path = "D:/GitHub/webScrape/firmalar.pdf"
pdf.output(pdf_file_path)

print("PDF dosyası oluşturuldu:", pdf_file_path)
