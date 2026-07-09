# 🔔 Smeny.cz – Monitor voľných smien

Automatický sledovač voľných smien na [smeny.cz](https://smeny.cz).  
Každých 5 minút skontroluje API a pošle Telegram notifikáciu ak sa uvoľní nová smena.

---

## ⚙️ Setup – krok za krokom

### 1. Vytvor Telegram bota

1. Otvor Telegram → vyhľadaj **@BotFather**
2. Napíš `/newbot`
3. Zvol meno bota (napr. `SmenyMonitor`)
4. Dostaneš **Bot Token** → ulož si ho

### 2. Získaj Chat ID zamestnanca

1. Zamestnanec nájde tvojho bota v Telegrame a napíše `/start`
2. Otvor v prehliadači:
   ```
   https://api.telegram.org/bot<BOT_TOKEN>/getUpdates
   ```
3. V JSON odpovedi nájdi `"chat": { "id": 123456789 }` → to je **Chat ID**

### 3. Vytvor GitHub repozitár

1. Choď na [github.com/new](https://github.com/new)
2. Nastav repozitár ako **Public** (pre neobmedzené Actions minúty)
3. Pushni tento kód:
   ```bash
   git init
   git add .
   git commit -m "init: smeny monitor"
   git remote add origin https://github.com/TVOJE_MENO/smeny-monitor.git
   git push -u origin main
   ```

### 4. Nastav GitHub Secrets

Choď na: `Settings → Secrets and variables → Actions → New repository secret`

| Secret name          | Hodnota                              |
|----------------------|--------------------------------------|
| `SMENY_USERNAME`     | Prihlasovacie meno do smeny.cz       |
| `SMENY_PASSWORD`     | Heslo do smeny.cz                    |
| `TELEGRAM_BOT_TOKEN` | Token z @BotFather                   |
| `TELEGRAM_CHAT_ID`   | Chat ID zamestnanca                  |

### 5. Prvé spustenie

1. Choď na záložku **Actions** v GitHub repozitári
2. Vyber workflow **"Smeny.cz – Monitor voľných smien"**
3. Klikni **"Run workflow"** → **"Run workflow"**
4. Skontroluj výstup – mal by si vidieť úspešné prihlásenie

Od teraz beží automaticky **každých 5 minút** 🎉

---

## 📁 Štruktúra projektu

```
smeny-monitor/
├── monitor.py              ← Hlavný Python skript
├── requirements.txt        ← Závislosti (len requests)
├── known_shifts.json       ← Stav (automaticky generovaný)
└── .github/
    └── workflows/
        └── monitor.yml     ← GitHub Actions konfigurácia
```

---

## 🐛 Ladenie

Ak chceš vidieť plný debug výstup:
1. Choď na **Actions → Run workflow**
2. Zaškrtni **"Zapnúť DEBUG výstup"**
3. Spusti

---

## ❓ Časté problémy

| Problém | Riešenie |
|---------|----------|
| `Prihlásenie zlyhalo` | Skontroluj SMENY_USERNAME a SMENY_PASSWORD v Secrets |
| `Telegram: 400` | Skontroluj TELEGRAM_BOT_TOKEN a TELEGRAM_CHAT_ID |
| `0 voľných smien` | Možno sa query volá inak – zapni DEBUG a pozri sa na odpoveď |
| Workflow nespúšťa | GitHub Actions cron má ~1-15 min oneskorenie, je to normálne |
