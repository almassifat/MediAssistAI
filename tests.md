# Manual test plan for MediAssist AI

This document outlines a set of manual tests that can be performed to
verify that the MediAssist AI backend and frontend work as expected.
Automated tests are not provided for brevity, but these scenarios can
easily be translated into `pytest` cases if desired.

## Prerequisites

1. Install the dependencies listed in `requirements.txt`.
2. Optionally install Tesseract on your system for OCR.  Without it
   the backend will fall back to an informative placeholder.
3. Start the backend server:

   ```bash
   uvicorn mediassist_ai.backend.main:app --reload --port 8000
   ```

4. Start the frontend in a separate terminal:

   ```bash
   streamlit run mediassist_ai/frontend/app.py
   ```

## API tests

### Health endpoint

* **Request:**

  ```bash
  curl -X GET http://localhost:8000/health
  ```

* **Expected response:**

  ```json
  {"status": "ok"}
  ```

### Analyse a report (fallback mode)

1. Prepare a small PDF or image file.  If OCR is not available the
   file contents do not matter.
2. Send a POST request to `/analyze-report` using `curl`:

   ```bash
   curl -X POST -F "file=@/path/to/report.pdf" -F "language=English" http://localhost:8000/analyze-report
   ```

3. **Expected behaviour:**
   * Status field equals `"success"`.
   * The `raw_text` field contains either extracted text or a message
     indicating OCR is unavailable.
   * The `abnormal_items` list may be empty if no values were parsed.
   * The `explanation` field contains a fallback explanation when no
     API key is configured.

### Ask a follow‑up question

1. Copy the `raw_text` field from the previous response.
2. Send a POST request to `/ask-report`:

   ```bash
   curl -X POST -H "Content-Type: application/json" \
     -d '{"report_text": "...", "question": "What is abnormal here?", "language": "English"}' \
     http://localhost:8000/ask-report
   ```

3. **Expected behaviour:**
   * Status field equals `"success"`.
   * The `answer` field contains a reply acknowledging the fallback.

## Frontend tests

1. Navigate to the Streamlit app in your browser (usually
   http://localhost:8501).
2. Upload a report in the **Analyze Report** tab.  Select a language
   and click **Analyze Report**.
3. Verify that the summary, explanation and disclaimer appear.  If no
   OCR is available, you should see a warning message in the
   explanation.
4. Switch to the **Ask About Report** tab, enter a question and click
   **Ask**.  The answer should appear below the button.
5. Switch to the **Technical View** tab to view the raw OCR output and
   any detected abnormal values.

## Error handling

* Uploading a file with an unsupported extension should return a
  response with `status` set to `"error"` and an explanatory
  message.
* Asking a question without analysing a report first should display an
  informational message in the frontend.

These manual tests ensure that the core functionality behaves as
expected in both fallback and fully configured modes.


