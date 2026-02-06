"""
Legal Assistant for SMEs - Main Streamlit Application
A GenAI-powered contract analysis platform
"""
import streamlit as st
import os
import sys
import json
import hashlib
import time
from datetime import datetime
from io import BytesIO

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    APP_NAME, APP_VERSION, SUPPORTED_EXTENSIONS, CONTRACT_TYPES,
    MODEL_OPTIONS, TOKENS_PER_PAGE, MAX_FILE_SIZE_MB
)
from utils.file_handlers import extract_text
from utils.text_preprocessing import clean_text, detect_language, segment_paragraphs
from utils.audit_logger import get_audit_logger
from utils.logging_config import get_logger
from nlp.contract_classifier import classify_contract, get_contract_type_features
from nlp.clause_extractor import extract_clauses, clauses_to_dict
from nlp.ai_clause_extractor import extract_clauses_with_ai, get_clause_count
from nlp.entity_recognizer import extract_entities, entities_to_dict
from nlp.obligation_analyzer import analyze_obligations, obligations_to_dict, get_obligations_summary
from nlp.multilingual import is_hindi, get_language_stats
from nlp.ambiguity_detector import detect_ambiguities, get_top_ambiguities
from nlp.clause_matcher import match_clauses_to_templates, get_low_similarity_clauses
from risk.risk_scorer import calculate_clause_risk, calculate_contract_risk, ClauseRisk
from risk.clause_analyzers import run_all_analyzers
from risk.compliance_checker import check_compliance, get_indian_law_notes
from llm.chain import get_llm_chain
from llm.summarizer import generate_contract_summary, generate_risk_report

