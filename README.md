# From Financial News to Market Behavior

This project studies whether financial news co-mentions contain useful information about stock-market behavior.

The main idea is to start from financial news articles, extract the companies mentioned in each article, build a company co-mention graph, and then test whether this graph is related to real financial variables such as return co-movement, volatility, and stock reactions around news mentions.

The project combines:

- named entity extraction from financial articles;
- company-name matching and alias cleaning;
- graph construction and Louvain community detection;
- centrality measures such as weighted degree, betweenness, and PageRank;
- financial enrichment using historical stock returns;
- statistical tests and event-study style analyses.

## Repository Structure

```text
.
|-- Companies_list_query.csv
|-- Companies_list_query_cleaner.ipynb
|-- Financial enrichment/
|   `-- financial_enrichment.ipynb
|-- Statistical_notebooks/
|   |-- edge_comovement_statistical_tests.ipynb
|   |-- centrality_volatility_statistical_tests.ipynb
|   |-- mention_spike_event_study.ipynb
|   `-- news_mention_size_event_study.ipynb
|-- outputs/
|   |-- centrality_groups_vs_volatility.png
|   |-- edge_vs_nonedge_return_corr.png
|   |-- edge_weight_vs_return_corr.png
|   |-- mention_spike_event_study_effects.png
|   `-- news_mention_size_event_study.png
`-- src/
    |-- dataset_generator.py
    `-- my_notebooks/
        |-- Articles entity extraction.ipynb
        |-- Co-mention csv with aliases.ipynb
        `-- Comention_Graph_Construction_and_analysis.ipynb
```

## Project Workflow

### 1. Build the Article Dataset

The file `src/dataset_generator.py` downloads the Hugging Face dataset `ashraq/financial-news-articles`, extracts publication dates, keeps 2018 articles, removes clearly non-financial URLs, samples 50,000 articles, and saves:

```text
dataset.csv
```

This file is the starting point for the article-level analysis.

### 2. Extract Company Mentions

`src/my_notebooks/Articles entity extraction.ipynb` uses spaCy named entity recognition to extract organizations from each article. It removes some generic or non-company entities and saves one row per article with a list of mentioned companies:

```text
companies_in_articles.csv
```

### 3. Clean the Company Database

`Companies_list_query.csv` is the raw company list exported from a Wikidata SPARQL query for companies listed on the New York Stock Exchange and NASDAQ.. The query retrieves companies whose stock exchange property matches NYSE or NASDAQ, together with metadata such as Wikidata company ID, company label, exchange label, ticker, industries, market capitalization, market capitalization date, revenue, and revenue date.

`Companies_list_query_cleaner.ipynb` cleans this NYSE/NASDAQ company list, keeps useful metadata such as company ID, ticker, exchange, industry, revenue, and market capitalization, and saves:

```text
nyse_nasdaq_companies_list.csv
```

This file is used to match extracted article names to real listed companies.

### 4. Match Mentions and Build Co-Mention Edges

`src/my_notebooks/Co-mention csv with aliases.ipynb` normalizes company names by removing legal suffixes, punctuation, ticker suffixes, and inconsistent formatting. It then builds aliases from company names, search names, and tickers.

The notebook creates two main outputs:

```text
company_article_counts.csv
company_comention_edges.csv
```

`company_article_counts.csv` counts how many articles mention each matched company.

`company_comention_edges.csv` stores weighted company pairs. An edge exists when two companies are mentioned in the same article, and the edge weight is the number of articles where they appear together.

### 5. Construct and Analyze the Co-Mention Graph

`src/my_notebooks/Comention_Graph_Construction_and_analysis.ipynb` builds an undirected weighted graph with:

- nodes = companies;
- edges = co-mentions;
- edge weights = number of shared article mentions.

The graph is filtered to remove very low-degree nodes. Louvain community detection is used to find clusters of companies that are frequently co-mentioned. The notebook also assigns broad industry groups and computes centrality measures:

- degree;
- weighted degree;
- degree centrality;
- betweenness centrality;
- PageRank.

The main output is:

```text
louvain_clusters_with_industries_degrees_ranks.csv
```

In the saved notebook results, the graph has 1,172 nodes and 8,166 edges after filtering, with 17 Louvain clusters.

### 6. Add Financial Data

`Financial enrichment/financial_enrichment.ipynb` uses `yfinance` to download daily adjusted stock prices from 2017 to 2019. It computes daily log returns and company-level financial variables:

- annualised volatility;
- cumulative return;
- mean daily return;
- Sharpe proxy.

The main outputs are:

```text
company_financials.csv
daily_returns_2017_2019.csv
```

These files are used by the statistical notebooks.

## Statistical Analyses

The production statistical work is in the `Statistical_notebooks/` folder.

### 1. Co-Mention Edges and Return Co-Movement

Notebook:

```text
Statistical_notebooks/edge_comovement_statistical_tests.ipynb
```

