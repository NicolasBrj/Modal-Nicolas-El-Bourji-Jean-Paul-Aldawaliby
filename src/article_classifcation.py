import spacy
import pandas as pd
import time

nlp = spacy.load("en_core_web_lg")
nlp.add_pipe("sentencizer")

EVENT_KEYWORDS = {
    "acquisition": ["acquired", "merger", "takeover", "buyout", "acquisition"],
    "lawsuit":     ["lawsuit", "filed suit", "class action", "settlement", "litigation", "indicted"],
    "earnings":    ["earnings", "revenue", "profit", "loss", "quarterly", "fiscal"],
    "downgrade":   ["downgrade", "upgrade", "price target", "credit rating", "outlook"],
    "layoffs":     ["layoff", "laid off", "job cuts", "restructuring", "redundancies"],
    "partnership": ["joint venture", "strategic partnership", "collaboration", "signed agreement"],
}

GENERIC_WORDS = {
    "company", "group", "corporation", "inc", "ltd", "the", "technologies",
    "systems", "solutions", "holdings", "international", "enterprises",
    "services", "consolidated", "global", "national", "partners", "capital"
}

def get_key_words(text):
    words = set(str(text).lower().split())
    return words - GENERIC_WORDS

# Load companies and precompute keywords once
companies_df = pd.read_csv("src/companies_with_revenu.csv")
companies_df["key_words"] = companies_df["search_name"].apply(get_key_words)

# Build inverted index
keyword_to_company = {}
for _, row in companies_df.iterrows():
    for word in row["key_words"]:
        if word not in keyword_to_company:
            keyword_to_company[word] = row["company"]

def canonize(ent_text):
    ent_keywords = get_key_words(ent_text)
    if not ent_keywords:
        return None
    for word in ent_keywords:
        if word in keyword_to_company:
            return keyword_to_company[word]
    return None

def process_article(doc, title=""):
    results = []
    title_lower = title.lower()

    org_map = {}
    for ent in doc.ents:
        if ent.label_ == "ORG":
            match = canonize(ent.text)
            if match:
                org_map[ent.text] = match

    if not org_map:
        return results

    # Count how many sentences each company appears in
    company_sent_count = {}
    for ent_text, company in org_map.items():
        count = sum(1 for sent in doc.sents if ent_text.lower() in sent.text.lower())
        in_title = any(kw in title_lower for kw in get_key_words(ent_text))
        company_sent_count[company] = (count, in_title)

    # Keep only companies mentioned in title OR in 2+ sentences
    relevant = {
        ent_text: company
        for ent_text, company in org_map.items()
        if company_sent_count[company][1] or company_sent_count[company][0] >= 2
    }

    if not relevant:
        return results

    for sent in doc.sents:
        companies_in_sent = []
        for ent_text, company in relevant.items():
            if ent_text.lower() in sent.text.lower():
                companies_in_sent.append(company)

        if not companies_in_sent:
            continue

        sent_lower = sent.text.lower()
        for event_type, keywords in EVENT_KEYWORDS.items():
            for kw in keywords:
                if kw in sent_lower:
                    for company in companies_in_sent:
                        results.append({
                            "company":    company,
                            "event_type": event_type,
                            "sentence":   sent.text.strip()
                        })
                    break

    return results

# Load articles
articles = pd.read_csv("src/dataset.csv")
texts = articles["text"].tolist()

# Timing test on 100 articles
print("Running timing test on 100 articles...")
start = time.time()
docs = list(nlp.pipe(texts[:100], batch_size=32))
for i, doc in enumerate(docs):
    process_article(doc, title=articles.iloc[i]["title"])
end = time.time()
print(f"Time for 100 articles with pipe: {end - start:.2f} seconds")
print(f"Estimated time for 50k articles: {(end - start) * 500 / 60:.0f} minutes")

# Ask before running full job
answer = input("\nProceed with full 50k run? (yes/no): ")
if answer.strip().lower() == "yes":
    all_results = []
    start = time.time()
    for i, doc in enumerate(nlp.pipe(texts, batch_size=32)):
        results = process_article(doc, title=articles.iloc[i]["title"])
        for r in results:
            r["article_index"] = i
            r["title"] = articles.iloc[i]["title"]
            r["date"] = articles.iloc[i]["date"]
        all_results.extend(results)

        if i % 1000 == 0:
            elapsed = (time.time() - start) / 60
            print(f"Processed {i}/50000 articles... ({elapsed:.1f} min elapsed)")

    end = time.time()
    print(f"\nDone in {(end-start)/60:.1f} minutes")

    results_df = pd.DataFrame(all_results)
    results_df.to_csv("src/event_extraction_results.csv", index=False)
    print(f"Saved {len(results_df)} event records.")
    print(results_df.head(10))