# Initialize logger
logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title=APP_NAME,
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional legal theme
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #1e3a5f;
        --secondary-color: #2c5282;
        --accent-color: #4299e1;
        --success-color: #48bb78;
        --warning-color: #ed8936;
        --danger-color: #f56565;
        --bg-dark: #1a202c;
        --bg-card: #2d3748;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2c5282 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2rem;
    }
    
    .main-header p {
        color: #a0aec0;
        margin: 0.5rem 0 0 0;
    }
    
    /* Risk score gauge */
    .risk-gauge {
        text-align: center;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
    }
    
    .risk-low { background: linear-gradient(135deg, #276749 0%, #48bb78 100%); }
    .risk-medium { background: linear-gradient(135deg, #c05621 0%, #ed8936 100%); }
    .risk-high { background: linear-gradient(135deg, #c53030 0%, #f56565 100%); }
    
    .risk-score {
        font-size: 3rem;
        font-weight: bold;
        color: white;
    }
    
    .risk-label {
        font-size: 1.2rem;
        color: rgba(255, 255, 255, 0.9);
    }
    
    /* Card styling */
    .info-card {
        background: #2d3748;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #4299e1;
    }
    
    .warning-card {
        background: #2d3748;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #ed8936;
    }
    
    .danger-card {
        background: #2d3748;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #f56565;
    }
    
    /* Entity tags */
    .entity-tag {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        margin: 0.25rem;
        border-radius: 20px;
        font-size: 0.875rem;
    }
    
    .entity-party { background: #4299e1; color: white; }
    .entity-date { background: #48bb78; color: white; }
    .entity-money { background: #ed8936; color: white; }
    .entity-jurisdiction { background: #9f7aea; color: white; }
    
    /* Clause cards */
    .clause-card {
        background: #2d3748;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        transition: all 0.2s;
    }
    
    .clause-card:hover {
        background: #3d4a5c;
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background: #1a202c;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #2c5282 0%, #4299e1 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(66, 153, 225, 0.4);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: #2d3748;
        border-radius: 8px 8px 0 0;
        padding: 0.75rem 1.5rem;
    }
    
    .stTabs [aria-selected="true"] {
        background: #4299e1;
    }
    
    /* Progress bar */
    .progress-bar {
        height: 8px;
        background: #2d3748;
        border-radius: 4px;
        overflow: hidden;
    }
    
    .progress-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.3s;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    if 'contract_text' not in st.session_state:
        st.session_state.contract_text = None
    if 'document_hash' not in st.session_state:
        st.session_state.document_hash = None
    if 'session_id' not in st.session_state:
        st.session_state.session_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:12]
    if 'user_api_key' not in st.session_state:
        st.session_state.user_api_key = ""
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = "gpt-4o"


def render_header():
    """Render the main header."""
    st.markdown(f"""
    <div class="main-header">
        <h1>⚖️ {APP_NAME}</h1>
        <p>AI-powered contract analysis for Indian SMEs • Understand, Analyze, Protect</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Render the sidebar with upload and settings."""
    with st.sidebar:
        # ----- API KEY CHECK -----
        user_api_key = st.session_state.get("user_api_key", "")
        has_api_key = bool(user_api_key)
        
        # Status banner
        if has_api_key:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #4caf50, #388e3c); 
                        padding: 0.75rem; border-radius: 8px; margin-bottom: 1rem; text-align: center;">
                <strong style="color: white;">✅ API Key Configured</strong>
                <p style="color: white; font-size: 0.8rem; margin: 0.25rem 0 0 0;">
                    Ready to analyze contracts
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #f44336, #d32f2f); 
                        padding: 0.75rem; border-radius: 8px; margin-bottom: 1rem; text-align: center;">
                <strong style="color: white;">⚠️ API Key Required</strong>
                <p style="color: white; font-size: 0.8rem; margin: 0.25rem 0 0 0;">
                    Enter your OpenAI API key below
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("### 📄 Upload Contract")
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["pdf", "docx", "doc", "txt"],
            help=f"Supported: PDF, DOCX, DOC, TXT • Max: {MAX_FILE_SIZE_MB}MB"
        )
        
        st.markdown("---")
        
        # ----- API KEY SECTION -----
        st.markdown("### 🔑 API Configuration")
        
        # API Key input
        api_key_input = st.text_input(
            "Your OpenAI API Key",
            type="password",
            value=user_api_key,
            help="Required - Get your API key from platform.openai.com"
        )
        
        # Save to session state
        if api_key_input != st.session_state.get("user_api_key", ""):
            st.session_state.user_api_key = api_key_input
            if api_key_input:
                os.environ["OPENAI_API_KEY"] = api_key_input
        
        if not has_api_key:
            st.warning("🔑 **Please enter your OpenAI API key to use AI features.**")
            st.markdown("[Get API Key →](https://platform.openai.com/api-keys)")
        
        st.markdown("---")
        
        # ----- MODEL SELECTION -----
        st.markdown("### 🤖 Model Selection")
        
        # Create options list from MODEL_OPTIONS
        model_options = list(MODEL_OPTIONS.keys())
        model_labels = [MODEL_OPTIONS[m]["name"] for m in model_options]
        
        selected_model = st.selectbox(
            "Select AI Model",
            options=model_options,
            format_func=lambda x: MODEL_OPTIONS[x]["name"],
            index=0,  # GPT-4o is default (first option)
            help="GPT-4o is a GPT-4-class model optimized for speed and cost. GPT-4 is available for users who prefer the original model."
        )
        
        st.session_state.selected_model = selected_model
        
        # Model info tooltip
        st.caption(f"ℹ️ {MODEL_OPTIONS[selected_model]['description']}")
        
        st.markdown("---")
        
        # ----- ANALYSIS OPTIONS -----
        st.markdown("### 🔧 Analysis Options")
        
        include_llm = st.checkbox(
            "Enable AI Analysis",
            value=True,
            help="Use AI for detailed explanations and summaries"
        )
        
        show_raw_text = st.checkbox(
            "Show Raw Text",
            value=False,
            help="Display extracted contract text"
        )
        
        st.markdown("---")
        
        # ----- QUICK STATS -----
        st.markdown("### 📊 Quick Stats")
        if st.session_state.analysis_result:
            result = st.session_state.analysis_result
            st.metric("Contract Type", result.get("contract_type", "N/A"))
            st.metric("Risk Score", f"{result.get('risk_score', 0):.1f}/10")
            st.metric("Clauses Found", result.get("clause_count", 0))
        
        st.markdown("---")
        st.markdown(f"<small>Version {APP_VERSION}</small>", unsafe_allow_html=True)
        
        return uploaded_file, include_llm, show_raw_text, selected_model


def analyze_contract(text: str, filename: str, use_ai_extraction: bool = True) -> dict:
    """Perform complete contract analysis."""
    logger.info(f"Starting contract analysis for: {filename}")
    logger.debug(f"Text length: {len(text)} chars, AI extraction: {use_ai_extraction}")
    
    result = {
        "filename": filename,
        "timestamp": datetime.now().isoformat()
    }
    
    # Clean text
    cleaned_text = clean_text(text)
    result["text_length"] = len(cleaned_text)
    logger.debug(f"Cleaned text length: {len(cleaned_text)} chars")
    
    # Language detection
    lang_stats = get_language_stats(cleaned_text)
    result["language"] = lang_stats
    logger.info(f"Language detected: {lang_stats.get('primary_language', 'unknown')}")
    
    # Contract classification
    contract_type, confidence, all_scores = classify_contract(cleaned_text)
    result["contract_type"] = contract_type
    result["classification_confidence"] = confidence
    logger.info(f"Contract classified as: {contract_type} (confidence: {confidence:.2f})")
    
    # Entity extraction
    # Regex based first
    entities = extract_entities(cleaned_text)
    
    # AI based override if enabled
    has_api_key = bool(os.getenv("OPENAI_API_KEY"))
    if use_ai_extraction and has_api_key:
        try:
            from llm.summarizer import extract_entities_with_ai
            logger.info("Extracting entities with AI...")
            
            # User Request: "Use full AI to extract every values" (Disable regex for these types)
            # We explicitly clear regex results to prevent noise (e.g., "India including...")
            entities["JURISDICTION"] = []
            entities["MONEY"] = []
            entities["PARTY"] = []
            # Note: We keep DATE regex as backup/supplement because dates are strictly formatted
            
            ai_entities = extract_entities_with_ai(cleaned_text)
            
            if ai_entities:
                # Override regex results completely with AI results for cleaner data
                from nlp.entity_recognizer import Entity
                
                # JURISDICTION
                if ai_entities.get("JURISDICTION"):
                    entities["JURISDICTION"] = [
                        Entity(text=j, entity_type="JURISDICTION", start=0, end=0, context="Extracted by AI")
                        for j in ai_entities["JURISDICTION"] if isinstance(j, str) and j.strip()
                    ]
                
                # PARTY - filter out placeholder patterns
                if ai_entities.get("PARTY"):
                    valid_parties = []
                    invalid_patterns = [".....", "m/s ...", "___", "[", "]", "party 1", "party 2", "first party", "second party"]
                    for p in ai_entities["PARTY"]:
                        if isinstance(p, str) and p.strip():
                            clean_p = p.lower().strip()
                            # Skip if it matches invalid patterns or is too short
                            if len(p.strip()) > 3 and not any(inv in clean_p for inv in invalid_patterns):
                                valid_parties.append(
                                    Entity(text=p.strip(), entity_type="PARTY", start=0, end=0, context="Extracted by AI")
                                )
                    if valid_parties:
                        entities["PARTY"] = valid_parties
                
                # MONEY - pure AI extraction as requested
                if ai_entities.get("MONEY"):
                    valid_money = []
                    indicators = ["rs", "inr", "₹", "rupee", "lakh", "lac", "crore", "usd", "$", "dollar"]
                    for m in ai_entities["MONEY"]:
                        if isinstance(m, str):
                            clean_m = m.lower().strip()
                            # Apply loose currency filter for AI (trusting AI more but still checking context)
                            if any(ind in clean_m for ind in indicators) or any(char.isdigit() for char in m):
                                valid_money.append(
                                     Entity(text=m, entity_type="MONEY", start=0, end=0, context="Extracted by AI")
                                )
                    if valid_money:
                        entities["MONEY"] = valid_money
                
                # DATES - Merge AI dates with regex (Regex is usually better for specific formats, AI for "Effective Date")
                if ai_entities.get("DATE"):
                     # We'll prepend AI dates as they are likely key dates like 'Effective Date'
                     ai_dates = [
                        Entity(text=d, entity_type="DATE", start=0, end=0, context="Extracted by AI")
                        for d in ai_entities["DATE"] if isinstance(d, str) and d.strip()
                     ]
                     # Keep regex dates that don't overlap too much?
                     # User wants AI. Let's make AI primary.
                     entities["DATE"] = ai_dates + [e for e in entities["DATE"] if e.text not in [d.text for d in ai_dates]]

                logger.info(f"AI entity extraction complete. Overwrote regex results.")
        except Exception as e:
            logger.error(f"AI entity extraction failed: {e}")

    result["entities"] = entities_to_dict(entities)
    logger.debug(f"Extracted entities: {len(result['entities'])} types")
    
    # Clause extraction - Try AI first, fallback to regex
    ai_clauses = None
    # Check for user API key
    has_api_key = bool(os.getenv("OPENAI_API_KEY"))
    if use_ai_extraction and has_api_key:
        logger.info("Attempting AI-powered clause extraction...")
        ai_result = extract_clauses_with_ai(cleaned_text)
        if ai_result["success"]:
            ai_clauses = ai_result["clauses"]
            result["clauses"] = ai_clauses
            result["clause_count"] = get_clause_count(ai_result)
            result["extraction_method"] = "ai"
            result["ai_tokens_used"] = ai_result.get("tokens_used", 0)
            logger.info(f"AI extraction successful: {result['clause_count']} clauses, {result['ai_tokens_used']} tokens used")
        else:
            logger.warning(f"AI extraction failed: {ai_result.get('error', 'Unknown error')}")
    
    # Fallback to regex-based extraction
    if ai_clauses is None:
        logger.info("Using regex-based clause extraction...")
        clauses = extract_clauses(cleaned_text)
        result["clauses"] = clauses_to_dict(clauses)
        result["clause_count"] = len(clauses)
        result["extraction_method"] = "regex"
        logger.info(f"Regex extraction complete: {result['clause_count']} clauses found")
    
    # Obligation analysis
    obligations = analyze_obligations(cleaned_text)
    result["obligations"] = obligations_to_dict(obligations)
    result["obligations_summary"] = get_obligations_summary(obligations)
    logger.debug(f"Obligations analyzed: {len(result['obligations'])} found")
    
    # Risk analysis for each clause
    clause_risks = []
    for i, clause in enumerate(result["clauses"]):
        clause_id = clause.get("id", f"clause_{i}")
        title = clause.get("title", f"Clause {i+1}")
        content = clause.get("content", "")
        clause_type = clause.get("clause_type", "general")
        
        # Use AI-provided risk level if available
        if "risk_level" in clause:
            from risk.risk_scorer import RiskLevel
            level_str = clause.get("risk_level", "low")
            level_enum = RiskLevel.HIGH if level_str == "high" else RiskLevel.MEDIUM if level_str == "medium" else RiskLevel.LOW
            risk = ClauseRisk(
                clause_id=clause_id,
                clause_title=title,
                clause_type=clause_type,
                risk_level=level_enum,
                risk_score={"low": 2, "medium": 5, "high": 8}.get(level_str, 3),
                risk_factors=[],
                alternatives=[]
            )
        else:
            risk = calculate_clause_risk(clause_id, title, content, clause_type)
        clause_risks.append(risk)
    
    # Contract-level risk
    contract_risk = calculate_contract_risk(clause_risks)
    result["risk_score"] = contract_risk.overall_score
    result["risk_level"] = contract_risk.risk_level.value
    result["risk_summary"] = contract_risk.summary
    result["top_concerns"] = contract_risk.top_concerns
    result["recommendations"] = contract_risk.recommendations
    
    # Generate AI-powered recommendations if LLM is enabled
    if use_ai_extraction and os.getenv("OPENAI_API_KEY"):
        try:
            logger.info("Generating AI recommendations...")
            from llm.summarizer import generate_ai_recommendations
            from risk.risk_scorer import RiskLevel
            
            # Filter for high/medium risk clauses
            risky_clauses = [
                cr.to_dict() for cr in clause_risks 
                if cr.risk_level in [RiskLevel.HIGH, RiskLevel.MEDIUM]
            ]
            
            ai_recs = generate_ai_recommendations(
                contract_type=result.get("contract_type", "General"),
                risk_score=result["risk_score"],
                high_risk_clauses=risky_clauses
            )
            
            if ai_recs:
                result["recommendations"] = ai_recs
                logger.info(f"Generated {len(ai_recs)} AI recommendations")
            
            # Generate AI-powered top concerns
            from llm.summarizer import generate_ai_top_concerns
            ai_concerns = generate_ai_top_concerns(
                contract_type=result.get("contract_type", "General"),
                risk_score=result["risk_score"],
                high_risk_clauses=risky_clauses
            )
            
            if ai_concerns:
                result["top_concerns"] = ai_concerns
                logger.info(f"Generated {len(ai_concerns)} AI top concerns")
                
        except Exception as e:
            logger.error(f"Failed to generate AI recommendations/concerns: {e}")

    # Build clause_risks with content for display
    clause_risks_with_content = []
    for i, cr in enumerate(clause_risks):
        risk_dict = cr.to_dict()
        # Add clause content for display in Risk Analysis
        if i < len(result["clauses"]):
            clause = result["clauses"][i]
            risk_dict["clause_content"] = clause.get("content", "")[:500]
            # Add key_points for richer explanations
            if clause.get("key_points"):
                risk_dict["key_points"] = clause.get("key_points")
        clause_risks_with_content.append(risk_dict)
    
    result["clause_risks"] = clause_risks_with_content
    
    # Specialized clause analysis
    clause_analysis = run_all_analyzers(cleaned_text)
    result["clause_analysis"] = {k: v.to_dict() for k, v in clause_analysis.items()}
    
    # Compliance check
    compliance = check_compliance(cleaned_text, contract_type)
    result["compliance"] = compliance.to_dict()
    result["indian_law_notes"] = get_indian_law_notes(contract_type)
    
    # Ambiguity detection
    ambiguity_report = detect_ambiguities(cleaned_text)
    result["ambiguity"] = ambiguity_report.to_dict()
    result["clarity_score"] = ambiguity_report.clarity_score
    
    # Clause similarity matching
    similarity_report = match_clauses_to_templates(result["clauses"], contract_type)
    result["similarity"] = similarity_report.to_dict()
    result["standard_compliance_score"] = similarity_report.standard_compliance_score
    
    return result


def render_risk_gauge(risk_score: float, risk_level: str):
    """Render the risk score gauge."""
    risk_class = f"risk-{risk_level}"
    
    st.markdown(f"""
    <div class="risk-gauge {risk_class}">
        <div class="risk-score">{risk_score:.1f}/10</div>
        <div class="risk-label">{risk_level.upper()} RISK</div>
    </div>
    """, unsafe_allow_html=True)


def render_entities(entities: dict):
    """Render extracted entities."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 👥 Parties")
        parties = entities.get("PARTY", [])
        if parties:
            for party in parties[:5]:
                text = party.get("text", "") if isinstance(party, dict) else str(party)
                st.markdown(f'<span class="entity-tag entity-party">{text}</span>', unsafe_allow_html=True)
        else:
            st.info("No parties identified")
        
        st.markdown("#### 📅 Key Dates")
        dates = entities.get("DATE", [])
        if dates:
            for date in dates[:5]:
                text = date.get("text", "") if isinstance(date, dict) else str(date)
                st.markdown(f'<span class="entity-tag entity-date">{text}</span>', unsafe_allow_html=True)
        else:
            st.info("No dates identified")
    
    with col2:
        st.markdown("#### 💰 Financial Values")
        money = entities.get("MONEY", [])
        if money:
            for amount in money[:5]:
                text = amount.get("text", "") if isinstance(amount, dict) else str(amount)
                st.markdown(f'<span class="entity-tag entity-money">{text}</span>', unsafe_allow_html=True)
        else:
            st.info("No amounts identified")
        
        st.markdown("#### 🏛️ Jurisdiction")
        jurisdiction = entities.get("JURISDICTION", [])
        if jurisdiction:
            for j in jurisdiction[:3]:
                text = j.get("text", "") if isinstance(j, dict) else str(j)
                st.markdown(f'<span class="entity-tag entity-jurisdiction">{text}</span>', unsafe_allow_html=True)
        else:
            st.info("No jurisdiction identified")


# Import advanced NLP modules
from nlp.ambiguity_detector import detect_ambiguities, get_top_ambiguities
from nlp.clause_matcher import match_clauses_to_templates
from nlp.obligation_analyzer import analyze_obligations, get_obligations_summary, get_high_risk_obligations, ObligationType

def render_advanced_analysis(text: str, clauses: list, contract_type: str):
    """Render advanced NLP analysis tab."""
    st.markdown("### 🔬 Advanced Contract Analytics")
    
    col1, col2, col3 = st.columns(3)
    
    # 1. Ambiguity Analysis
    with st.spinner("Analyzing ambiguity..."):
        ambiguity_report = detect_ambiguities(text)
    
    with col1:
        st.metric("Clarity Score", f"{ambiguity_report.clarity_score}/100", 
                 delta="Clear" if ambiguity_report.clarity_score > 80 else "-Ambiguous",
                 delta_color="normal" if ambiguity_report.clarity_score > 80 else "inverse")
    
    # 2. Obligation Analysis
    with st.spinner("Mapping obligations..."):
        obligations = analyze_obligations(text)
        ob_summary = get_obligations_summary(obligations)
    
    with col2:
        st.metric("Total Obligations", ob_summary["total"], 
                 f"{ob_summary['by_type']['obligations']} mandatory")
                 
    # 3. Standardization
    with st.spinner("Checking standards..."):
        std_report = match_clauses_to_templates(clauses, contract_type)
        
    with col3:
        st.metric("Standard Score", f"{std_report.standard_compliance_score:.0f}/100",
                 f"{std_report.matched_clauses}/{std_report.total_clauses} matched")

    st.divider()

    # Ambiguity Details
    with st.expander("🔍 Ambiguity Detection Details", expanded=False):
        st.markdown(f"**Analysis:** {ambiguity_report.summary}")
        if ambiguity_report.flags:
            st.dataframe([
                {"Term": f["term"], "Issue": f["category"].replace("_", " ").title(), "Suggestion": f["suggestion"], "Context": f["context"]}
                for f in get_top_ambiguities(ambiguity_report)
            ])
        else:
            st.success("No significant ambiguities found.")

    # Obligation Breakdown
    with st.expander("⚖️ Obligations, Rights & Prohibitions", expanded=False):
        tabs = st.tabs(["🔴 Prohibitions (Must Not)", "🟢 Obligations (Must)", "🔵 Rights (May)"])
        
        high_risk_obs = get_high_risk_obligations(obligations)
        if high_risk_obs:
            st.error(f"⚠️ Found {len(high_risk_obs)} High-Risk Obligations (e.g., Penalties, Prohibitions)")
        
        with tabs[0]:
            prohibitions = [o for o in obligations if o.obligation_type == ObligationType.PROHIBITION]
            if prohibitions:
                for p in prohibitions:
                    st.markdown(f"- **{p.subject}**: {p.action} {f'_(If: {p.condition})_' if p.condition else ''}")
            else:
                st.info("No explicit prohibitions found.")
                
        with tabs[1]:
            mandatory = [o for o in obligations if o.obligation_type == ObligationType.OBLIGATION]
            if mandatory:
                for m in mandatory[:10]: # Limit for brevity
                    st.markdown(f"- **{m.subject}**: {m.action}")
                if len(mandatory) > 10:
                    st.caption(f"And {len(mandatory)-10} more...")
            else:
                st.info("No mandatory obligations detected.")
                
        with tabs[2]:
            rights = [o for o in obligations if o.obligation_type == ObligationType.RIGHT]
            if rights:
                for r in rights[:10]:
                    st.markdown(f"- **{r.subject}**: {r.action}")
            else:
                st.info("No explicit rights detected.")

    # Standardization Check
    with st.expander("📏 Standardization & Template Compliance", expanded=False):
        st.markdown(f"**Analysis:** {std_report.summary}")
        if std_report.non_standard_clauses:
            st.warning(f"**Non-Standard Clauses:** {', '.join(std_report.non_standard_clauses)}")
        
        # Show comparison table for low match clauses
        low_sim = [m for m in std_report.matches if m.match_level in ["low", "no_match"]]
        if low_sim:
            st.markdown("### Significant Deviations")
            for m in low_sim[:5]:
                st.text(f"Clause: {m.clause_title} (vs Standard {m.template_clause_title})")
                st.caption(f"Similarity: {m.similarity_score}% - {', '.join(m.deviations[:2])}")

    
    
def render_clauses(clauses: list, clause_risks: list):
    """Render extracted clauses with risk indicators."""
    st.markdown("### 📋 Contract Clauses")
    
    if not os.getenv("OPENAI_API_KEY"):
        st.warning("⚠️ **Using Basic Regex Mode** - Enter your OpenAI API key in the sidebar for AI analysis & risk scoring.")
    
    if not clauses:
        if not os.getenv("OPENAI_API_KEY"):
            st.warning("🔑 **API Key Required** - Enter your OpenAI API key in the sidebar to enable AI-powered clause extraction.")
        else:
            st.info("No clauses extracted. Try uploading a contract with clear section headers.")
        return
    
    # Create risk lookup
    risk_lookup = {cr["clause_id"]: cr for cr in clause_risks}
    
    for i, clause in enumerate(clauses):
        clause_id = clause.get("id", f"clause_{i}")
        title = clause.get("title", f"Clause {i+1}")
        clause_type = clause.get("clause_type", "general")
        content = clause.get("content", "")[:500]
        key_points = clause.get("key_points", [])
        sub_clauses = clause.get("sub_clauses", [])
        
        # Get risk info - from clause directly (AI) or from risk lookup
        risk_level = clause.get("risk_level") or risk_lookup.get(clause_id, {}).get("risk_level", "low")
        risk_info = risk_lookup.get(clause_id, {})
        risk_score = risk_info.get("risk_score", {"low": 2, "medium": 5, "high": 8}.get(risk_level, 3))
        
        # Risk indicator
        if risk_level == "high":
            risk_icon = "🔴"
        elif risk_level == "medium":
            risk_icon = "🟡"
        else:
            risk_icon = "🟢"
        
        with st.expander(f"{risk_icon} **{title}** ({clause_type}) - Risk: {risk_score:.1f}/10"):
            # Key points (AI-generated)
            if key_points:
                st.markdown("**📌 Key Points:**")
                for point in key_points:
                    st.markdown(f"- {point}")
                st.markdown("")
            
            # Content
            if content:
                st.markdown(f"**Content:**\n{content}{'...' if len(clause.get('content', '')) > 500 else ''}")
            
            # Sub-clauses
            if sub_clauses:
                st.markdown("**Sub-clauses:**")
                for sub in sub_clauses:
                    sub_title = sub.get("title", sub.get("clause_number", ""))
                    sub_risk = sub.get("risk_level", "low")
                    sub_icon = "🔴" if sub_risk == "high" else "🟡" if sub_risk == "medium" else "🟢"
                    st.markdown(f"- {sub_icon} **{sub_title}**: {sub.get('content', '')[:100]}...")
            
            # Risk factors
            if risk_info.get("risk_factors"):
                st.markdown("**⚠️ Risk Factors:**")
                for rf in risk_info["risk_factors"]:
                    desc = rf.get("description", "") if isinstance(rf, dict) else str(rf)
                    st.markdown(f"- {desc}")
            
            # Alternatives
            if risk_info.get("alternatives"):
                st.markdown("**💡 Suggested Alternatives:**")
                for alt in risk_info["alternatives"][:2]:
                    st.markdown(f"- {alt}")



def render_risk_analysis(clause_risks: list, risk_score: float):
    """Render risk analysis dashboard."""
    st.markdown("### ⚠️ Risk Analysis")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Risk gauge
        if risk_score >= 7.0:
            color = "#f56565"  # Red
            level = "HIGH RISK"
        elif risk_score >= 4.0:
            color = "#ed8936"  # Orange
            level = "MEDIUM RISK"
        else:
            color = "#48bb78"  # Green
            level = "LOW RISK"
            
        st.markdown(f"""
        <div style="text-align: center; padding: 1.5rem; background: {color}; border-radius: 8px; margin-bottom: 1rem;">
            <h1 style="color: white; margin: 0; font-size: 3rem;">{risk_score:.1f}</h1>
            <h3 style="color: white; margin: 0;">{level}</h3>
            <p style="color: white; margin: 0;">Risk Score</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        # High risk summary
        high_risks = [r for r in clause_risks if r.get("risk_score", 0) >= 7]
        med_risks = [r for r in clause_risks if 4 <= r.get("risk_score", 0) < 7]
        
        st.markdown(f"**Found {len(clause_risks)} risky clauses:**")
        st.markdown(f"- 🔴 **{len(high_risks)} High Risk** clauses")
        st.markdown(f"- 🟠 **{len(med_risks)} Medium Risk** clauses")
        
        if not clause_risks:
            st.success("✅ No significant risks detected based on standard patterns.")

    st.divider()
    
    # Detailed Risk List
    if clause_risks:
        st.markdown("#### 📋 Detailed Issues")
        for risk in sorted(clause_risks, key=lambda x: x.get("risk_score", 0), reverse=True):
            score = risk.get("risk_score", 0)
            if score >= 7:
                icon = "🔴"
            elif score >= 4:
                icon = "🟠"
            else:
                icon = "🟢"
                
            with st.expander(f"{icon} {risk.get('clause_id', 'Unknown Clause')}: {risk.get('clause_type', 'General')} (Score: {score})"):
                # Extract explanation from risk_factors if available
                risk_factors = risk.get('risk_factors', [])
                if risk_factors:
                    explanations = [rf.get('description', '') for rf in risk_factors if rf.get('description')]
                    explanation = "; ".join(explanations[:3]) if explanations else "Risk identified based on clause patterns."
                else:
                    explanation = "Risk identified based on clause patterns."
                
                st.markdown(f"**Issue:** {explanation}")
                
                # Show clause content
                clause_content = risk.get('clause_content', '') or risk.get('clause_title', '')
                if clause_content:
                    st.info(f"**Clause:** \"{clause_content[:300]}{'...' if len(str(clause_content)) > 300 else ''}\"")
                
                # Show alternatives/recommendations
                alternatives = risk.get("alternatives", [])
                if alternatives:
                    st.markdown("**💡 Suggested Alternatives:**")
                    for alt in alternatives[:2]:
                        st.markdown(f"- {alt}")


def render_compliance(compliance: dict, law_notes: list):
    """Render compliance section."""
    st.markdown("### ✅ Compliance Check")
    
    score = compliance.get("score", 0)
    is_compliant = compliance.get("is_compliant", False)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        color = "#48bb78" if is_compliant else "#f56565"
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: {color}; border-radius: 8px;">
            <h2 style="color: white; margin: 0;">{score:.0f}%</h2>
            <p style="color: white; margin: 0;">Compliance Score</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        issues = compliance.get("issues", [])
        high_issues = [i for i in issues if i.get("severity") == "high"]
        
        if high_issues:
            st.error(f"⚠️ {len(high_issues)} critical compliance issues found")
            for issue in high_issues[:3]:
                st.markdown(f"- {issue.get('description', '')}")
        else:
            st.success("✅ No critical compliance issues")
    
    # Indian law notes
    if law_notes:
        with st.expander("📚 Relevant Indian Law Considerations"):
            for note in law_notes:
                st.markdown(f"- {note}")


def render_ambiguity(ambiguity: dict):
    """Render ambiguity detection results."""
    st.markdown("### 🔍 Ambiguity Detection")
    
    clarity_score = ambiguity.get("clarity_score", 0)
    total_flags = ambiguity.get("total_flags", 0)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Clarity score gauge
        if clarity_score >= 70:
            color = "#48bb78"  # Green
        elif clarity_score >= 50:
            color = "#ed8936"  # Orange
        else:
            color = "#f56565"  # Red
        
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: {color}; border-radius: 8px;">
            <h2 style="color: white; margin: 0;">{clarity_score:.0f}%</h2>
            <p style="color: white; margin: 0;">Clarity Score</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.metric("Total Ambiguities", total_flags)
    
    with col3:
        st.metric("High Severity", ambiguity.get("high_severity_count", 0))
    
    # Summary
    st.markdown(f"**Summary:** {ambiguity.get('summary', '')}")
    
    # Detailed flags
    flags = ambiguity.get("flags", [])
    if flags:
        with st.expander(f"📋 View All Ambiguities ({len(flags)} found)"):
            for i, flag in enumerate(flags[:20]):  # Limit to 20
                severity = flag.get("severity", "low")
                if severity == "high":
                    icon = "🔴"
                elif severity == "medium":
                    icon = "🟡"
                else:
                    icon = "🟢"
                
                st.markdown(f"""
                **{icon} {flag.get('term', '')}** ({flag.get('category', '').replace('_', ' ')})
                - Context: *{flag.get('context', '')}*
                - 💡 Suggestion: {flag.get('suggestion', '')}
                ---
                """)


def render_similarity(similarity: dict):
    """Render clause similarity matching results."""
    st.markdown("### 📊 Standard Template Comparison")
    
    compliance_score = similarity.get("standard_compliance_score", 0)
    avg_similarity = similarity.get("average_similarity", 0)
    matched = similarity.get("matched_clauses", 0)
    total = similarity.get("total_clauses", 0)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if compliance_score >= 70:
            color = "#48bb78"
        elif compliance_score >= 50:
            color = "#ed8936"
        else:
            color = "#f56565"
        
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: {color}; border-radius: 8px;">
            <h2 style="color: white; margin: 0;">{compliance_score:.0f}%</h2>
            <p style="color: white; margin: 0;">Standard Compliance</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.metric("Average Similarity", f"{avg_similarity:.0f}%")
    
    with col3:
        st.metric("Clauses Matched", f"{matched}/{total}")
    
    # Summary
    st.markdown(f"**Summary:** {similarity.get('summary', '')}")
    
    # Non-standard clauses
    non_standard = similarity.get("non_standard_clauses", [])
    if non_standard:
        st.warning(f"⚠️ **Non-Standard Clauses:** {', '.join(non_standard[:5])}")
    
    # Detailed matches
    matches = similarity.get("matches", [])
    if matches:
        with st.expander("📋 Clause-by-Clause Comparison"):
            for match in matches:
                level = match.get("match_level", "low")
                if level == "exact" or level == "high":
                    icon = "✅"
                elif level == "moderate":
                    icon = "🔶"
                else:
                    icon = "⚠️"
                
                st.markdown(f"""
                **{icon} {match.get('clause_title', '')}** → {match.get('template_clause_title', '')}
                - Similarity: **{match.get('similarity_score', 0):.0f}%** ({match.get('match_level', '')})
                """)
                
                deviations = match.get("deviations", [])
                if deviations:
                    for dev in deviations[:3]:
                        st.markdown(f"  - {dev}")
                st.markdown("---")


def render_recommendations(recommendations: list, top_concerns: list):
    """Render recommendations section."""
    st.markdown("### 💡 Recommendations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**⚠️ Top Concerns:**")
        if top_concerns:
            for concern in top_concerns[:5]:
                st.markdown(f"""
                <div class="warning-card">
                    {concern}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No major concerns identified")
    
    with col2:
        st.markdown("**✨ Action Items:**")
        if recommendations:
            for i, rec in enumerate(recommendations[:5], 1):
                st.markdown(f"{i}. {rec}")
        else:
            if not os.getenv("OPENAI_API_KEY"):
                st.warning("🔑 API Key Required for AI recommendations")
            else:
                st.info("No specific recommendations")


def generate_pdf_report(result: dict) -> bytes:
    """Generate PDF report for export."""
    from fpdf import FPDF
    
    def safe_text(text, max_len=400):
        """Sanitize text for PDF - remove special chars, truncate, and break long words."""
        if not text:
            return "N/A"
        # Convert to string and truncate
        text = str(text)[:max_len]
        
        # Replace common unicode with ASCII equivalents FIRST
        replacements = {
            '₹': 'Rs.', '–': '-', '—': '-', '"': '"', '"': '"', 
            ''': "'", ''': "'", '•': '-', '→': '->', '←': '<-',
            '…': '...', '\u200b': '', '\xa0': ' ', '\t': ' '
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        
        # Remove/replace problematic characters
        try:
            text = text.encode('latin-1', 'replace').decode('latin-1')
        except:
            text = text.encode('ascii', 'replace').decode('ascii')
        
        # Break very long words (prevent FPDF horizontal overflow)
        words = text.split()
        safe_words = []
        for word in words:
            if len(word) > 40:
                # Break long words
                safe_words.append(word[:40] + "...")
            else:
                safe_words.append(word)
        text = ' '.join(safe_words)
        
        # Remove multiple spaces
        while '  ' in text:
            text = text.replace('  ', ' ')
        
        return text.strip() if text.strip() else "N/A"
    
    def safe_multi_cell(pdf_obj, h, txt):
        """Wrapper for multi_cell with error handling. Uses full usable width."""
        # A4 page is 210mm, with 15mm margins on each side = 180mm usable
        w = 180
        try:
            pdf_obj.multi_cell(w, h, txt)
        except Exception:
            try:
                pdf_obj.multi_cell(w, h, str(txt)[:80])
            except:
                pdf_obj.cell(w, h, "Error", ln=True)
    
    pdf = FPDF()
    pdf.set_margins(15, 15, 15)  # MUST be set BEFORE add_page
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Title
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Contract Analysis Report", ln=True, align="C")
    pdf.ln(10)
    
    # Contract info
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, safe_text(f"Contract Type: {result.get('contract_type', 'N/A')}", 60), ln=True)
    pdf.cell(0, 10, safe_text(f"Risk Level: {str(result.get('risk_level', 'N/A')).upper()}", 30), ln=True)
    pdf.cell(0, 10, f"Risk Score: {result.get('risk_score', 0):.1f}/10", ln=True)
    pdf.cell(0, 10, f"Analysis Date: {str(result.get('timestamp', 'N/A'))[:10]}", ln=True)
    pdf.ln(10)
    
    # Risk Summary
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Risk Assessment Summary", ln=True)
    pdf.set_font("Helvetica", "", 10)
    safe_multi_cell(pdf, 8, safe_text(result.get("risk_summary", "No summary available"), 500))
    pdf.ln(5)
    
    # Top Concerns
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Top Concerns", ln=True)
    pdf.set_font("Helvetica", "", 10)
    concerns = result.get("top_concerns", [])
    if concerns:
        for concern in concerns[:5]:
            safe_multi_cell(pdf, 8, safe_text(f"- {concern}", 200))
    pdf.ln(5)
    
    # Recommendations
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Recommendations", ln=True)
    pdf.set_font("Helvetica", "", 10)
    recs = result.get("recommendations", [])
    if recs:
        for rec in recs[:5]:
            safe_multi_cell(pdf, 8, safe_text(f"- {rec}", 200))
    pdf.ln(5)
    
    # Compliance
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Compliance Score", ln=True)
    pdf.set_font("Helvetica", "", 10)
    compliance = result.get("compliance", {})
    pdf.cell(0, 8, f"Score: {compliance.get('score', 0):.0f}%", ln=True)
    
    # Disclaimer
    pdf.ln(20)
    pdf.set_font("Helvetica", "I", 8)
    safe_multi_cell(pdf, 5, 
        "DISCLAIMER: This report is AI-generated for educational purposes only. "
        "It does not constitute legal advice. Consult a legal professional."
    )
    
    return bytes(pdf.output())


def render_template_library():
    """Render the contract template library."""
    st.markdown("### 📚 Contract Templates")
    st.markdown("Download SME-friendly contract templates")
    
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    
    if os.path.exists(templates_dir):
        template_files = [f for f in os.listdir(templates_dir) if f.endswith('.json')]
        
        for template_file in template_files:
            template_path = os.path.join(templates_dir, template_file)
            try:
                with open(template_path, 'r') as f:
                    template = json.load(f)
                
                with st.expander(f"📄 {template.get('name', template_file)}"):
                    st.markdown(f"**Description:** {template.get('description', 'N/A')}")
                    st.markdown(f"**Contract Type:** {template.get('contract_type', 'N/A')}")
                    
                    # Show sections
                    st.markdown("**Sections:**")
                    for section in template.get("sections", []):
                        st.markdown(f"- {section.get('title', 'Untitled')}")
                    
                    # Download button
                    template_text = "\n\n".join([
                        f"## {s.get('title', '')}\n\n{s.get('content', '')}"
                        for s in template.get("sections", [])
                    ])
                    
                    st.download_button(
                        label="📥 Download Template",
                        data=template_text,
                        file_name=f"{template.get('template_id', 'template')}.txt",
                        mime="text/plain"
                    )
            except Exception as e:
                st.error(f"Error loading template: {str(e)}")
    else:
        st.info("No templates available")


def estimate_page_count(text: str) -> int:
    """Estimate page count from text (approx 3000 chars per page)."""
    return max(1, len(text) // 3000)


def estimate_token_count(text: str) -> int:
    """Estimate token count (approx 4 chars per token)."""
    return len(text) // 4


def main():
    """Main application entry point."""
    init_session_state()
    render_header()
    
    # Sidebar - returns 4 values (no more is_demo_mode)
    uploaded_file, include_llm, show_raw_text, selected_model = render_sidebar()
    
    # Check if API key is configured
    has_api_key = bool(st.session_state.get("user_api_key", ""))
    
    # Main content area
    if uploaded_file is not None:
        # Process uploaded file
        try:
            logger.info(f"File uploaded: {uploaded_file.name} ({uploaded_file.size} bytes)")
            
            # Get file extension
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            logger.debug(f"File extension: {file_ext}")
            
            # Extract text
            with st.spinner("📄 Extracting text..."):
                file_bytes = BytesIO(uploaded_file.read())
                text, metadata = extract_text(file_bytes=file_bytes, file_extension=file_ext)
            
            # BLOCKER: Only proceed if API key is present
            if not os.getenv("OPENAI_API_KEY"):
                st.info("👋 **Welcome!** Please enter your OpenAI API key in the sidebar to start the analysis.")
                st.stop()
                
            st.session_state.contract_text = text
            st.session_state.document_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
            
            # Log upload
            audit_log = get_audit_logger()
            audit_log.log_upload(
                filename=uploaded_file.name,
                file_size=uploaded_file.size,
                file_type=file_ext,
                content_hash=st.session_state.document_hash,
                session_id=st.session_state.session_id
            )
            
            # Show raw text if requested
            if show_raw_text:
                with st.expander("📝 Extracted Text"):
                    st.text_area("Contract Text", text, height=300)
            
            # Analyze contract (pass selected model)
            with st.spinner("🔍 Analyzing contract..."):
                result = analyze_contract(text, uploaded_file.name, use_ai_extraction=include_llm)
                result["api_mode"] = "user"
                result["model_used"] = selected_model
                st.session_state.analysis_result = result
            
            # Log analysis
            audit_logger = get_audit_logger()
            audit_logger.log_analysis(
                filename=uploaded_file.name,
                content_hash=st.session_state.document_hash,
                analysis_type="full",
                contract_type=result.get("contract_type"),
                risk_score=result.get("risk_score"),
                session_id=st.session_state.session_id
            )
            logger.info(f"Analysis complete: {result.get('contract_type')} - Risk: {result.get('risk_score', 0):.1f}/10")
            
            # Display results in tabs
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                "📊 Overview",
                "📋 Clauses",
                "🔍 Analysis",
                "✅ Compliance",
                "💡 Recommendations",
                "📥 Export"
            ])
            
            with tab1:
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.markdown(f"**Contract Type:** {result.get('contract_type', 'Unknown')}")
                    st.markdown(f"**Classification Confidence:** {result.get('classification_confidence', 0)*100:.0f}%")
                    
                    # Language info
                    lang_stats = result.get("language", {})
                    if lang_stats.get("requires_translation"):
                        st.warning("⚠️ Hindi content detected - translation may be needed")
                    
                    render_risk_gauge(
                        result.get("risk_score", 0),
                        result.get("risk_level", "low")
                    )
                
                with col2:
                    st.markdown("### 📊 Quick Summary")
                    st.markdown(result.get("risk_summary", "No summary available"))
                
                st.markdown("---")
                render_entities(result.get("entities", {}))
            
            with tab2:
                render_clauses(
                    result.get("clauses", []),
                    result.get("clause_risks", [])
                )
            
            with tab3:
                # Advanced Analysis (Ambiguity, Standards, Obligations)
                render_advanced_analysis(
                    st.session_state.contract_text,
                    result.get("clauses", []),
                    result.get("contract_type", "General")
                )
                
                # Show Risk Analysis here too 
                st.markdown("---")
                render_risk_analysis(
                    result.get("clause_risks", []),
                    result.get("risk_score", 0)
                )
            
            with tab4:
                render_compliance(
                    result.get("compliance", {}),
                    result.get("indian_law_notes", [])
                )
            
            with tab5:
                render_recommendations(
                    result.get("recommendations", []),
                    result.get("top_concerns", [])
                )
                
                # LLM-powered summary if enabled
                if include_llm and os.getenv("OPENAI_API_KEY"):
                    st.markdown("---")
                    st.markdown("### 🤖 AI-Powered Analysis")
                    
                    # Show model info
                    model_name = MODEL_OPTIONS.get(selected_model, {}).get("name", selected_model)
                    st.caption(f"🔧 Using model: {model_name}")
                    
                    if st.button("Generate Detailed AI Summary"):
                        with st.spinner("Generating AI analysis..."):
                            # Get LLM chain with selected model and user's API key
                            user_key = st.session_state.get("user_api_key", "")
                            llm = get_llm_chain(
                                api_key=user_key if user_key else None,
                                model=selected_model
                            )
                            summary_result = llm.analyze_contract(
                                text,
                                result.get("contract_type", "Unknown")
                            )
                            
                            if summary_result["success"]:
                                st.markdown(summary_result["content"])
                                st.info(f"Tokens used: {summary_result.get('usage', {}).get('total_tokens', 'N/A')}")
                            else:
                                st.error(f"Error: {summary_result.get('error', 'Unknown error')}")
            
            with tab6:
                st.markdown("### 📥 Export Options")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # PDF Report
                    if st.button("📄 Generate PDF Report"):
                        with st.spinner("Generating PDF..."):
                            pdf_bytes = generate_pdf_report(result)
                            st.download_button(
                                label="📥 Download PDF Report",
                                data=pdf_bytes,
                                file_name=f"contract_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                                mime="application/pdf"
                            )
                
                with col2:
                    # JSON Export
                    json_str = json.dumps(result, indent=2, default=str)
                    st.download_button(
                        label="📥 Download JSON Data",
                        data=json_str,
                        file_name=f"analysis_data_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                        mime="application/json"
                    )
                
                st.markdown("---")
                st.info("""
                **Export Notes:**
                - PDF Report: Formatted summary suitable for legal consultation
                - JSON Data: Complete analysis data for further processing
                """)
        
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            st.exception(e)
    
    else:
        # Welcome screen
        st.markdown("""
        <div style="text-align: center; padding: 3rem;">
            <h2>👋 Welcome to Legal Assistant</h2>
            <p style="color: #a0aec0; font-size: 1.2rem;">
                Upload a contract to get started with AI-powered analysis
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Feature highlights
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="info-card">
                <h4>🔍 Smart Analysis</h4>
                <p>Automatic contract classification and clause extraction with NLP</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="info-card">
                <h4>⚠️ Risk Detection</h4>
                <p>Identify risky clauses with severity scoring and recommendations</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="info-card">
                <h4>🇮🇳 India-Focused</h4>
                <p>Compliance checks for Indian business law and SME needs</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Template library
        render_template_library()


if __name__ == "__main__":
    main()
