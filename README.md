# ResilienceAI

An AI-powered earthquake hazard assessment system that analyzes building characteristics, seismic activity, fault proximity, and soil characteristics to estimate earthquake risk for a building.

ResilienceAI combines a building resilience model with an environmental hazard assessment engine to produce an overall earthquake risk assessment, supported by AI-generated explanations and recommendations.

---

## Requirements

Before running the project, make sure you have the following installed:

### Python 3.11 or later

Download Python from the official Python website.

During installation on Windows, make sure to enable:

> **Add Python to PATH**

before clicking **Install Now**.

You can verify your installation with:

```bash
python --version
```

or:

```bash
python3 --version
```

---

### Node.js

Install the latest **LTS version of Node.js**.

Verify the installation:

```bash
node --version
npm --version
```

---

### Uvicorn

Uvicorn is used to run the FastAPI backend.

Install it with:

```bash
pip install "uvicorn[standard]"
```

---

### Git

Git is required to clone the repository.

Verify the installation:

```bash
git --version
```

---

## Setup

### 1. Clone the repository

Clone the repository and navigate into the project directory:

```bash
git clone <repository-url>
cd <repository-name>
```

Replace `<repository-url>` and `<repository-name>` with the actual repository URL and folder name.

---

### 2. Create the environment file

The project requires environment variables for external services and the database.

Create a file named:

```text
.env
```

in the project root directory:

```text
ResilienceAI/
├── backend/
├── frontend/
└── .env
```

> **Important:** The `.env` file is not included in the repository because it contains secret credentials. Do not commit it to Git or share it publicly.

---

## 3. Create a Neon PostgreSQL Database

ResilienceAI uses a PostgreSQL database hosted by Neon.

### Create a Neon account

Go to the official Neon website and create an account or sign in.

After signing in:

1. Create a new project.

2. Enter a project name, for example:

   ```text
   ResilienceAI
   ```

3. Select a PostgreSQL region close to your users or application server.

4. Create the project.

Neon will automatically create a PostgreSQL database for your project.

---

### Get the database connection string

After creating your Neon project:

1. Open the Neon project dashboard.
2. Go to the **Connect** section.
3. Select the PostgreSQL connection option.
4. Copy the connection string.

It should look similar to:

```text
postgresql://username:password@ep-example-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
```

Your actual connection string will be different.

> **Important:** Keep this connection string private. It contains your database credentials.

---

## 4. Generate a Gemini API Key

ResilienceAI uses Google's Gemini API for AI-generated earthquake risk interpretations and recommendations.

> **Note:** Gemini API availability depends on your country or region. If Google AI Studio is unavailable in your region, you may need to use a VPN where permitted by applicable laws and Google's terms of service.

Go to Google AI Studio's API key page and sign in with your Google account.

Then:

1. Click **Create API Key**.
2. Select an existing Google Cloud project or create a new one if prompted.
3. Confirm the creation of the key.
4. Copy the API key using the clipboard icon.

> **Important:** Never publish your Gemini API key or commit it to Git.

---

## 5. Configure the `.env` File

Open the `.env` file in the project root and add the required environment variables.

Example:

```env
GEMINI_API_KEY="your_actual_gemini_api_key_here"
DATABASE_URL="your_neon_postgresql_connection_string_here"
```

For example:

```env
GEMINI_API_KEY="AIzaSy..."
DATABASE_URL="postgresql://username:password@ep-example.neon.tech/neondb?sslmode=require"
```

Replace the placeholder values with your actual credentials.

> **Do not include the quotation marks as part of the actual credential values if your environment or configuration system does not require them.**

Your `.env` file should never be uploaded to GitHub or shared publicly.

---

## 6. Install Backend Dependencies

Navigate to the backend directory:

```bash
cd backend
```

Install the project's Python dependencies.

If the project includes a `requirements.txt` file:

```bash
pip install -r requirements.txt
```

If you are using a virtual environment, it is recommended to create and activate one first.

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Then install the dependencies:

```bash
pip install -r requirements.txt
```

---

## Running the Backend

From the `backend` directory, start the FastAPI development server:

```bash
uvicorn main:app --reload
```

The backend will normally be available at:

```text
http://127.0.0.1:8000
```

FastAPI's interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

The alternative ReDoc documentation is available at:

