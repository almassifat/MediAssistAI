# 🩺 MediAssist AI

**MediAssist AI** is an AI-powered, multilingual medical report analysis system designed to bridge the gap between complex clinical data and patient understanding.

The platform allows users to upload medical reports (images or PDFs), automatically extract key information using OCR, detect abnormal values, and generate clear, human-readable explanations using AI.

---

## 🚀 Key Features

### 📄 Medical Report Processing
- Supports **PNG, JPG, JPEG, and PDF**
- Extracts text using **Tesseract OCR**
- Handles PDFs via image conversion pipeline

### 🧠 AI-Powered Explanation
- Generates:
  - Concise **summary**
  - **Abnormal value detection**
  - Patient-friendly **medical explanation**
- Uses **Groq LLM API** for contextual responses

### 🌐 Multilingual Support
- English
- Bangla (বাংলা)

### 💬 Interactive AI Chat
- Ask follow-up questions about the report
- Context-aware responses
- Chat-style interface

### 📊 Health Insights Dashboard
- Visual representation of detected values
- Easy-to-understand insights

### 🔍 Transparency
- Raw OCR text
- Parsed abnormal parameters

---

## 🏗️ System Architecture

User → Frontend → FastAPI → OCR → Parser → LLM → Response

---

## 📁 Project Structure

```text
mediassist_ai/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── prompts.py
│   ├── llm_service.py
│   ├── ocr_service.py
│   ├── parser_service.py
│   ├── medical_service.py
│   └── utils.py
├── frontend/
│   └── app.py
├── temp_uploads/
├── .env
├── requirements.txt
└── README.md
```
---

## ⚙️ Setup

python -m venv venv  
source venv/Scripts/activate  
pip install -r requirements.txt  

---

## ▶️ Run

Backend:
uvicorn backend.main:app --reload  

Frontend:
streamlit run frontend/app.py  

---

## 📡 API Endpoints
POST /analyze-report
Upload report
Returns summary + explanation
POST /ask-report
Ask questions based on report
Returns AI response

## 🧪 Testing

Manual test scenarios available in tests.md

## 👨‍💻 Author

Hasin Almas Sifat

---

## 📈 Future Improvements
Advanced NLP parsing
Better clinical accuracy
Plotly dashboards
Multi-report comparison

## © Copyright

© 2026 Hasin Almas Sifat. All rights reserved.
