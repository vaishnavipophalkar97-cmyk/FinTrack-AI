# 💰 FinTrack AI

### A local-first AI-powered personal finance tracker built with Streamlit, SQLite, Ollama and Google's Gemma

> **Built for a friend/family member who wanted a simple way to keep track of deposits, withdrawals, investments and financial activity without relying on complicated finance applications or sending personal financial data to cloud AI services.**

---

## 🚀 Overview

FinTrack AI is a **local-first personal finance management application** designed to make everyday financial tracking simple, understandable and private.

The application allows users to:

- Record deposits and withdrawals
- Track investments and financial transactions
- Organize transactions by category and account
- Import transaction data from Excel/CSV files
- View financial activity through an interactive dashboard
- Search and review transaction history
- Ask an AI assistant questions about their recorded financial activity
- Run the AI assistant **locally using Google's Gemma open-weight model through Ollama**

The core idea behind FinTrack AI is simple:

> **Personal financial information should be useful to the person who owns it without requiring that information to be sent to a third-party cloud AI service.**

Instead of sending financial records to a remote AI API, FinTrack AI performs the financial calculations locally and sends only a generated financial summary and the user's question to a locally running Gemma model.

---

# 🎯 Why I Built FinTrack AI

This project started from a very practical problem.

Managing personal finances often means dealing with:

- Multiple bank accounts
- Deposits and withdrawals
- SIPs
- Mutual fund purchases
- Different transaction categories
- Excel spreadsheets
- Manually calculating totals
- Trying to understand spending and investment patterns

Traditional finance applications can also be unnecessarily complicated for someone who simply wants to understand:

> "Where did my money go?"

> "How much have I deposited?"

> "What does my recent financial activity look like?"

> "Can you summarize my transactions?"

I wanted to build something **simple enough for a family member to actually use**, while experimenting with AI in a way that does not require uploading sensitive financial records to a cloud AI provider.

That led to FinTrack AI.

---

# 🤖 Why Open-Weight AI?

AI is useful for financial data when it can turn numbers into something humans can easily understand.

For example, a traditional program can calculate:

```text
Total deposits: ₹85,000
Total withdrawals: ₹32,500
Investment transactions: 7
