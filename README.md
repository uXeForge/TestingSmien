# 🔔 Smeny.cz – Monitor voľných smien

Automatický sledovač voľných smien na [smeny.cz](https://smeny.cz).  
Skript v pravidelných intervaloch kontroluje rozvrh zamestnanca na najbližších 30 dní a v prípade, že sa objaví nová voľná smena (označená akciou `ATTEND`), okamžite odošle notifikáciu na Telegram.

---

## ⚙️ Setup – Krok za krokom

### 1. 📱 Nastavenie Telegram Bota
Notifikácie chodia cez súkromného Telegram bota. Jeho vytvorenie trvá 1 minútu:

1. V aplikácii Telegram vyhľadaj používateľa **@BotFather** (oficiálny bot s modrou fajočkou).
2. Spusti ho stlačením **Start** (alebo napíš `/start`).
3. Pošli správu `/newbot`.
4. Zadaj viditeľný názov bota (napr. `Smeny Monitor`).
5. Zadaj prezývku bota (username), ktorá **musí** končiť slovom `bot` (napr. `kika_smeny_bot`).
6. BotFather ti odpovie správou, ktorá obsahuje **Token** na prístup k API.
   * *Príklad tokenu:* `8765779374:AAHst-JuNkJdE0mrr2WFZOT9z1JW6Z9KPCw`
   * **Dôležité:** Skopíruj si ho celý bez vynechania akéhokoľvek znaku na konci!
7. Vyhľadaj v Telegrame tvojho novovytvoreného bota podľa jeho prezývky (napr. `@kika_smeny_bot`) a stlač tlačidlo **Start / Spustiť** na spodku obrazovky. *(Bez tohto kroku ti bot nebude môcť poslať správu!)*

---

### 2. 🆔 Získanie tvojho Chat ID
Každý používateľ v Telegrame má unikátne číselné ID. Skript ho potrebuje, aby vedel, komu má správu doručiť:

#### Rýchla možnosť A (odporúčaná):
1. Vyhľadaj v Telegrame bota **@userinfobot** a klikni na **Start**.
2. Bot ti ihneď odpovie. Skopíruj si číslo z riadku **Id:** (napr. `8933335367`).

#### Záložná možnosť B (cez prehliadač):
Ak možnosť A nefunguje alebo chceš overiť, že ťa tvoj bot reálne vidí:
1. Otvor v prehliadači nasledujúcu adresu (nahraď `<BOT_TOKEN>` tvojím skutočným tokenom):
   ```
   https://api.telegram.org/bot<BOT_TOKEN>/getUpdates
   ```
2. V zobrazenom JSON texte vyhľadaj časť `"chat"` a v nej riadok `"id": XXXXXXXXX` (napr. `"id": 8933335367`).

---

### 3. 💻 Lokálne testovanie (na tvojom PC)
Pred nasadením na GitHub je rozumné skript otestovať lokálne.

#### A. Inštalácia Pythonu (ak ho nemáš):
Ak nemáš na počítači Python, otvor **PowerShell** a spusti:
```powershell
winget install Python.Python.3.12
```
Po dokončení inštalácie **reštartuj PowerShell** (zatvor ho a znova otvor).

#### B. Inštalácia závislostí:
V priečinku projektu spusti:
```powershell
pip install requests
```

#### C. Spustenie testu:
1. V priečinku projektu nájdeš súbor `run_test.cmd`.
2. Klikni naň pravým tlačidlom -> *Upraviť* (Edit) a doplň svoje reálne prihlasovacie údaje a Telegram tokeny.
3. Dvakrát klikni na `run_test.cmd` pre spustenie.
4. Skript beží v **TEST_SEND** režime. To znamená, že aj keď nie sú žiadne voľné smeny, nasimuluje uvoľnenie prvej nájdenej smeny a odošle ti ju na Telegram. Týmto overíš celú funkčnosť.

---

### 4. ☁️ Nasadenie na GitHub Actions (beh na pozadí)
Keď všetko lokálne funguje, presunieme skript na GitHub, aby bežal automaticky každých 5 minút zadarmo.

1. Vytvor nový repozitár na [github.com/new](https://github.com/new).
2. Nastav ho ako **Public** (pre neobmedzené spustenia zadarmo).
3. Nahraj/Pushni kód do repozitára:
   ```bash
   git init
   git add .
   git commit -m "init: smeny monitor"
   git branch -M main
   git remote add origin https://github.com/TVOJE_MENO/smeny-monitor.git
   git push -u origin main --force
   ```
4. Choď do nastavení repozitára na GitHube:
   `Settings` -> `Secrets and variables` -> `Actions` -> tlačidlo **New repository secret**.
5. Pridaj 4 Secrets (dôverné premenné):

| Názov Secretu | Čo do neho vložiť |
|---|---|
| `SMENY_USERNAME` | Prihlasovací e-mail do smeny.cz |
| `SMENY_PASSWORD` | Heslo do smeny.cz |
| `TELEGRAM_BOT_TOKEN` | Celý API token z @BotFather |
| `TELEGRAM_CHAT_ID` | Tvoje číselné Chat ID |

---

### 5. 🚀 Prvé spustenie na GitHube
1. Choď na záložku **Actions** vo svojom GitHub repozitári.
2. Vľavo klikni na workflow **"Smeny.cz – Monitor voľných smien"**.
3. Vpravo klikni na sivé tlačidlo **Run workflow** -> zelené **Run workflow**.
4. Počkaj 1-2 minúty. Po úspešnom dobehnutí (zelená fajočka) bude skript bežať automaticky každých 5 minút.

---

## ❓ Riešenie problémov

### ❌ Telegram chyba `401 Unauthorized`
* **Príčina:** Token bota je nesprávny.
* **Riešenie:** Uisti sa, že si skopíroval kompletný token z BotFather vrátane prípadných písmen či znakov na úplnom konci.

### ❌ Telegram chyba `400 Bad Request: chat not found`
* **Príčina:** Nesprávne Chat ID, alebo si ešte neaktivoval bota.
* **Riešenie:** 
  1. Otvor čet so svojím botom na Telegrame a klikni na **Start**.
  2. Over svoje Chat ID cez `@userinfobot`.

### ❌ Prihlásenie na smeny.cz zlyhalo s chybou `403 Forbidden`
* **Príčina:** Server zablokoval automatický skript kvôli podozrivým hlavičkám.
* **Riešenie:** Skript už obsahuje pokročilé maskovanie hlavičiek (Chrome User-Agent). Ak sa chyba objaví, uisti sa, že používaš najnovšiu verziu `monitor.py`.
