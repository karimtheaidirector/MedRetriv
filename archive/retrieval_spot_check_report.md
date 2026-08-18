# Retrieval Spot-Check Verification Report

All **525 chunks** across the 5 documents were embedded using `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions) and indexed into ChromaDB with rich metadata (`source`, `doc_type`, `section`, `page_start`, `page_end`).

---

## 1. General & Definitional Questions

### Q1: *"What is breast cancer?"*

| Rank | Distance | `doc_type` | Source Document | Section | Relevance Assessment |
|:---:|:---:|:---:|:---|:---|:---|
| **1** | **0.5132** | `patient_guide` | [NCINIH Overview.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/NCINIH%20%E2%80%93%20Breast%20Cancer%20Overview%20(Patient%20&%20Professional%20Versions).pdf#page=1) | `What Is Breast Cancer?` | **Highly Relevant**: Explicitly defines breast cancer, how cells grow uncontrollably, and describes tissues involved (ducts, lobules, stroma, nipple, vessels). |
| **2** | **0.6242** | `patient_guide` | [NCINIH Overview.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/NCINIH%20%E2%80%93%20Breast%20Cancer%20Overview%20(Patient%20&%20Professional%20Versions).pdf#page=2) | `What Is Breast Cancer?` | **Highly Relevant**: Differentiates in situ vs. invasive cancer and extent of spread. |
| **3** | **0.6720** | `patient_guide` | [NCINIH Overview.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/NCINIH%20%E2%80%93%20Breast%20Cancer%20Overview%20(Patient%20&%20Professional%20Versions).pdf#page=4) | `Types of Breast Cancer` | **Relevant**: Covers DCIS, LCIS, Paget disease, and phyllodes tumor. |
| **4** | **0.7131** | `patient_guide` | [NCINIH Overview.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/NCINIH%20%E2%80%93%20Breast%20Cancer%20Overview%20(Patient%20&%20Professional%20Versions).pdf#page=3) | `Types of Breast Cancer` | **Relevant**: Covers invasive ductal, invasive lobular, inflammatory, and TNBC. |
| **5** | **0.7186** | `patient_guide` | [NCINIH Overview.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/NCINIH%20%E2%80%93%20Breast%20Cancer%20Overview%20(Patient%20&%20Professional%20Versions).pdf#page=53) | `Breast Cancer Treatment` | **Marginal / Contextual**: Covers pregnancy-associated breast cancer. |

- **`doc_type` Confirmation**: **Confirmed** — 100% of top chunks come from `patient_guide`. The system can now retrieve direct definitional explanations that were previously missing when only screening guideline PDFs were ingested.

---

### Q2: *"What are the different types of breast cancer?"*

| Rank | Distance | `doc_type` | Source Document | Section | Relevance Assessment |
|:---:|:---:|:---:|:---|:---|:---|
| **1** | **0.4878** | `patient_guide` | [NCINIH Overview.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/NCINIH%20%E2%80%93%20Breast%20Cancer%20Overview%20(Patient%20&%20Professional%20Versions).pdf#page=3) | `Types of Breast Cancer` | **Highly Relevant**: Directly lists and defines invasive ductal, invasive lobular, inflammatory, TNBC, and metastatic cancer. |
| **2** | **0.6237** | `patient_guide` | [NCINIH Overview.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/NCINIH%20%E2%80%93%20Breast%20Cancer%20Overview%20(Patient%20&%20Professional%20Versions).pdf#page=1) | `What Is Breast Cancer?` | **Highly Relevant**: Anatomical origins of ductal, lobular, Paget, inflammatory, and angiosarcoma. |
| **3** | **0.6824** | `patient_guide` | [NCINIH Overview.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/NCINIH%20%E2%80%93%20Breast%20Cancer%20Overview%20(Patient%20&%20Professional%20Versions).pdf#page=2) | `What Is Breast Cancer?` | **Relevant**: In situ vs. invasive cancer classification. |
| **4** | **0.6867** | `government_evidence_report` | [AHRQ Evidence Review.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/breast-cancer-screening-final-evidence-review.pdf#page=13) | `Chapter 1. Introduction` | **Highly Relevant**: Molecular/histological subtypes (HR+, HER2+, Triple-negative, Luminal A). |
| **5** | **0.6898** | `patient_guide` | [NCINIH Overview.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/NCINIH%20%E2%80%93%20Breast%20Cancer%20Overview%20(Patient%20&%20Professional%20Versions).pdf#page=4) | `Molecular subtypes...` | **Relevant**: Summarizes molecular subtypes (TNBC, Luminal A/B, HER2+). |

- **`doc_type` Confirmation**: **Confirmed** — 4 `patient_guide` chunks + 1 `government_evidence_report` chunk. The retrieved context covers both anatomical classifications (ductal, lobular, inflammatory) and molecular/receptor subtypes (HR+, HER2+, TNBC).

---

### Q3: *"What causes breast cancer?"*

| Rank | Distance | `doc_type` | Source Document | Section | Relevance Assessment |
|:---:|:---:|:---:|:---|:---|:---|
| **1** | **0.5997** | `general_review` | [Nature Review (2025).pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/Nature%20Review%20Breast%20cancer%20pathogenesis%20and%20treatments%20(2025).pdf#page=2) | `unknown` | **Highly Relevant**: Discusses interplay of genetic, environmental, and lifestyle factors, multi-step carcinogenesis, two-hit model, and mutation accumulation. |
| **2** | **0.6084** | `general_review` | [Nature Review (2025).pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/Nature%20Review%20Breast%20cancer%20pathogenesis%20and%20treatments%20(2025).pdf#page=3) | `unknown` | **Highly Relevant**: Estrogenic factors, genomic instability, and multistep clonal expansion. |
| **3** | **0.6226** | `patient_guide` | [NCINIH Overview.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/NCINIH%20%E2%80%93%20Breast%20Cancer%20Overview%20(Patient%20&%20Professional%20Versions).pdf#page=1) | `What Is Breast Cancer?` | **Relevant**: Cellular mechanism of uncontrolled cell division in breast tissue. |
| **4** | **0.6662** | `patient_guide` | [NCINIH Overview.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/NCINIH%20%E2%80%93%20Breast%20Cancer%20Overview%20(Patient%20&%20Professional%20Versions).pdf#page=2) | `What Is Breast Cancer?` | **Relevant**: Progression from in situ abnormal cells to invasive tissue spread. |
| **5** | **0.6993** | `general_review` | [Frontiers Review (2026).pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/Frntiers%20Breast%20Cancer%20pathogenesis,%20diagnosis%20and%20treatment%20(2026).pdf#page=3) | `2.1 Hormonal factors` | **Highly Relevant**: Hormonal etiology, estrogen/progesterone mitogenic effects, nulliparity, obesity, and alcohol. |

- **`doc_type` Confirmation**: **Confirmed** — 3 `general_review` + 2 `patient_guide` chunks. Rich multi-document coverage across Nature, NCI, and Frontiers.

---

## 2. Screening-Specific Questions

### Q4: *"At what age should screening mammography begin?"*

| Rank | Distance | `doc_type` | Source Document | Section | Relevance Assessment |
|:---:|:---:|:---:|:---|:---|:---|
| **1** | **0.4115** | `screening_guideline` | [USPSTF Final Rec.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/breast-cancer-screening-final-rec.pdf#page=10) | `Recommendations of Others` | **Highly Relevant**: Compares guideline recommendations across bodies (ACS starting age 45 vs opportunity at 40; ACOG starting age 40; ACR/SBI starting age 40). |
| **2** | **0.5992** | `screening_guideline` | [USPSTF Final Rec.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/breast-cancer-screening-final-rec.pdf#page=10) | `Recommendations of Others` | **Relevant**: ACR risk assessment by age 25 and AAFP endorsement. |
| **3** | **0.6572** | `screening_guideline` | [USPSTF Final Rec.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/breast-cancer-screening-final-rec.pdf#page=8) | `Screening Interval` | **Highly Relevant**: USPSTF recommendation to start screening at age 40 (vs. age 50) and stopping age trials (age 70-74 vs 75+). |
| **4** | **0.6887** | `government_evidence_report` | [AHRQ Evidence Review.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/breast-cancer-screening-final-evidence-review.pdf#page=43) | `Summary of Results` | **Relevant**: Evidence on age to start or stop screening and overdiagnosis. |
| **5** | **0.7158** | `screening_guideline` | [USPSTF Final Rec.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/breast-cancer-screening-final-rec.pdf#page=4) | `Disparities in Breast Cancer Outcomes` | **Highly Relevant**: Explicitly states *"USPSTF recommends biennial screening mammography for women aged 40 to 49 years, rather than individualizing the decision"*. |

- **`doc_type` Confirmation**: **Confirmed** — 4 `screening_guideline` + 1 `government_evidence_report`. Zero general review or patient guide chunks in the top 5.

---

### Q5: *"How often should women get screened for breast cancer?"*

| Rank | Distance | `doc_type` | Source Document | Section | Relevance Assessment |
|:---:|:---:|:---:|:---|:---|:---|
| **1** | **0.6033** | `screening_guideline` | [USPSTF Final Rec.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/breast-cancer-screening-final-rec.pdf#page=10) | `Recommendations of Others` | **Highly Relevant**: Directly contrasts annual (ACS 45-54, ACR/SBI) vs. biennial intervals (ACS 55+, ACOG every 1-2 years). |
| **2** | **0.6662** | `government_evidence_report` | [AHRQ Evidence Review.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/breast-cancer-screening-final-evidence-review.pdf#page=36) | `Summary of Results` | **Relevant**: Evidence from BCSC comparing annual (11-14 mo) vs. biennial (23-26 mo) intervals. |
| **3** | **0.6749** | `screening_guideline` | [USPSTF Final Rec.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/breast-cancer-screening-final-rec.pdf#page=10) | `Recommendations of Others` | **Marginal**: Short continuation chunk on AAFP guideline support. |
| **4** | **0.6790** | `government_evidence_report` | [AHRQ Evidence Review.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/breast-cancer-screening-final-evidence-review.pdf#page=73) | `Limitations of the Evidence...` | **Relevant**: Trial data comparing annual vs. biennial screening intervals (MISS and TBST trials). |
| **5** | **0.7019** | `government_evidence_report` | [AHRQ Evidence Review.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/breast-cancer-screening-final-evidence-review.pdf#page=19) | `Chapter 1. Introduction` | **Highly Relevant**: Mentions USPSTF recommendation of biennial screening for women ages 50 to 74 and annual screening false-positive rates. |

- **`doc_type` Confirmation**: **Confirmed** — 2 `screening_guideline` + 3 `government_evidence_report`. 100% authoritative guideline/evidence sources.

---

### Q6: *"What are the harms of breast cancer screening?"*

| Rank | Distance | `doc_type` | Source Document | Section | Relevance Assessment |
|:---:|:---:|:---:|:---|:---|:---|
| **1** | **0.4399** | `patient_guide` | [NCINIH Overview.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/NCINIH%20%E2%80%93%20Breast%20Cancer%20Overview%20(Patient%20&%20Professional%20Versions).pdf#page=13) | `Breast Cancer Screening` | **Highly Relevant**: Concise summary of all 4 key harms: false-positive results, overdiagnosis/overtreatment, delayed diagnosis (false-negatives), and radiation. |
| **2** | **0.5316** | `government_evidence_report` | [AHRQ Evidence Review.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/breast-cancer-screening-final-evidence-review.pdf#page=19) | `Chapter 1. Introduction` | **Highly Relevant**: Deep dive on evidence review screening harms: false-positive/negative rates, biopsies, overdiagnosis, psychological distress, pain, and radiation. |
| **3** | **0.6224** | `government_evidence_report` | [AHRQ Evidence Review.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/breast-cancer-screening-final-evidence-review.pdf#page=71) | `Limitations of the Evidence...` | **Relevant**: Need for robust measures on patient false-positive experiences and treatment harms. |
| **4** | **0.6310** | `screening_guideline` | [USPSTF Final Rec.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/breast-cancer-screening-final-rec.pdf#page=5) | `Potential Preventable Burden` | **Relevant**: Balance of benefits and harms across modalities (DBT, ultrasound, MRI). |
| **5** | **0.6362** | `screening_guideline` | [USPSTF Final Rec.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/breast-cancer-screening-final-rec.pdf#page=5) | `Potential Preventable Burden` | **Highly Relevant**: Formal USPSTF statement on harms: false-positives, psychological harms, overdiagnosis, overtreatment, and radiation. |

- **`doc_type` Confirmation**: 1 `patient_guide` + 2 `government_evidence_report` + 2 `screening_guideline`. Ranks 2, 4, 5 are authoritative guideline/evidence chunks; Rank 1 from the NCI patient guide happens to have the highest lexical density for the exact phrase *"potential harms of breast cancer screening"*.

---

## 3. Mixed / Edge Case Question

### Q7: *"What is the difference between DCIS and invasive breast cancer?"*

| Rank | Distance | `doc_type` | Source Document | Section | Relevance Assessment |
|:---:|:---:|:---:|:---|:---|:---|
| **1** | **0.5256** | `government_evidence_report` | [AHRQ Evidence Review.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/breast-cancer-screening-final-evidence-review.pdf#page=14) | `Chapter 1. Introduction` | **Highly Relevant**: Explicitly explains DCIS as precursor lesion/risk marker for invasive cancer and features predicting invasive progression. |
| **2** | **0.5717** | `screening_guideline` | [USPSTF Final Rec.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/breast-cancer-screening-final-rec.pdf#page=3) | `Treatment or Intervention` | **Highly Relevant**: Defines DCIS as noninvasive abnormal cells in duct lining vs. treatment intended to prevent future invasive cancer. |
| **3** | **0.5829** | `government_evidence_report` | [AHRQ Evidence Review.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/breast-cancer-screening-final-evidence-review.pdf#page=69) | `Chapter 4. Discussion` | **Highly Relevant**: Clinical management differences, active surveillance trials (PRECISION collaboration), and overtreatment concerns. |
| **4** | **0.5974** | `government_evidence_report` | [AHRQ Evidence Review.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/breast-cancer-screening-final-evidence-review.pdf#page=14) | `Chapter 1. Introduction` | **Highly Relevant**: DCIS epidemiology (16% of breast neoplasms), progression rates (14-53% to invasive cancer over 8-22 yrs), and overdiagnosis. |
| **5** | **0.5990** | `patient_guide` | [NCINIH Overview.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/NCINIH%20%E2%80%93%20Breast%20Cancer%20Overview%20(Patient%20&%20Professional%20Versions).pdf#page=59) | `Breast Cancer Research Results` | **Highly Relevant**: Explains DCIS as precancerous cells confined to the duct lining and the 2024 active monitoring trial. |

- **Cross-document diversity**: Draws from AHRQ evidence review (3 chunks), USPSTF recommendation (1 chunk), and NCI overview (1 chunk).

---

## 4. Key Findings & Observations

### 1. General Questions Fix Verification (Q1–Q3)
- **Previous state**: Ingestion failed to answer general questions because only screening guidelines were loaded.
- **Current state**: Queries 1, 2, and 3 now retrieve relevant content from [NCINIH Overview.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/NCINIH%20%E2%80%93%20Breast%20Cancer%20Overview%20(Patient%20&%20Professional%20Versions).pdf) (`patient_guide`), [Nature Review (2025).pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/Nature%20Review%20Breast%20cancer%20pathogenesis%20and%20treatments%20(2025).pdf) (`general_review`), and [Frontiers Review (2026).pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/Frntiers%20Breast%20Cancer%20pathogenesis,%20diagnosis%20and%20treatment%20(2026).pdf) (`general_review`).

### 2. Screening Specificity Verification (Q4–Q6)
- Queries 4, 5, and 6 retrieve predominantly from `screening_guideline` ([USPSTF Final Rec.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/breast-cancer-screening-final-rec.pdf)) and `government_evidence_report` ([AHRQ Evidence Review.pdf](file:///e:/Projects/Software%20Projects/RAGs/MedRetriv/data/raw/breast-cancer-screening-final-evidence-review.pdf)).
- In Q6, the top rank came from `patient_guide` (NCI), which has a clean bulleted breakdown of screening harms, followed by 4 guideline/evidence chunks.

### 3. Document Dominance vs. Multi-Document Diversity
- **Q1**: Dominated by NCI overview (all 5 chunks). Given that NCI is the dedicated patient guide defining breast anatomy and cancer concepts in layman terms, this is expected and appropriate.
- **Q2, Q3, Q5, Q6, Q7**: Show strong multi-document diversity across 2 to 3 distinct sources.

### 4. Impact of the "unknown" Section Chunks
- In Q3 (*"What causes breast cancer?"*), Ranks 1 and 2 retrieved chunks from `Nature Review Breast cancer pathogenesis and treatments (2025).pdf` pages 2 and 3, which have `section="unknown"`.
- **Quality check**: Despite the missing heading text in the metadata, the chunk text itself is clinically relevant (describing the multistep two-hit model, somatic mutations, and interaction of genetic/lifestyle risk factors). The missing section metadata did not impede semantic retrieval.