This notebook tests whether company pairs connected in the co-mention graph have higher stock-return correlation than random non-edge pairs.

Method:

- convert graph edges into ticker pairs;
- sample random non-edge ticker pairs as a control group;
- compute Pearson correlations of daily log returns for each pair;
- apply Fisher-z transformation to correlations;
- compare edge pairs vs non-edge pairs using a two-sample test;
- test whether stronger co-mention weights are associated with higher return co-movement.

Main result:

Co-mentioned companies have significantly higher return co-movement than random non-edge pairs. Stronger co-mention weights are also positively associated with higher return correlation.

### 2. Centrality and Volatility

Notebook:

```text
Statistical_notebooks/centrality_volatility_statistical_tests.ipynb
```

This notebook tests whether graph centrality is related to stock volatility.

Method:

- merge PageRank centrality with annualised volatility;
- split companies into low, middle, and high PageRank groups;
- compare volatility across groups using Welch ANOVA;
- compare high vs low centrality directly;
- check the continuous relationship using Pearson and Spearman correlations.

Main result:

Higher PageRank centrality is significantly associated with lower annualised volatility. In this dataset, the most central companies are usually large, visible, established firms, so centrality seems to capture stability rather than risk.

### 3. Mention-Spike Event Study

Notebook:

```text
Statistical_notebooks/mention_spike_event_study.ipynb
```

This notebook tests whether unusual increases in media attention are followed by abnormal stock behavior.

Method:

- map article company mentions to stock tickers;
- count weekly mentions by ticker;
- define ticker-specific mention spikes as top-decile weekly mention counts;
- compare next-week returns after spike weeks with normal weeks;
- aggregate to one value per ticker before testing.

Main result:

Mention spikes are followed by significantly larger next-week absolute returns. The signed-return result is weaker and should be interpreted carefully, because the main evidence is about larger movement, not necessarily positive returns.

### 4. News Mentions, Company Visibility, and Stock Reaction

Notebook:

```text
Statistical_notebooks/news_mention_size_event_study.ipynb
```

This notebook tests whether less-mentioned companies react more strongly to news mentions than more-mentioned companies.

Method:

- build ticker-date mention events;
- use article count as a proxy for company visibility or size;
- compare low-article-count companies with high-article-count companies;
- compute event-window reactions using the previous trading day and next trading day;
- aggregate reactions to one row per ticker;
- compare low-visibility and high-visibility companies using Welch's two-sample t-test.

Main result:

Low-article-count companies show significantly larger post-news absolute-return reactions than high-article-count companies. This supports the idea that news mentions may affect less visible companies more strongly.

## Main Outputs

The `outputs/` folder contains the final figures from the statistical notebooks:

- `edge_vs_nonedge_return_corr.png`
- `edge_weight_vs_return_corr.png`
- `centrality_groups_vs_volatility.png`
- `mention_spike_event_study_effects.png`
- `news_mention_size_event_study.png`

These figures summarize the main statistical results.

## Important Generated Files

Several CSV files are generated by the notebooks but are not included directly in this repository. To reproduce the full project, run the notebooks in order so these files are created:

```text
dataset.csv
companies_in_articles.csv
nyse_nasdaq_companies_list.csv
company_article_counts.csv
company_comention_edges.csv
louvain_clusters_with_industries_degrees_ranks.csv
company_financials.csv
daily_returns_2017_2019.csv
```

The statistical notebooks expect these files to exist in the working directory where the notebooks are run.

## Suggested Run Order

Run the project in this order:

1. `src/dataset_generator.py`
2. `Companies_list_query_cleaner.ipynb`
3. `src/my_notebooks/Articles entity extraction.ipynb`
4. `src/my_notebooks/Co-mention csv with aliases.ipynb`
5. `src/my_notebooks/Comention_Graph_Construction_and_analysis.ipynb`
6. `Financial enrichment/financial_enrichment.ipynb`
7. Statistical notebooks in `Statistical_notebooks/`

Because some notebooks use relative paths, it is important to run them from their own folder or adjust the paths if running from a different location.

## Dependencies

The project uses Python notebooks and common data-science libraries:

```text
pandas
numpy
matplotlib
scipy
statsmodels
networkx
ipysigma
spacy
yfinance
datasets
```

The entity extraction notebook also requires the spaCy English model:

```bash
python -m spacy download en_core_web_sm
```

## Project Conclusion

The results suggest that financial news co-mentions are not random text artifacts. They capture meaningful relationships between companies that are visible in financial data:

- co-mentioned firms move together more than random firm pairs;
- stronger co-mentions correspond to stronger return co-movement;
- highly central firms in the news graph tend to be less volatile;
- mention spikes are followed by larger next-week stock movements;
- less-mentioned companies react more strongly to news mentions than highly mentioned companies.

Overall, the project shows how financial text mining, graph analysis, and statistical testing can be combined to study the link between media attention and market behavior.
