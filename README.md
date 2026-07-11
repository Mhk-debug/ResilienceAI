# ResilienceAI

An AI-powered earthquake hazard assessment system that analyzes building characteristics, seismic activity, fault proximity, and soil characteristics to estimate earthquake risk for a building.

---

## Requirements

Before running the project, make sure you have installed:

- Python 3.11 or later

> Go to the Official Python Downloads Page to grab the executable for your operating system. Run the installer, and crucially, make sure to check the box for "Add Python to PATH" before clicking "Install Now."

- Node.js (LTS recommended)
- uvicorn

```bash
pip install "uvicorn[standard]"
```

- npm

---

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd <repository-name>
```

### 2. Create a `.env` file

Before starting the project, create a file named `.env`.

> **Note:** The `.env` file is not included in the repository and must be created manually.

### 3. Generate a Gemini API key

> **Note:** If you are in a country that is ineligible for Gemini API key like Myanmar, first activate a VPN.

Go to https://aistudio.google.com/api-keys?project=gen-lang-client-0545020544. 
Sign in or sign up as required. 
Click 'Create API Key'. 
Click 'Create Key'. 
Copy the API key by clicking on the clipboard icon of your newly created key.

### 4. Write the Gemini API key into the `.env` file

Open the `.env` that you have created using notepad or other suitable application. 
Once inside, add GEMINI_API_KEY="your_actual_api_key_here" without spaces exactly like this. 
Save the file. 
Done🎉

---

## Running the Backend

Open a terminal and run:

```bash
cd backend
uvicorn main:app --reload
```

---

## Running the Frontend

Open a terminal and run:

```bash
cd frontend
npm run dev
```

---

## Project Structure

```text
ResilienceAI/
│
├── backend/
│   ├── hazard_engine/
│   ├── services/
│   ├── main.py
│   └── ...
│
├── frontend/
│   ├── src/
│   ├── public/
│   └── ...
│
└── README.md
```
