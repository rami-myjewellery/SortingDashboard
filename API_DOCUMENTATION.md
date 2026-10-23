# Warehouse Dashboard API Documentatie

Dit document beschrijft de beschikbare REST endpoints van de **Sorting Dashboard API**, hoe je deze kunt aanroepen met authenticatie (`x-api-key`), en wat voor JSON-data je terugkrijgt.

---

## 1. Algemene Informatie & Authenticatie

* **Base URL:** `https://sorting-dashboard-api-208732756826.europe-west4.run.app`
* **Swagger UI / Documentatie:** `https://sorting-dashboard-api-208732756826.europe-west4.run.app/`
* **OpenAPI JSON:** `https://sorting-dashboard-api-208732756826.europe-west4.run.app/openapi.json`
* **Authenticatie Header:**
  ```http
  x-api-key: wh_live_GAqd6uJQ_j5UdXY4HLC7lZXyxXn_9u0m2evCh2kQe30
  ```

> **Opmerking over backwards compatibility:**  
> Requests met een geldige `x-api-key` worden direct geaccepteerd. Requests zónder key worden momenteel nog getolereerd (zodat bestaande gecachte browsers niet breken), maar verzoeken met een *onjuiste* key worden geweigerd met `401 Unauthorized`.

---

## 2. Overzicht van de Beschikbare Endpoints

Alle dashboard-endpoints zijn `GET` requests onder het pad `/dashboard/<Afdeling>`:

| Endpoint | Afdeling / Proces | Belangrijkste Metrics & Data |
| :--- | :--- | :--- |
| `GET /dashboard/GeekPicking` | **Geek+ Robot Picking** | Picksnelheid per uur, dagtotaal (Lines), wachtende Geek-karren en actieve operators. |
| `GET /dashboard/GeekInbound` | **Geek+ Robot Inslag** | Inslagvolume, aantal items en verwerkte handling units. |
| `GET /dashboard/Picking` | **Regulier / Mono Picking** | Picktijd per item, aantal verwerkte eenheden, wachttijd FMA-karren en actieve pickers. |
| `GET /dashboard/InboundAndBulk` | **Inslag & Bulk Handling** | Verwerkte bulk items, bulk volume ($m^3$) en verwerkingstijden. |
| `GET /dashboard/Replenishment` | **Aanvullen (Replenishment)** | Inslag- en aanvulsnelheden, verwerkte dozen/units. |
| `GET /dashboard/Sorting` | **Sorteermachine (Sorting)** | Vullingsgraad van de sorteerbanden (Error belt, Single belt, Multi belt). |
| `GET /dashboard/Returns` | **Retourenverwerking** | Retourvolume, aantal verwerkte retouritems en behandeltijd. |
| `GET /dashboard/ErrorLanes` | **Foutstraten & Storingen** | Error rate percentage, opgeloste fouten en openstaande fouten. |
| `GET /dashboard/NextDayProgress` | **Next Day Cut-Off & Loading** | Chronologische laad- & vertrekplanning (Reflex docks), pick batch voortgang en HD laadstatus. |

---

## 3. Voorbeeld cURL Requests

### Voorbeeld 1: Geek Picking ophalen
```bash
curl -X GET "https://sorting-dashboard-api-208732756826.europe-west4.run.app/dashboard/GeekPicking" \
  -H "x-api-key: wh_live_GAqd6uJQ_j5UdXY4HLC7lZXyxXn_9u0m2evCh2kQe30" \
  -H "Accept: application/json"
```

### Voorbeeld 2: Sorteerband status ophalen
```bash
curl -X GET "https://sorting-dashboard-api-208732756826.europe-west4.run.app/dashboard/Sorting" \
  -H "x-api-key: wh_live_GAqd6uJQ_j5UdXY4HLC7lZXyxXn_9u0m2evCh2kQe30" \
  -H "Accept: application/json"
```

### Voorbeeld 3: Replenishment ophalen
```bash
curl -X GET "https://sorting-dashboard-api-208732756826.europe-west4.run.app/dashboard/Replenishment" \
  -H "x-api-key: wh_live_GAqd6uJQ_j5UdXY4HLC7lZXyxXn_9u0m2evCh2kQe30" \
  -H "Accept: application/json"
```

### Voorbeeld 4: Next Day Progress (Reflex Docks) ophalen
```bash
curl -X GET "https://sorting-dashboard-api-208732756826.europe-west4.run.app/dashboard/NextDayProgress" \
  -H "x-api-key: wh_live_GAqd6uJQ_j5UdXY4HLC7lZXyxXn_9u0m2evCh2kQe30" \
  -H "Accept: application/json"
```

---

## 4. Response Structuur & Datamodel

Elk endpoint geeft hetzelfde consistente JSON-schema terug:

```json
{
  "title": "Geek Picks",
  "status": "good",
  "kpis": [
    {
      "label": "per hour",
      "value": 40.0,
      "unit": "Lines"
    },
    {
      "label": "today",
      "value": 40.0,
      "unit": "Lines"
    },
    {
      "label": "Waiting carts (Geek)",
      "value": 0.0,
      "unit": "carts"
    }
  ],
  "historyText": "",
  "people": [
    {
      "name": "KarynaHoluik",
      "comment": "",
      "category": "GeekPicking",
      "speed": 21,
      "idleSeconds": 3,
      "last_seen": "2026-10-12T09:46:10.106003Z",
      "jobs": 24
    }
  ],
  "idleThreshold": 60,
  "kpi_state": {
    "date": "2026-10-12",
    "total": 40,
    "first_event_time": "2026-10-12T09:44:00.120416Z"
  }
}
```

### Uitleg van de velden

* **`title`** *(string)*: De herkenbare naam van het dashboard / proces.
* **`status`** *(enum: `"good"` | `"risk"` | `"bad"`)*: De algehele gezondheidsstatus van de afdeling op basis van drempelwaarden.
* **`kpis`** *(array)*: Lijst met specifieke indicatoren voor die afdeling:
  * `label` *(string)*: Wat de metric voorstelt (bijv. "per hour", "today", "Picking Speed").
  * `value` *(number)*: De actuele numerieke waarde.
  * `unit` *(string)*: De eenheid (bijv. "Lines", "carts", "units", "items").
* **`people`** *(array)*: Actieve medewerkers / operators die recent scans of acties hebben uitgevoerd:
  * `name` *(string)*: Naam of identificatie van de operator.
  * `speed` *(integer)*: Gemiddelde afhandelsnelheid (jobs per minuut).
  * `idleSeconds` *(integer)*: Aantal seconden sinds de laatste geregistreerde scan.
  * `last_seen` *(ISO datetime)*: Tijdstip van de laatste actie.
  * `jobs` *(integer)*: Totaal aantal voltooide taken vandaag.
* **`idleThreshold`** *(integer)*: Aantal seconden inactiviteit voordat een medewerker als 'inactief' wordt gemarkeerd (standaard 60 sec).

---

## 5. Aanroepen vanuit Python / Claude App

```python
import requests

API_URL = "https://sorting-dashboard-api-208732756826.europe-west4.run.app/dashboard/GeekPicking"
API_KEY = "wh_live_GAqd6uJQ_j5UdXY4HLC7lZXyxXn_9u0m2evCh2kQe30"

response = requests.get(
    API_URL,
    headers={"x-api-key": API_KEY}
)

if response.status_code == 200:
    data = response.json()
    print(f"Status: {data['title']} is {data['status']}")
    for kpi in data["kpis"]:
        print(f" - {kpi['label']}: {kpi['value']} {kpi['unit']}")
else:
    print(f"Fout: {response.status_code} - {response.text}")
```
