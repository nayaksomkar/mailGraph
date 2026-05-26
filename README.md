# MailGraph

AI-powered email assistant using LangChain + LangGraph (Python) and Node.js (Gmail proxy) with MongoDB.

## Architecture

```
                    main.py (FastAPI - Python)
                    /        |        \
          crud.py  workflow.py  schemas.py
           /          |           \
    MongoDB      LangGraph Chains    httpx
                    |
              node-gmail/ (Express - Node.js)
                    |
                Gmail API
```

- **Python (FastAPI)** - Core API, LangGraph workflows, MongoDB CRUD
- **Node.js (Express)** - Gmail OAuth + API proxy
- **MongoDB** - Persistent storage

## Prerequisites

- **Python 3.10+** ([download](https://www.python.org/))
- **Node.js 18+** ([download](https://nodejs.org/))
- **MongoDB** (local or Docker)
- **Groq API key** ([get one](https://console.groq.com/))
- **Mistral API key** ([get one](https://console.mistral.ai/))
- **Google Cloud account** (for Gmail API)

## Setup

### 1. Clone the Project

```bash
git clone <repo-url>
cd mailGraph
```

### 2. Set Up Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Set Up Node.js Gmail Proxy

```bash
cd node-gmail
npm install
cd ..
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Now open `.env` and change these values:

#### Values You MUST Change

| Variable | What to Put | Where to Get It |
|----------|-------------|-----------------|
| `GROQ_API_KEY` | Your Groq API key | [console.groq.com/keys](https://console.groq.com/keys) |
| `MISTRAL_API_KEY` | Your Mistral API key | [console.mistral.ai/api-keys](https://console.mistral.ai/api-keys) |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | Google Cloud Console (see below) |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret | Google Cloud Console (see below) |
| `SECRET_KEY` | Any random string | Generate with: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `MONGODB_URI` | MongoDB connection string | Your MongoDB URL (default works for local) |

#### Variables You Can Keep Default

| Variable | Default | Change Only If |
|----------|---------|----------------|
| `LLM_PROVIDER` | `groq` | Want to use `mistral` instead |
| `LLM_MODEL` | `llama-3.1-8b-instant` | Using Mistral (try `mistral-small-latest`) |
| `LLM_TEMPERATURE` | `0.7` | Want more/less creative responses |
| `MAX_ITERATIONS` | `3` | Want more/fewer refinement loops |
| `CRITIQUE_THRESHOLD` | `8` | Want higher/lower quality bar |
| `MONGODB_URI` | `mongodb://localhost:27017/mailgraph` | Using remote MongoDB |
| `PYTHON_PORT` | `8000` | Port 8000 is taken |
| `NODE_PORT` | `3000` | Port 3000 is taken |

#### Example `.env` Configuration

**Using Groq:**
```env
GROQ_API_KEY=gsk_your_actual_key_here
MISTRAL_API_KEY=your_mistral_key_here
LLM_PROVIDER=groq
LLM_MODEL=llama-3.1-8b-instant
```

**Using Mistral:**
```env
GROQ_API_KEY=gsk_your_key_here
MISTRAL_API_KEY=your_actual_mistral_key_here
LLM_PROVIDER=mistral
LLM_MODEL=mistral-small-latest
```

### 5. Get API Keys

#### Groq API Key

1. Go to [https://console.groq.com/](https://console.groq.com/)
2. Sign up or log in
3. Go to **API Keys** in the sidebar
4. Click **Create API Key**
5. Copy the key and paste it in `.env` as `GROQ_API_KEY`

#### Mistral API Key

1. Go to [https://console.mistral.ai/](https://console.mistral.ai/)
2. Sign up or log in
3. Go to **API Keys** in your account settings
4. Click **Create API Key**
5. Copy the key and paste it in `.env` as `MISTRAL_API_KEY`

#### Gmail API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (e.g., "MailGraph")
3. Enable Gmail API:
   - **APIs & Services > Library**
   - Search "Gmail API" and click **Enable**
4. Configure OAuth consent screen:
   - **APIs & Services > OAuth consent screen**
   - Select **External**
   - Fill in app name and support email
   - Add scopes: `.../auth/gmail.readonly`, `.../auth/gmail.send`, `.../auth/gmail.modify`
   - Add your email as test user
5. Create credentials:
   - **APIs & Services > Credentials**
   - **Create Credentials > OAuth client ID**
   - Type: **Web application**
   - Redirect URI: `http://localhost:3000/auth/google/callback`
   - Copy **Client ID** and **Client Secret** to `.env`

### 6. Start MongoDB

**Option A - Local MongoDB**

```bash
# macOS (Homebrew):
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community

# Linux (Ubuntu):
sudo systemctl start mongod

# Verify:
mongosh "mongodb://localhost:27017/mailgraph"
```

**Option B - Docker**

```bash
docker run -d --name mailgraph-mongo -p 27017:27017 mongo:7
```

## Running the Project

### Start Both Services

Open **two terminal windows**:

**Terminal 1 - Python FastAPI:**
```bash
# Activate virtual environment first
source .venv/bin/activate

# Start FastAPI
uvicorn main:app --reload --port 8000
```

**Terminal 2 - Node.js Gmail Proxy:**
```bash
cd node-gmail
npm run dev
```

The API is now running at:
- **Python API**: `http://localhost:8000`
- **Node.js Proxy**: `http://localhost:3000`
- **Swagger Docs**: `http://localhost:8000/docs`

### Using Docker (Everything at Once)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop everything
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

### Quick Commands Reference

```bash
# Python setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start Python API
uvicorn main:app --reload --port 8000

# Start Node.js Gmail proxy
cd node-gmail && npm install && npm run dev

# Run tests
pytest

# Run tests with coverage
pytest --cov=. --cov-report=term-missing

# Docker - start all
docker-compose up -d

# Docker - stop all
docker-compose down

# Docker - rebuild and start
docker-compose up -d --build

# Docker - view logs
docker-compose logs -f python
docker-compose logs -f node-gmail
```

## First-Time Usage Flow

### 1. Authenticate with Gmail

```bash
# Get OAuth URL
curl http://localhost:3000/auth/google/url

# Open the URL in your browser, authorize, copy the code from redirect
curl -X POST http://localhost:3000/auth/google/callback \
  -H "Content-Type: application/json" \
  -d '{"code": "AUTH_CODE_FROM_REDIRECT"}'
```

### 2. Sync Emails from Gmail

```bash
curl -X POST http://localhost:8000/emails/sync \
  -H "Content-Type: application/json" \
  -d '{"maxResults": 20}'
```

### 3. List and Classify Emails

```bash
# List all emails
curl http://localhost:8000/emails

# Classify a specific email
curl -X POST http://localhost:8000/emails/{gmail_id}/classify
```

### 4. Generate AI Reply

```bash
curl -X POST http://localhost:8000/emails/{gmail_id}/reply \
  -H "Content-Type: application/json" \
  -d '{"userTone": "professional", "userInstructions": "Keep it brief"}'
```

### 5. Approve and Send

```bash
# Approve the draft
curl -X POST http://localhost:8000/drafts/{draft_id}/approve

# Edit first (optional)
curl -X PUT http://localhost:8000/drafts/{draft_id} \
  -H "Content-Type: application/json" \
  -d '{"body": "Your edited text"}'

# Send
curl -X POST http://localhost:8000/drafts/{draft_id}/send
```

### 6. Search and Tag

```bash
# Search emails
curl "http://localhost:8000/search?q=project deadline"

# Create a tag
curl -X POST http://localhost:8000/tags \
  -H "Content-Type: application/json" \
  -d '{"name": "urgent", "color": "#FF0000"}'
```

## API Endpoints

### Core
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/health` | Health + DB status |

### Emails
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/emails` | List emails |
| GET | `/emails/{id}` | Get email |
| GET | `/emails/thread/{id}` | Get thread |
| POST | `/emails/sync` | Sync from Gmail |
| POST | `/emails/{id}/classify` | AI classify |
| POST | `/emails/{id}/reply` | Generate reply |
| POST | `/emails/{id}/read` | Mark as read |
| GET | `/search?q=query` | Search emails |

### Drafts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/drafts` | List drafts |
| GET | `/drafts/{id}` | Get draft |
| POST | `/drafts/{id}/approve` | Approve |
| POST | `/drafts/{id}/reject` | Reject |
| PUT | `/drafts/{id}` | Edit draft |
| POST | `/drafts/{id}/send` | Send draft |

### Tags
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tags` | List tags |
| POST | `/tags` | Create tag |
| PUT | `/tags/{id}` | Update tag |
| DELETE | `/tags/{id}` | Delete tag |

### Gmail Proxy (Node.js)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auth/google/url` | Get OAuth URL |
| GET | `/auth/google/callback` | OAuth callback |
| GET | `/messages` | List Gmail messages |
| GET | `/messages/{id}` | Get message |
| GET | `/threads/{id}` | Get thread |
| POST | `/send` | Send email |

## LangGraph Workflow

The AI uses a **4-step feedback loop**:

```
User Email
    │
    ▼
┌──────────────┐
│ Classify     │  ← Categorize: important/spam/work/personal
└──────┬───────┘
       ▼
┌──────────────┐
│ Generate     │  ← Draft reply with context
└──────┬───────┘
       ▼
┌──────────────┐
│ Critic       │  ← Score 1-10
└──────┬───────┘
       │
  ┌────┴────┐
  │ Score≥8 │──► Return draft
  └────┬────┘
       │ Score<8 (loop back)
       ▼
┌──────────────┐
│ Refine       │  ← Improve based on critique
└──────┬───────┘
       │
       └────────► Critic (repeat up to MAX_ITERATIONS)
```

## Supported LLM Models

| Provider | Models Available | Default |
|----------|-----------------|---------|
| **Groq** | `llama-3.1-8b-instant`, `llama-3.1-70b-versatile`, `mixtral-8x7b-32768`, `gemma-7b-it` | `llama-3.1-8b-instant` |
| **Mistral** | `mistral-small-latest`, `mistral-medium-latest`, `mistral-large-latest` | `mistral-small-latest` |

Change model in `.env`:
```env
LLM_PROVIDER=groq
LLM_MODEL=llama-3.1-70b-versatile
```

## Project Structure

```
mailGraph/
├── main.py                 # FastAPI application + routes
├── config.py               # Settings (pydantic)
├── crud.py                 # MongoDB CRUD operations
├── database.py             # MongoDB connection (motor)
├── workflow.py             # LangGraph chains + workflows
├── schemas.py              # Pydantic request/response models
├── logging_config.py       # Logging setup
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Pytest + coverage config
├── .env.example            # Environment template
├── .gitignore              # Git ignore rules
├── docker-compose.yml      # Docker (MongoDB + API)
├── Dockerfile              # Python Docker build
├── node-gmail/
│   ├── package.json        # Node.js dependencies
│   ├── tsconfig.json       # TypeScript config
│   └── src/
│       └── gmail-proxy.ts  # Express Gmail proxy
└── test/
    └── test_main.py        # Pytest tests
```

## Troubleshooting

### LLM Provider Errors

```
Error: Groq API key not found
```
- Check `LLM_PROVIDER=groq` and `GROQ_API_KEY` is set in `.env`

```
Error: Mistral API key not found
```
- Set `LLM_PROVIDER=mistral` and `MISTRAL_API_KEY` in `.env`

### MongoDB Connection Failed

```bash
# Check if MongoDB is running
docker ps | grep mongo
mongosh --eval "db.adminCommand('ping')"

# Start with Docker
docker run -d --name mailgraph-mongo -p 27017:27017 mongo:7
```

### Gmail OAuth Errors

- Verify redirect URI matches: `http://localhost:3000/auth/google/callback`
- Ensure Gmail API is enabled in Google Cloud Console
- Your email must be in OAuth test users list

### Port Already in Use

```bash
# Find process on port 8000
lsof -i :8000
kill -9 <PID>

# Or change port in .env
PYTHON_PORT=8001
```

## Testing

```bash
# Activate virtual environment
source .venv/bin/activate

# Run tests
pytest

# Verbose output
pytest -v

# With coverage
pytest --cov=. --cov-report=html

# Open coverage report
open htmlcov/index.html
```

## Fetched Emails Summary (100 emails)

_Generated from the live MongoDB database on 2026-05-26._

- **Total emails fetched:** 100
- **Unread:** 96 | **Read:** 4
- **Date range:** 2026-05-09 to 2026-05-26

### Top Senders

| Sender | Emails |
|--------|--------|
| Glassdoor Jobs | 15 |
| Flipkart | 10 |
| Tata CLiQ Luxury | 9 |
| Steam | 4 |
| IRCTC Tourism Packages | 4 |
| Groww | 4 |
| Caratlane - A Tata Product | 4 |
| Tata CLiQ Fashion | 3 |
| Amazon Web Services | 3 |
| Instagram | 3 |

### Top Domains

| Domain | Emails |
|--------|--------|
| glassdoor.com | 15 |
| rmp.flipkart.com | 10 |
| luxeupdates.tatacliq.com | 9 |
| irctc.co.in | 6 |
| google.com | 5 |
| steampowered.com | 4 |
| marketing.beekeeperstudio.io | 4 |
| groww.in | 4 |
| engage.caratlane.com | 4 |

### Label Distribution

| Label | Count |
|-------|-------|
| INBOX | 100 |
| UNREAD | 96 |
| CATEGORY_UPDATES | 50 |
| CATEGORY_PROMOTIONS | 44 |
| CATEGORY_SOCIAL | 3 |
| CATEGORY_PERSONAL | 3 |
| IMPORTANT | 2 |

### Recent Subjects (last 10)

- What costs less than your weekend brunch bill
- Freelancing at The Lotus House and 11 more jobs in India for you
- Summer, Styled To Perfection
- What happened in the markets last week?
- CYBER JAAGROOKTA DIWAS - MAY 2026
- Get 10% Off Up to ₹1,000 + No Cost EMI
- New jobs in India. Apply Now.
- See _keonjhar_handball_, jayantimohanta1 and more in your feed
- ₹29.00 received in your Federal Savings account
- Quarterly reminder about YouTube's Terms of Service
```

---

### Sample Email Summaries & Inbox Q&A

_AI-generated summaries and questions using groq (llama-3.1-8b-instant)._


**📧 Email 1**
> **Subject:** Security alert
> **From:** `no-reply@accounts.google.com`

**Summary:** Google has detected unauthorized access to some of your account data and recommends checking your account activity to secure your account. To access your account activity and manage access permissions, visit your Google Account or go to myaccount.google.com/notifications.

**🤔 Question:** Did someone else gain unauthorized access to your Google Account data by using the mailGraph application?

**📧 Email 2**
> **Subject:** A Smarter Way To Shop Gold💛
> **From:** `tatacliq@mall.tatacliq.com`

**Summary:** Tata CLiQ is hosting The Big CLiQ Sale, offering shopping deals and savings on coins through their app.

**🤔 Question:** Is this email a promotional offer from Tata CLiQ Fashion, or a notification about a specific sale or event?

**📧 Email 3**
> **Subject:** The Big CLiQ Sale Goes Homegrown
> **From:** `tatacliqluxury@luxeupdates.tatacliq.com`

**Summary:** You're invited to discover Indian luxury labels at Tata CLiQ Luxury, featuring curated collections of modern and traditional designs. You can unsubscribe from their emails by clicking the link provided.

**🤔 Question:** What is the name of the select group that the recipient is a part of, as mentioned in the email?
