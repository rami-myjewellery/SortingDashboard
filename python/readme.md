# 📦 Geek+ IOP Scraper – Container Binding Dashboard

This project scrapes data from the **Geek+ Container Binding Dashboard**, particularly the "Total" row, using Selenium and serves it via a Flask API.

## 🚀 Features

- ✅ Headless Chrome-based scraping via Selenium 4
- ✅ Auto-handling of `iframe`-embedded dashboards
- ✅ Language-agnostic scraping using pure CSS selectors
- ✅ Easy deployment via Flask + CORS support
- ✅ Environment variable support for credentials

---

## 🔧 Installation Guide

### 1. Install Python

Ensure Python 3.9+ is installed:

- **macOS** (using Homebrew):
  ```bash
  brew install python
  ```

- **Ubuntu/Linux**:
  ```bash
  sudo apt update
  sudo apt install python3 python3-pip
  ```

- **Windows**:  
  Download from: [https://www.python.org/downloads/](https://www.python.org/downloads/)

Verify installation:
```bash
python3 --version
pip3 --version
```

---

## 📁 Project Setup

### 2. Clone the Repo

```bash
git clone https://github.com/your-org/geekplus-iop-scraper.git
cd geekplus-iop-scraper
```

### 3. Create Virtual Environment (Optional but Recommended)

```bash
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

---

### 4. Install Dependencies

Install required packages using pip:

```bash
pip install -r requirements.txt
```

If you don't have `requirements.txt`, create it with:

```text
attrs==25.3.0
blinker==1.9.0
certifi==2025.4.26
charset-normalizer==3.4.2
click==8.2.0
Flask==3.1.1
flask-cors==6.0.0
h11==0.16.0
idna==3.10
itsdangerous==2.2.0
Jinja2==3.1.6
MarkupSafe==3.0.2
outcome==1.3.0.post0
packaging==25.0
PySocks==1.7.1
python-dotenv==1.1.0
requests==2.32.3
selenium==4.32.0
sniffio==1.3.1
sortedcontainers==2.4.0
trio==0.30.0
trio-websocket==0.12.2
typing_extensions==4.13.2
urllib3==2.4.0
webdriver-manager==4.0.2
websocket-client==1.8.0
Werkzeug==3.1.3
wsproto==1.2.0
```

---

## 🔑 Configuration

### 5. Set Environment Variables

You can set login credentials in your environment:

```bash
export GEEKPLUS_USER=your_username
export GEEKPLUS_PW=your_password
```

Or define them in a `.env` file (if using `python-dotenv`):

```env
GEEKPLUS_USER=your_username
GEEKPLUS_PW=your_password
```

---

## ▶️ Running the Server

To start the Flask server:

```bash
python3 your_script_name.py
```

Server will be accessible at:  
[http://localhost:5001/scrape](http://localhost:5001/scrape)

---

## 🧪 Testing

Use curl or Postman to test:

```bash
curl http://localhost:5001/scrape
```

You should receive a JSON response with headers and numbers.

---

## 🛠 Troubleshooting

- **Timeout Error**: Make sure the dashboard is accessible from your network and the iframe is not blocked.
- **Missing Chrome Driver**: `webdriver-manager` should handle this, but make sure Chrome is installed and up-to-date.
- **Headless Errors**: Set `headless=False` in `start_driver()` for debugging in a visible browser window.

---

## 📄 License

MIT License. Use at your own risk.
