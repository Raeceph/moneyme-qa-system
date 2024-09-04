# MONEYME AI Q&A System Documentation

## CLI Usage (Docker)

Use the following commands in your terminal:

1. Upload a PDF:
   ```
   docker-compose run --rm moneyme-qa cli --mode upload --pdf /external_pdfs/moneyme_report.pdf
   ```

2. List processed documents:
   ```
   docker-compose run --rm moneyme-qa cli --mode list
   ```

3. Ask a question:
   ```
   docker-compose run --rm moneyme-qa cli --mode query --question "What is MONEYME's business model?"
   ```

4. Start a chat session:
   ```
   docker-compose run --rm -it moneyme-qa cli --mode chat
   ```

Note: Ensure your PDFs are in the directory mapped to `/external_pdfs` in your Docker setup.

## REST API Usage

To interact with the MONEYME AI Q&A API, use the provided Postman collection:

1. Import the `MONEYME AI Q&A API.postman_collection.json` file into Postman.
2. Set the `base_url` variable to `http://localhost:8000` (or your specific API URL).

### Available Endpoints:

1. **Upload PDF**
   - POST `{{base_url}}/upload_pdf`
   - Use form-data with key 'file' and select your PDF.

2. **List Documents**
   - GET `{{base_url}}/list_documents`

3. **Query**
   - POST `{{base_url}}/query`
   - Body: `{ "question": "Your question here" }`

4. **Chat**
   - POST `{{base_url}}/chat`
   - Body: 
     ```json
     {
       "session_id": "{{session_id}}",
       "question": "Your question here"
     }
     ```
   - For a new chat, omit the session_id. Use the returned session_id for follow-up questions.

Use Postman to send requests to these endpoints. The collection includes pre-configured requests for each endpoint, making it easy to interact with the API.

