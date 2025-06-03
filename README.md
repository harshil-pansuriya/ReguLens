# Regulens: DPDP Compliance Auditor

Regulens is an AI-powered tool to audit documents for compliance with India's Digital Personal Data Protection (DPDP) Act. It processes PDF or DOCX files, extracts text, generates embeddings, and uses Google Gemini to analyze compliance against all DPDP Act sections, providing gaps and recommendations.

## Features

- Upload PDF or DOCX documents for analysis
- Audit compliance with the full DPDP Act
- Identify compliance gaps with actionable suggestions
- Scalable architecture using FastAPI, PostgreSQL, Pinecone, and LangChain
- Preprocess DPDP Act sections for reference

## Tech Stack

- Framework: FastAPI
- Database: PostgreSQL (AsyncPG)
- Vector Store: Pinecone
- LLM: Google Gemini (via LangChain)
- Embeddings: Sentence Transformers (all-MiniLM-L6-v2)
- Workflow: LangGraph
- File Processing: PyMuPDF, python-docx
- Logging: Loguru
- Configuration: Pydantic

## Setup

1. Clone the repository:

    ```
    git clone https://github.com/harshil-pansuriya/ReguLens.git
    cd Regulens
    ```

2. Create and activate a virtual environment:
   ```
    python -m venv yout_env_name
    source your_env_name/bin/activate  # On Windows: your_env_name\Scripts\activate
    ```

3. Install dependencies:
    ```
   pip install -r requirements.txt
    ```
4. Configure environment variables:
- Copy `.env.example` to `.env` and update:
  ```
    POSTGRES_HOST=localhost
    POSTGRES_PORT=potgres_port
    POSTGRES_DB=database_name
    POSTGRES_USER=postgres
    POSTGRES_PASSWORD=your_password
    PINECONE_API_KEY=your_pinecone_key
    GOOGLE_API_KEY=your_google_key
    ```



5. Set up PostgreSQL:
run command:
 ``` psql -U postgres -h localhost ```

Ensure PostgreSQL is running and create a database named your_database_name.

Run the following SQL to create tables (or use an ORM tool to initialize):
```
CREATE TABLE dpdp_act (
    id SERIAL PRIMARY KEY,
    section_number VARCHAR NOT NULL,
    section_title VARCHAR,
    chapter VARCHAR,
    content TEXT NOT NULL,
    is_chunk BOOLEAN DEFAULT FALSE,
    chunk_index INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR NOT NULL,
    chunk_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE audits (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) NOT NULL,
    dpdp_section VARCHAR,
    compliance_status BOOLEAN NOT NULL,
    gaps TEXT,
    suggestions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

```


6. Preprocess DPDP Act:

Place dpdp_act.txt in the data/ directory.
Run:
``` 
python scripts/process_dpdp_act.py
```

Run the application:
```
python -m app.main
```

- API available at `http://localhost:8000`.

## Usage

### Upload a Document
- Endpoint: POST /documents/upload
- Request: Multipart form with a `file` field (PDF or DOCX).
- Example:
```
curl -X POST -F "file=@policy.pdf" http://localhost:8000/documents/upload
```

- Response:
```
{
  "document_ids": [1, 2],
  "filename": "policy.pdf"
}
```

### Audit a Document
- Endpoint: POST /documents/audit/{document_id}
- Request: Specify `document_id` from upload response.
- Example:
``` 
curl -X POST http://localhost:8000/documents/audit/1
```

- Response:
```
{
  "document_id": 1,
  "filename": "policy.pdf",
  "compliance_status": false,
  "dpdp_sections_analyzed": "Section 1, Section 2",
  "compliance_gaps": "Missing consent mechanism",
  "recommendations": "Implement explicit consent"
}

```

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Contributing
Contributions are welcome! Submit a pull request or open an issue to discuss changes.
