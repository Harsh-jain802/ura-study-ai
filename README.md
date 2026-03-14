# Aura Study AI

**Aura Study AI** is an intelligent study assistant that transforms complex study materials into easy-to-understand summaries, quiz questions, and interactive explanations.

Users can upload a PDF document and instantly receive simplified insights, knowledge-testing questions, and answers to their doubts through an AI-powered chat interface.

---

## Elevator Pitch

Upload your study material and let AI instantly generate summaries, quizzes, and answers to your doubts.

---

## Problem

Students often struggle with long and complex academic materials such as research papers, lecture notes, and technical PDFs. Extracting key ideas from these documents can take a lot of time and effort.

Traditional study methods require students to read large amounts of text manually, which can slow down learning and reduce productivity.

---

## Solution

Aura Study AI converts static study documents into an interactive learning experience.

Users can upload a PDF and the system will:

• Generate a simplified summary of the document
• Create quiz questions for self-assessment
• Provide an AI-powered doubt solver to answer questions about the document

This allows students to quickly understand important concepts and reinforce their learning through interaction.

---

## Features

AI Study Guide
Generates clear and simplified summaries from uploaded study materials.

Quiz Generator
Automatically creates questions from the document to help test knowledge.

Doubt Solver
Students can ask questions related to the uploaded material and receive contextual answers.

Document Analysis
Extracts and analyzes content from uploaded PDF files.

Deployed Web Application
The application is accessible through a live web interface.

---

## How It Works

1. User uploads a PDF study document
2. The system extracts text using PyMuPDF
3. The extracted content is processed by the AI model
4. The AI generates summaries, quiz questions, and answers
5. Results are displayed in the Streamlit interface

---

## Tech Stack

Programming Language
Python

Web Framework
Streamlit

AI Model
Google Gemini 1.5 Flash

AI API Integration
Google Generative AI SDK

Document Processing
PyMuPDF (fitz)

User Interface Styling
Custom CSS and HTML injection

Deployment Platform
Streamlit Cloud

Version Control
GitHub

---

## Demo

Live Application
https://ura-study-ai-ju8ey5voyozp46sez29dof.streamlit.app

---

## Installation

Clone the repository

```bash
git clone https://github.com/yourusername/aura-study-ai.git
```

Navigate to the project directory

```bash
cd aura-study-ai
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run the application

```bash
streamlit run app.py
```

---

## Future Improvements

• Image and diagram understanding
• Voice-based explanations
• Support for multiple document formats
• Personalized learning recommendations

---

## Team

Harsh Jain
Project Developer
Krishna Agarwal
Frontend Developer
---

## Project

Built as an AI-powered learning assistant to make studying faster, smarter, and more interactive.
