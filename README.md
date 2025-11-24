# Local AI DB Assistant

A lightweight Python/Rust application built with Tauri and React that runs fully offline and connects directly to your local database.  
The goal is to help developers work faster by allowing a local AI to:

- Read and explore the database efficiently  
- Generate SQL queries on demand  
- Assist in debugging and development  
- Work entirely offline, without external APIs  

## Tech Stack

- Rust — backend core for performance and database operations  
- Python — local AI engine and model orchestration  
- Tauri — desktop application wrapper  
- React — user interface  
- SQLite/Postgres/MySQL — compatible with common local databases  

## Features

- Full offline operation  
- Fast local database queries  
- Natural language to SQL generation  
- Automatic understanding of schemas  
- Cross-platform support (Windows, macOS, Linux)  

## How It Works

1. The AI model runs locally through Python.  
2. Tauri manages communication between the Python engine and the Rust backend.  
3. Rust handles secure communication with the database running on localhost.  
4. React provides the interface for interacting with the AI and generating queries.

## Project Structure

/rust-app -> Rust backend (Tauri)
/rust-app/src -> React frontend
/python-core -> Local AI engine


Requirements:
- Rust installed  
- Python 3.10 or higher  
- Node.js  