```text
http://127.0.0.1:8000/redoc
```

Keep the backend terminal running while using the frontend.

---

## Running the Frontend

Open a second terminal window and navigate to the frontend directory:

```bash
cd frontend
```

Install the required JavaScript dependencies:

```bash
npm install
```

Start the Next.js development server:

```bash
npm run dev
```

The frontend will normally be available at:

```text
http://localhost:3000
```

Open this address in your browser.

---

## Running the Full Application

To run the complete application locally, you need two terminal windows.

### Terminal 1 — Backend

```bash
cd backend
uvicorn main:app --reload
```

### Terminal 2 — Frontend

```bash
cd frontend
npm install
npm run dev
```

Then open:

```text
http://localhost:3000
```

The frontend communicates with the FastAPI backend running on:

```text
http://127.0.0.1:8000
```

---

## Project Structure

```text
ResilienceAI/
│
├── backend/
│   ├── database/
│   │   └── Database configuration and database-related functionality
│   │
│   ├── models/
│   │   └── Data models and schemas
│   │
│   ├── routes/
│   │   └── FastAPI API endpoints
│   │
│   ├── scripts/
│   │   └── Utility and data-processing scripts
│   │
│   ├── services/
│   │   ├── hazard_engine/
│   │   │   └── Environmental and seismic hazard calculations
│   │   │
│   │   ├── resilience_engine.py
│   │   │   └── Building resilience and vulnerability calculations
│   │   │
│   │   ├── llm_services.py
│   │   │   └── Gemini API integration
│   │   │
│   │   └── pipeline.py
│   │       └── Assessment processing pipeline
│   │
│   ├── tests/
│   │   └── Backend tests
│   │
│   ├── main.py
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   └── Next.js application routes and pages
│   │
│   ├── components/
│   │   └── Reusable React UI components
│   │
│   ├── lib/
│   │   └── Shared libraries and utilities
│   │
│   ├── utils/
│   │   └── Frontend utility functions
│   │
│   ├── package.json
│   └── ...
│
├── .env
└── README.md
```

---

## Environment Variables

The application requires the following environment variables:

| Variable         | Description                                        |
| ---------------- | -------------------------------------------------- |
| `GEMINI_API_KEY` | API key used to access Google's Gemini API         |
| `DATABASE_URL`   | PostgreSQL connection string for the Neon database |

Example:

```env
GEMINI_API_KEY="your_gemini_api_key"
DATABASE_URL="your_neon_database_connection_string"
```

---

## Troubleshooting

### Backend cannot connect to the database

Check that:

* `DATABASE_URL` is present in the `.env` file.
* The connection string was copied correctly from Neon.
* The connection string includes the required SSL configuration, usually:

```text
?sslmode=require
```

* Your Neon project and database are active.

---

### Gemini API errors

Check that:

* `GEMINI_API_KEY` is present in `.env`.
* The API key is valid.
* The Gemini API is available in your region.
* The API key has not been accidentally exposed or revoked.

---

### Frontend cannot connect to the backend

Make sure that:

1. The backend is running.
2. The backend is running on the expected port.
3. The frontend is configured to use the correct backend URL.

The default local backend URL is:

```text
http://127.0.0.1:8000
```

---

## Security

Never commit secrets to the repository.

The following should remain private:

* Gemini API keys
* Neon database connection strings
* Database passwords
* Any other API credentials

Make sure `.env` is included in `.gitignore`:

```text
.env
```

If a secret is accidentally committed to a public repository, revoke or rotate the credential immediately.

---

## Technology Stack

### Frontend

* Next.js
* React
* TypeScript
* Tailwind CSS
* shadcn/ui
* Recharts

### Backend

* Python
* FastAPI
* Uvicorn
* Pydantic

### Database

* PostgreSQL
* Neon

### Artificial Intelligence

* Google Gemini API

### Earthquake and Environmental Data

The hazard assessment engine uses external seismic, geographic, and environmental data sources to evaluate factors such as:

* Historical seismic activity
* Proximity to active faults
* Soil conditions
* Elevation
* Urban density

---

## Project Information

This project was developed for the AI Innovation Competition 2026 at STI Myanmar University by CodeTrio.

Team - CodeTrio

Competition - AI Innovation Competition 2026

School - STI Myanmar University
