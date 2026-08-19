import re

# Common conversational and clinical typographical slips mapping
CLINICAL_TYPO_MAP = {
    # Conversational & general words
    "thee": "the",
    "meee": "me",
    "mee": "me",
    "telll": "tell",
    "tel": "tell",
    "aboutt": "about",
    "abouut": "about",
    "whatt": "what",
    "wat": "what",
    "plz": "please",
    "pls": "please",
    "helllo": "hello",
    "hiii": "hi",
    "hii": "hi",
    "okaay": "okay",
    "okkay": "okay",
    "okayy": "okay",
    "alrightt": "alright",
    "alrite": "alright",
    "gud": "good",
    
    # Clinical domain terms
    "breaast": "breast",
    "brest": "breast",
    "breastt": "breast",
    "cancerr": "cancer",
    "cancr": "cancer",
    "cancerrs": "cancers",
    "typesg": "types",
    "typessg": "types",
    "typess": "types",
    "symtoms": "symptoms",
    "symptomms": "symptoms",
    "symtom": "symptom",
    "pathogensis": "pathogenesis",
    "pathogeneis": "pathogenesis",
    "pathogenisis": "pathogenesis",
    "pathogesis": "pathogenesis",
    "treatmnt": "treatment",
    "treatement": "treatment",
    "treatments": "treatment",
    "diagnosiss": "diagnosis",
    "diagnossis": "diagnosis",
    "prognossis": "prognosis",
    "prognosiss": "prognosis",
    "biomarkerss": "biomarkers",
    "biomarkr": "biomarker",
    "biomarkrs": "biomarkers",
    "subtyps": "subtypes",
    "subtypess": "subtypes",
    "mamogram": "mammogram",
    "mamograms": "mammograms",
    "mamography": "mammography",
    "mammogramm": "mammogram",
    "mammografy": "mammography",
    "screenin": "screening",
    "screning": "screening",
    "screenning": "screening",
    "preventive": "preventive",
    "preventative": "preventive",
    "morbidity": "morbidity",
    "mortality": "mortality",
    "tomosynthesis": "tomosynthesis",
    "biopsie": "biopsy",
    "biopsys": "biopsies",
    "ultrasond": "ultrasound",
    "ultrsound": "ultrasound",
    "chemotherpy": "chemotherapy",
    "radiotherapy": "radiotherapy",
    "stagingg": "staging",
    "metastis": "metastasis",
    "metastasiss": "metastasis",
}


def normalize_query(query: str) -> str:
    """
    Lightweight, low-risk query normalization that mitigates repeated-character typos
    and common keyboard slips before conversational filtering and embedding generation.
    """
    if not query or not query.strip():
        return query

    text = query.strip()

    # 1. Collapse 3+ repeated characters ("hellooooo" -> "hello", "hiiii" -> "hi", "whatttt" -> "what")
    text = re.sub(r"(\w)\1{2,}", r"\1", text)

    # 2. Token-level normalization for known typographical slips
    tokens = text.split()
    normalized_tokens = []
    for token in tokens:
        clean_token = re.sub(r"[^\w]", "", token.lower())
        if clean_token in CLINICAL_TYPO_MAP:
            corrected = CLINICAL_TYPO_MAP[clean_token]
            # Preserve case if uppercase/capitalized
            if token.isupper():
                corrected = corrected.upper()
            elif token.istitle():
                corrected = corrected.title()
            punct = token[len(clean_token):]
            normalized_tokens.append(corrected + punct)
        else:
            normalized_tokens.append(token)

    # 3. Collapse multiple whitespace
    return re.sub(r"\s+", " ", " ".join(normalized_tokens)).strip()
