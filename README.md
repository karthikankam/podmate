# 🎧 PodMate - AI-Powered Podcast Generator

Transform your study materials into engaging audio podcasts using AI technology.

[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://podmate-app.streamlit.app/)
[![GitHub](https://img.shields.io/badge/github-repository-blue)](https://github.com/karthikankam/podmate)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

##  Table of Contents

- [About](#about)
- [Features](#features)
- [Demo](#demo)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Limitations](#limitations)
- [Future Enhancements](#future-enhancements)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

##  About

PodMate is a full-stack web application that converts textbooks, notes, and documents into summarized audio podcasts using advanced AI language models. It also features an intelligent research assistant powered by multiple knowledge sources including Wikipedia, ArXiv, and real-time web search.

**Problem it Solves:** Students and professionals often struggle to find time to read lengthy documents. PodMate makes learning accessible on-the-go by converting written content into audio format while maintaining the key information through AI-powered summarization.

##  Features

### Podcast Generator
- **PDF & Text Support**: Upload PDF or TXT files for conversion
- **Smart Summarization**: AI-powered content summarization using LangChain
- **Natural Audio**: High-quality text-to-speech using Groq API
- **Batch Processing**: Handle documents up to 10MB
- **Session History**: View podcasts generated in your current session

###  AI Research Assistant
- **Multi-Source Search**: Integrates Wikipedia, ArXiv, and DuckDuckGo
- **Interactive Chat**: Natural conversation interface with the AI assistant
- **Context-Aware**: Maintains conversation history for better responses
- **Real-Time Research**: Access the latest information from multiple sources

###  User Management
- **Secure Authentication**: Bcrypt password hashing
- **User Registration**: Create personal accounts
- **Session Management**: Secure session handling
- **API Key Validation**: Auto-validate Groq API keys

##  Demo

 **Live Application:** [https://podmate-app.streamlit.app/](https://podmate-app.streamlit.app/)

### How to Use

1. **Visit the app** at [podmate-app.streamlit.app](https://podmate-app.streamlit.app/)
2. **Create an account** or login
3. **Enter your Groq API key** in the sidebar (get one free at [console.groq.com](https://console.groq.com/keys))
4. **Upload a document** and generate your podcast!

##  Tech Stack

**Frontend:**
- [Streamlit](https://streamlit.io/) - Interactive web framework

**Backend:**
- Python 3.9+
- [LangChain](https://python.langchain.com/) - LLM framework
- [LangGraph](https://python.langchain.com/docs/langgraph) - Agent orchestration
- SQLite - Database for user management

**AI & APIs:**
- [Groq](https://groq.com/) - Fast LLM inference
- gTTS - Text-to-speech conversion
- Wikipedia API
- ArXiv API
- DuckDuckGo Search API

**Deployment:**
- Streamlit Community Cloud
- GitHub for version control

##  Installation

### Prerequisites

- Python 3.9 or higher
- pip package manager
- Groq API key ([Get one here](https://console.groq.com/keys))

### Local Setup

1. **Clone the repository**

2. **Create virtual environment**

3. **Install dependencies**

4. **Run the application**
5. **Open in browser** https://podmate-app.streamlit.app/
