# ⚖️ Legal Assistant for Indian SMEs

A sophisticated GenAI-powered legal assistant that helps small and medium business owners understand complex contracts, identify potential legal risks, and receive actionable advice in plain language.

![Legal Assistant](https://img.shields.io/badge/GenAI-Powered-blue) ![Python](https://img.shields.io/badge/Python-3.9+-green) ![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red) ![GPT-4](https://img.shields.io/badge/OpenAI-GPT--4o-orange)

## 🎯 Problem Statement

Indian SMEs often lack access to affordable legal expertise to review contracts. This leads to:
- Signing unfavorable contract terms unknowingly
- Missing critical compliance requirements
- Exposure to legal and financial risks

## 💡 Solution

Our Legal Assistant provides:
- **AI-powered contract analysis** using GPT-4o
- **Risk scoring** at clause and contract level
- **Plain-language explanations** of complex legal terms
- **Compliance checking** with Indian laws
- **Actionable recommendations** for negotiation

## ✨ Key Features

### Core NLP Capabilities
- ✅ **Contract Type Classification** - Automatically identifies employment, vendor, lease, partnership, or service contracts
- ✅ **Clause & Sub-Clause Extraction** - AI-powered hierarchical clause extraction
- ✅ **Named Entity Recognition** - Extracts parties, dates, amounts, jurisdiction, liabilities
- ✅ **Obligation Analysis** - Identifies obligations, rights, and prohibitions
- ✅ **Ambiguity Detection** - Flags vague terms like "reasonable", "may", "approximately"
- ✅ **Clause Similarity Matching** - Compares clauses to standard templates

### Risk Assessment
- ✅ **Clause-level Risk Scores** (Low/Medium/High with 0-10 scale)
- ✅ **Contract-level Composite Risk Score**
- ✅ **Risky Clause Detection:**
  - Penalty clauses
  - Indemnity clauses
  - Unilateral termination rights
  - Arbitration & jurisdiction terms
  - Auto-renewal & lock-in periods
  - Non-compete & IP transfer clauses

### User Outputs
- ✅ **Simplified contract summary** in plain English
- ✅ **Clause-by-clause explanations** with key points
- ✅ **Unfavorable clause highlighting** with risk indicators
- ✅ **Suggested renegotiation alternatives**
- ✅ **SME-friendly contract templates** (4 templates included)
- ✅ **PDF & JSON export** for legal review

### Additional Features
- ✅ **Multilingual support** - Hindi detection with English normalization
- ✅ **Indian law compliance** - Checks against Indian business practices
- ✅ **Audit logging** - JSON-based operation logs

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **LLM** | OpenAI GPT-4o |
| **NLP** | Python with regex patterns |
| **UI** | Streamlit |
| **Storage** | Local file & JSON-based logs |
| **File Formats** | PDF, DOCX, TXT |

## 📁 Project Structure

```
legal_assistant/
├── app.py                    # Main Streamlit application
├── config.py                 # Configuration settings
├── requirements.txt          # Dependencies
├── nlp/                      # NLP modules
│   ├── contract_classifier.py
│   ├── clause_extractor.py
│   ├── ai_clause_extractor.py
│   ├── entity_recognizer.py
│   ├── obligation_analyzer.py
│   ├── ambiguity_detector.py
│   ├── clause_matcher.py
│   └── multilingual.py
├── risk/                     # Risk assessment modules
│   ├── risk_scorer.py
│   ├── clause_analyzers.py
│   └── compliance_checker.py
├── llm/                      # LLM integration
│   ├── chain.py
│   ├── prompts.py
│   └── summarizer.py
├── utils/                    # Utility modules
│   ├── file_handlers.py
│   ├── text_preprocessing.py
│   └── audit_logger.py
└── templates/                # Contract templates
    ├── employment_agreement.json
    ├── service_contract.json
    ├── vendor_contract.json
    └── lease_agreement.json
```

## 🚀 Installation

### Prerequisites
- Python 3.9+
- OpenAI API Key

### Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/legal-assistant-sme.git
cd legal-assistant-sme

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

## 🎮 Usage

1. **Enter API Key** - Provide your OpenAI API key in the sidebar
2. **Upload Contract** - Upload PDF, DOCX, or TXT file
3. **View Analysis** - Navigate through tabs:
   - 📊 **Overview** - Contract type, risk score, extracted entities (AI-powered)
   - 📋 **Clauses** - AI-extracted clauses with risk indicators
   - 🔍 **Analysis** - Deep analysis: ambiguity detection, clause similarity, obligation breakdown, risk details
   - ✅ **Compliance** - Indian law compliance check
   - 💡 **Recommendations** - AI-powered negotiation suggestions
   - 📥 **Export** - Download PDF/JSON reports

## 🔧 Configuration

Edit `config.py` to customize:
- `LLM_MODEL` - OpenAI model (default: gpt-4o)
- `MAX_FILE_SIZE` - Max upload size (default: 15MB)
- `CONTRACT_TYPES` - Supported contract types

## ⚠️ Disclaimer

This tool is for educational and informational purposes only. It does not constitute legal advice. Always consult a qualified legal professional before making decisions based on contract analysis.

## 📄 License

MIT License - see LICENSE file for details.

## 👥 Team

Built for the GenAI Hackathon 2026

---

**Made with ❤️ for Indian SMEs**
