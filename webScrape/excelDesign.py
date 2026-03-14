import pandas as pd
from email_listesi_duzeltilmis import emails

path = r""

df = pd.read_excel(path, engine="xlrd")

epostalar = (
    df["Eposta"]
    .dropna()
    .astype(str)
    .str.strip()
    .str.lower()
    .tolist()
)

# eski + yeni listeyi birleştir
tum_mailler = list(set(emails + epostalar))
tum_mailler = sorted(tum_mailler)

print(f"Toplam email sayısı: {len(tum_mailler)}")

# .py dosyasına kalıcı yaz
with open(r"", "w", encoding="utf-8") as f:
    f.write("emails = [\n")
    for mail in tum_mailler:
        f.write(f'    "{mail}",\n')
    f.write("]\n")

print("Liste dosyaya kaydedildi.")