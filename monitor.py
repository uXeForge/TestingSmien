#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════╗
║         Smeny.cz – Monitor voľných smien            ║
║  Sleduje nové dostupné smeny a posiela notifikácie  ║
╚══════════════════════════════════════════════════════╝

Premenné prostredia (GitHub Secrets):
  SMENY_USERNAME      – prihlasovacie meno do smeny.cz
  SMENY_PASSWORD      – heslo do smeny.cz
  TELEGRAM_BOT_TOKEN  – token Telegram bota
  TELEGRAM_CHAT_ID    – Telegram Chat ID príjemcu

Ako detekujeme voľnú smenu:
  - Dotaz: me { shifts } – funguje s employee tokenom
  - Voľná smena = shift kde assignment.userActions obsahuje "ATTEND"
  - To znamená "môžem sa prihlásiť na túto smenu"
"""

import os
import json
import sys
import requests
from datetime import datetime, timezone, timedelta

# ─── Konfigurácia ────────────────────────────────────────────────────────────

GRAPHQL_URL  = "https://smeny.cz/api/graphql/"
STATE_FILE   = "known_shifts.json"
# Počet dní dopredu na sledovanie (30 dní = rozumný horizont)
DAYS_AHEAD   = 30
DEBUG        = os.environ.get("DEBUG", "").lower() in ("1", "true", "yes")


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        print(f"[CHYBA] Chýba premenná prostredia: {name}")
        sys.exit(1)
    return value


# ─── GraphQL pomocník ────────────────────────────────────────────────────────

def gql(query: str, variables: dict = None, token: str = None) -> dict:
    """Vykoná GraphQL POST požiadavku a vráti dáta."""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    resp = requests.post(GRAPHQL_URL, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if DEBUG:
        print("[DEBUG]", json.dumps(data, indent=2, ensure_ascii=False))

    if "errors" in data:
        raise RuntimeError(f"GraphQL chyba: {data['errors']}")

    return data.get("data", {})


# ─── Prihlásenie ─────────────────────────────────────────────────────────────

LOGIN_MUTATION = """
mutation UserLogin($input: UserLoginInput!) {
    userLogin(input: $input) {
        token
        user {
            id
            firstName
            lastName
            email
        }
    }
}
"""

def login(username: str, password: str) -> tuple[str, dict]:
    """Prihlási sa na smeny.cz, vráti (token, user)."""
    data    = gql(LOGIN_MUTATION, variables={"input": {
        "username": username,
        "password": password
    }})
    payload = data["userLogin"]
    return payload["token"], payload["user"]


# ─── Načítanie smien ─────────────────────────────────────────────────────────
#
# DÔLEŽITÉ – Prečo me { shifts } a nie shifts {}?
#   - Globálny endpoint shifts{} vracia 403 pre employee token
#   - me { shifts } je prístupný zamestnancom a vracia ich rozvrh
#     vrátane voľných smien (state=UNOCCUPIED) v ich pracovisku
#
# Ako identifikujeme VOĽNÚ smenu:
#   - assignment.userActions obsahuje "ATTEND"
#   - "ATTEND" = zamestnanec sa môže prihlásiť / obsadiť smenu

SHIFTS_QUERY = """
query ShiftsCalendar($filter: UserShiftsFilter) {
    me {
        shifts(filter: $filter) {
            id
            since
            till
            timeLabel
            note
            borrow
            workplace {
                id
                name
            }
            position {
                name
            }
            user {
                id
                fullName
            }
            assignment {
                userActions
            }
        }
    }
}
"""

def get_available_shifts(token: str) -> list[dict]:
    """
    Načíta smeny zamestnanca na najbližších DAYS_AHEAD dní.
    Filtruje iba tie kde userActions obsahuje ATTEND = voľné smeny.
    """
    now      = datetime.now(timezone.utc)
    date_to  = now + timedelta(days=DAYS_AHEAD)

    # ISO 8601 formát s timezone offsetom
    since_str = now.strftime("%Y-%m-%dT00:00:00+00:00")
    till_str  = date_to.strftime("%Y-%m-%dT23:59:59+00:00")

    data   = gql(SHIFTS_QUERY, token=token, variables={
        "filter": {
            "since": {
                "greaterThanOrEqual": since_str,
                "lessThanOrEqual":    till_str,
            },
            "includeScheduleShifts": {"is": True},
        }
    })

    all_shifts = data.get("me", {}).get("shifts", [])
    print(f"[OK] Celkom smien v rozvrhu: {len(all_shifts)}")

    # Voľná smena = ATTEND je v userActions
    open_shifts = [
        s for s in all_shifts
        if "ATTEND" in (s.get("assignment") or {}).get("userActions", [])
    ]
    print(f"[OK] Voľných smien (ATTEND): {len(open_shifts)}")
    return open_shifts


# ─── Správa stavu ────────────────────────────────────────────────────────────

def load_known_ids() -> set[str]:
    """Načíta množinu ID smien o ktorých sme už notifikovali."""
    if not os.path.exists(STATE_FILE):
        return set()
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f).get("seen_ids", []))
    except (json.JSONDecodeError, KeyError):
        return set()


def save_known_ids(seen_ids: set[str]) -> None:
    """Uloží množinu seen ID do súboru stavu."""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "seen_ids":   sorted(seen_ids),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }, f, indent=2, ensure_ascii=False)
    print(f"[OK] Stav uložený ({len(seen_ids)} ID).")


# ─── Telegram ────────────────────────────────────────────────────────────────

DAYS_SK = {
    "Monday": "Pondelok", "Tuesday": "Utorok",   "Wednesday": "Streda",
    "Thursday": "Štvrtok", "Friday": "Piatok",   "Saturday": "Sobota",
    "Sunday": "Nedeľa"
}

def escape_md(text: str) -> str:
    """Escapuje špeciálne znaky pre Telegram MarkdownV2."""
    for ch in r"_*[]()~`>#+-=|{}.!":
        text = text.replace(ch, f"\\{ch}")
    return text

def format_message(shift: dict) -> str:
    """Sformátuje smenu do Telegram správy (MarkdownV2)."""
    workplace  = escape_md((shift.get("workplace") or {}).get("name", "Neznáme pracovisko"))
    position   = escape_md((shift.get("position")  or {}).get("name", ""))
    note       = escape_md((shift.get("note")       or "").strip())
    time_label = (shift.get("timeLabel") or "").strip()
    is_borrow  = shift.get("borrow", False)

    since_raw = str(shift.get("since", ""))
    till_raw  = str(shift.get("till",  ""))

    try:
        since_dt = datetime.fromisoformat(since_raw.replace("Z", "+00:00"))
        till_dt  = datetime.fromisoformat(till_raw.replace("Z",  "+00:00"))
        day_sk   = DAYS_SK.get(since_dt.strftime("%A"), since_dt.strftime("%A"))
        date_str = escape_md(f"{day_sk} {since_dt.strftime('%d.%m.%Y')}")
        time_str = escape_md(f"{since_dt.strftime('%H:%M')} – {till_dt.strftime('%H:%M')}")
    except Exception:
        date_str = escape_md(since_raw)
        time_str = escape_md(till_raw)

    lines = [
        "🔔 *Uvoľnila sa smena\\!*",
        "",
        f"📍 *Pracovisko:* {workplace}",
    ]
    if position:
        lines.append(f"💼 *Pozícia:* {escape_md(position)}")
    lines.append(f"📅 *Deň:* {date_str}")

    if time_label:
        lines.append(f"⏰ *Čas:* {escape_md(time_label)}")
    else:
        lines.append(f"⏰ *Čas:* {time_str}")

    if is_borrow:
        lines.append("🔄 *Typ:* Výpomoc")
    if note:
        lines.append(f"📝 *Poznámka:* {note}")

    lines += ["", "👉 [Otvoriť smeny\\.cz](https://smeny.cz)"]
    return "\n".join(lines)


def send_telegram(bot_token: str, chat_id: str, text: str) -> bool:
    """Odošle Telegram správu cez Bot API."""
    url  = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    resp = requests.post(url, json={
        "chat_id":                  chat_id,
        "text":                     text,
        "parse_mode":               "MarkdownV2",
        "disable_web_page_preview": False,
    }, timeout=30)
    if resp.status_code == 200:
        print("[OK] Telegram správa odoslaná.")
        return True
    print(f"[CHYBA] Telegram {resp.status_code}: {resp.text}")
    return False


# ─── Hlavná logika ───────────────────────────────────────────────────────────

def main():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{'='*55}")
    print(f"  Smeny.cz Monitor  –  {ts}")
    print(f"  Horizont: {DAYS_AHEAD} dní dopredu")
    print(f"{'='*55}")

    username  = require_env("SMENY_USERNAME")
    password  = require_env("SMENY_PASSWORD")
    bot_token = require_env("TELEGRAM_BOT_TOKEN")
    chat_id   = require_env("TELEGRAM_CHAT_ID")

    # 1. Prihlásenie
    print("\n[1/4] Prihlasujem sa na smeny.cz...")
    try:
        token, user = login(username, password)
        name = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
        print(f"[OK]  Prihlásený ako: {name} ({user.get('email', '')})")
    except Exception as e:
        print(f"[CHYBA] Prihlásenie zlyhalo: {e}")
        sys.exit(1)

    # 2. Načítanie voľných smien
    print("\n[2/4] Načítavam voľné smeny (ATTEND v userActions)...")
    try:
        open_shifts = get_available_shifts(token)
    except Exception as e:
        print(f"[CHYBA] Načítanie smien zlyhalo: {e}")
        sys.exit(1)

    # 3. Porovnanie so stavom
    print("\n[3/4] Porovnávam so stavom...")
    known_ids  = load_known_ids()
    new_shifts = [s for s in open_shifts if s["id"] not in known_ids]
    print(f"[OK]  Nových voľných smien: {len(new_shifts)}")

    # 4. Notifikácie
    print("\n[4/4] Odosielam notifikácie...")
    if new_shifts:
        for shift in new_shifts:
            msg = format_message(shift)
            send_telegram(bot_token, chat_id, msg)
            if DEBUG:
                print("[DEBUG] Správa:\n", msg)
    else:
        print("[OK]  Žiadne nové voľné smeny.")

    # Aktualizácia stavu
    current_ids = {s["id"] for s in open_shifts}
    updated_ids = (known_ids & current_ids) | current_ids
    save_known_ids(updated_ids)

    print(f"\n{'='*55}")
    print(f"  Hotovo. Nových notifikácií: {len(new_shifts)}")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
