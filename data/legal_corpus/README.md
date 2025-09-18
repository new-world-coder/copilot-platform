# Legal Corpus

This directory contains sample legal documents for testing the RAG (Retrieval-Augmented Generation) system.

## Documents Included

- **sample_contract.txt** - Software License Agreement with standard clauses
- **sample_case_law.txt** - Court case (Smith v. Jones Corporation) regarding non-compete clauses
- **privacy_policy.txt** - Privacy policy document with data collection and usage terms
- **terms_of_service.txt** - Terms of service with user agreements and limitations

## Usage

To index these documents for RAG retrieval:

```bash
# From the project root
python rag/indexer.py data/legal_corpus/
```

This will create a FAISS index in `data/vector_store/` that can be used for semantic search and retrieval.

## Document Types

### Contracts
- License agreements
- Employment contracts
- Service agreements
- Non-disclosure agreements

### Case Law
- Court decisions
- Legal precedents
- Judicial opinions
- Case summaries

### Policies
- Privacy policies
- Terms of service
- Data protection policies
- Compliance documents

## Adding More Documents

To add more legal documents:

1. Place text files (.txt, .md, .json) in this directory
2. Run the indexer to rebuild the search index
3. The documents will be automatically included in RAG retrieval

## File Formats Supported

- `.txt` - Plain text files
- `.md` - Markdown files
- `.json` - JSON documents with text fields

## Indexing Options

The indexer supports various options:

```bash
# Basic indexing
python rag/indexer.py data/legal_corpus/

# With custom model and index type
python rag/indexer.py data/legal_corpus/ --model all-mpnet-base-v2 --index-type hnsw

# With verbose output
python rag/indexer.py data/legal_corpus/ --verbose
```
