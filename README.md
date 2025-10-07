HollywoodBuster is a full-stack REST API + automation platform that detects and monitors Instagram Users who don't follow you back and safely mass-unfollows unwanted Instagram accounts using Playwright browser automation with Python and FastAPI.

Public Repo coming soon!

Is your Instagram follower list cluttered? Are you following people who act like hollywood stars and don’t follow you back? Have no fear, HollywoodBuster is here!

**Have no fear — HollywoodBuster is here!**

HollywoodBuster automates Instagram using an authenticated browser session to:
- Fetch your follower and following lists.
- Detect who doesn’t follow you back.
- Optionally mass-unfollow those accounts safely.

---

##  Setting Up for the First Time

Before you can run the scraper, you need to authenticate your Instagram account once.  
This step saves your **login cookies** locally so the automation can use your real session safely — without re-logging in each time.

### 1. Create and activate a virtual environment

```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS / Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Authenticate with Instagram

Run the cookie fetcher script:

```bash
python instagram_cookie_fetcher.py
```

Then:

1. Type in your **Instagram username** when prompted.  
2. A Chrome window will open — log in to Instagram (and complete 2FA if required).  
3. Once you see your home/feed/profile, **press ENTER** in the terminal.  
4. The script will save your authenticated session under:
   ```
   cookies/<username>_<date>_cookies.json
   cookies/<username>_<date>_state.json
   ```

---

## Run the Main Scraper

After cookies are saved, you can run the main script to scrape your followers and following:

```bash
python main.py
```

When prompted, type in the **same username** you used during login.

The scraper will connect to your authenticated Instagram session, fetch your follower and following lists, and save them in the root directory as:

```
followers.json
following.json
```

---

## Output Files

| File | Description |
|------|--------------|
| `followers.json` | List of all users who follow you |
| `following.json` | List of all users you follow |
| `cookies/*.json` | Authentication cookies and session state |

---

## Tech Stack

- **Python 3.10+**
- **FastAPI** – REST API framework  
- **Playwright** – browser automation  
- **Asyncio** – concurrency for scraping tasks  
- **Celery** – For job orchrestration and concurrency 
- **SocketIO** - For Real time reporting of unfollow/follower scrapes
- **React.jS** - Frontend interface for visualizing data
---

##  Coming Soon

-  REST API endpoints  
- Auto-scheduler to fetch the list daily and auto-unfollow
- Dashboard for follower analytics in react.js 

---
