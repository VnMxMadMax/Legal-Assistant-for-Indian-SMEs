# 📋 PROJECT DESCRIPTION

## Legal Assistant for Indian SMEs
**GenAI-Powered Contract Analysis Platform**

---

## 🎯 Problem Statement

Indian Small and Medium Enterprises (SMEs) face significant challenges when dealing with legal contracts:

1. **Limited Access to Legal Expertise**: Most SMEs cannot afford regular legal consultation
2. **Complex Legal Language**: Contracts contain jargon that business owners struggle to understand
3. **Hidden Risks**: Unfavorable clauses often go unnoticed until disputes arise
4. **Compliance Gaps**: Many SMEs unknowingly violate Indian business law requirements
5. **Time Constraints**: Business owners lack time to thoroughly review lengthy contracts

---

## 💡 Our Solution

We built a **GenAI-powered Legal Assistant** that democratizes legal understanding for Indian SMEs:

- **Upload any contract** (PDF, DOCX, TXT) and receive instant AI-powered analysis
- **Understand complex terms** through plain-language explanations
- **Identify hidden risks** with clause-level and contract-level risk scoring
- **Check compliance** with key Indian business laws
- **Get actionable advice** with negotiation recommendations
- **Export professional reports** for legal consultation

### How It Works

| Step | Action |
|------|--------|
| 1 | Enter your OpenAI API key |
| 2 | Upload contract (PDF/DOCX/TXT) |
| 3 | View AI-powered analysis across 6 tabs |
| 4 | Export PDF report for legal review |

---

## ✨ Key Features

### Core NLP Capabilities
- ✅ **Contract Classification** - Auto-identifies 6 contract types
- ✅ **AI Clause Extraction** - GPT-4o powered hierarchical extraction
- ✅ **Entity Recognition** - Parties, dates, amounts, jurisdiction (AI-powered)
- ✅ **Obligation Analysis** - Identifies shall/must/may patterns
- ✅ **Ambiguity Detection** - Flags vague terms
- ✅ **Similarity Matching** - Compares to 12 standard templates

### Risk Assessment
- ✅ **Clause-Level Scoring** - Low/Medium/High (0-10 scale)
- ✅ **Contract Risk Score** - Weighted composite score
- ✅ Detection of: Penalty clauses, Indemnity, Unilateral termination, Auto-renewal, IP transfer, Non-compete

### User Outputs
- ✅ Visual Risk Gauge with color coding
- ✅ AI-generated plain-language summaries
- ✅ Clause-by-clause key points
- ✅ Deep Analysis (ambiguity, similarity, obligations, risk details)
- ✅ Indian law compliance scorecard
- ✅ Negotiation recommendations
- ✅ PDF & JSON export

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│            STREAMLIT UI                  │
│  Overview | Clauses | Analysis | Export  │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────┴───────────────────────┐
│           ANALYSIS ENGINE                │
│  ┌─────────┐ ┌─────────┐ ┌───────────┐  │
│  │   NLP   │ │  Risk   │ │    LLM    │  │
│  │Pipeline │ │ Scoring │ │  (GPT-4o) │  │
│  └─────────┘ └─────────┘ └───────────┘  │
└─────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| **LLM** | OpenAI GPT-4o |
| **NLP** | Python + Regex |
| **UI** | Streamlit |
| **File Parsing** | pdfplumber, python-docx |
| **PDF Export** | FPDF2 |

### Compliance with Hackathon Requirements
✅ LLM: GPT-4o for legal reasoning  
✅ NLP: Python with regex patterns  
✅ UI: Streamlit  
✅ Storage: Local JSON audit logs  
✅ No external legal APIs used  

---

## 📁 Project Structure

```
legal_assistant/
├── app.py                 # Main Streamlit app (1500+ lines)
├── config.py              # Configuration
├── nlp/                   # NLP modules (8 files)
├── risk/                  # Risk assessment (3 files)
├── llm/                   # LLM integration (3 files)
├── utils/                 # Utilities (4 files)
└── templates/             # Contract templates (4 files)
```

**Code Metrics**: ~6,000+ lines across 20+ modules

---

## 🚀 How to Use

1. **Get API Key**: Obtain from [platform.openai.com](https://platform.openai.com)
2. **Enter Key**: Paste in sidebar
3. **Upload Contract**: PDF, DOCX, or TXT
4. **View Analysis**: Navigate through 6 tabs
5. **Export Report**: Download PDF for consultation

---

## 🎯 Impact

- **Cost Savings**: Reduce legal consultation costs by 60-70%
- **Time Efficiency**: Analyze contracts in under 60 seconds
- **Risk Mitigation**: Identify unfavorable terms before signing
- **Compliance Confidence**: Verify adherence to Indian laws

---

## ⚠️ Disclaimer

This tool provides AI-assisted contract analysis for educational purposes only. It does not constitute legal advice. Always consult qualified legal professionals before making decisions.

---

**Made with ❤️ for Indian SMEs**
