# FinAI — Financial Intelligence Assistant

FinAI is an AI-powered financial analysis assistant that allows users to query financial datasets using natural language. The system combines structured data retrieval with large language models (LLMs) to generate accurate and explainable insights about financial metrics, trends, and comparisons.

The goal of this project is to build a **data-grounded AI system** that prevents hallucinations by combining deterministic database queries with LLM-generated explanations.

---

# Overview

Financial datasets often contain complex tables and historical metrics that are difficult to analyze quickly. FinAI enables users to ask questions in natural language and receive responses generated directly from verified data.

Instead of allowing the language model to invent answers, FinAI retrieves financial data from a database and then uses an LLM to produce a human-readable explanation.

This architecture ensures responses remain **accurate, interpretable, and traceable to real data**.

---

# Key Features

- Natural language financial queries  
- Data-grounded responses generated from verified database values  
- Hybrid RAG-style architecture combining SQL retrieval with LLM explanations  
- Hallucination prevention by restricting models from generating financial numbers  
- Interactive web interface for user queries  

---

# System Architecture

The system follows a hybrid pipeline:

User Query  
↓  
Intent Detection  
↓  
Query Planning  
↓  
SQL Data Retrieval  
↓  
Financial Computation  
↓  
LLM Explanation Layer  
↓  
Final Response

Key principle:  
The language model **does not generate financial numbers**, it only explains values retrieved from the database.

---
## Repository Structure

```
finai/
│
├── backend/                     # Core backend services
│   ├── api.py                   # Flask API endpoints
│   ├── query_engine.py          # Query planning and execution logic
│   ├── data_processing.py       # Data cleaning and preprocessing
│   ├── database/                # Database schema and database helpers
│   │   ├── schema.sql
│   │   └── db_utils.py
│   └── requirements.txt
│
├── frontend/                    # React user interface
│   ├── components/
│   ├── pages/
│   └── package.json
│
├── evaluation/                  # Model evaluation experiments
│   └── experiments.ipynb
│
└── README.md
```
---
# Tech Stack

Frontend  
React

Backend  
Flask (Python)

Database  
PostgreSQL / SQLite

AI Layer  
LLM via Ollama (LLaMA 3)

Cloud Infrastructure  
AWS Lambda  
AWS DynamoDB

Data Processing  
Pandas  
NumPy

---

# Example Queries

- "What was the NAV growth of this fund over the last five years?"  
- "Compare performance between two mutual funds."  
- "What was the average monthly SIP contribution in 2023?"  

---

# Model Evaluation

FinAI was evaluated against a baseline rule-based financial assistant.

Evaluation metrics included:

- Response accuracy  
- Explanation completeness  
- Information relevance  
- Response latency  
- User clarity and interpretability  

Statistical tests were applied to measure improvements between the baseline system and the LLM-augmented architecture.

---

# Project Goals

- Build reliable AI systems for financial data analysis  
- Reduce hallucination risk in LLM applications  
- Demonstrate hybrid retrieval + LLM architectures  
- Enable natural language interaction with structured financial data  

---

