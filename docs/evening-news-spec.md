# Evening News Digest — Feature Spec

## Goal
Gather headlines from news sites across the political spectrum and synthesize a report
of the TOP 5 stories of the day, with an indicator showing where each story appeared.

## Output Format
- Top 5 stories only (not a raw feed dump)
- Per story: headline, link, and a **coverage indicator**

## Coverage Indicators
- 🟥 = Covered only by conservative outlets
- 🟦 = Covered only by liberal outlets  
- 🟪 = Covered by BOTH conservative and liberal outlets (cross-spectrum coverage)
- ⚖️ = Covered mainly by center/neutral outlets

Cross-spectrum stories (🟪) are particularly notable — if both sides are covering it,
it's probably important.

## Sources
Conservative: Fox News, Breitbart, Newsmax
Liberal: CNN, MSNBC
Balanced/Center: Reuters, AP, BBC, NPR, Washington Post, NY Times

## Story Selection Logic
1. Fetch top 5 headlines from each source
2. Group stories by topic/subject (fuzzy match on keywords)
3. Rank by number of sources covering the story (most coverage = most important)
4. Pick top 5 stories
5. Label each with coverage indicator based on which outlets picked it up

## Fact Check
- **DISABLED** — fact-check feeds rarely match headlines and add noise/tokens
- Do NOT include fact-check icons or fetch PolitiFact/Snopes feeds

## Example Output
```
📰 Evening News Digest — 2026-03-31

🟪 [Iran Ceasefire Talks Resume in Geneva](https://ap.org/...)
   Reuters, AP, Fox News, CNN, BBC — 5 sources

🟥 [Border Arrests Hit Record Low Under New Policy](https://foxnews.com/...)
   Fox News, Breitbart — 2 sources

🟦 [Senate Democrats Block Budget Vote](https://cnn.com/...)
   CNN, MSNBC, NPR — 3 sources
```

## No numbers — intentional
News articles are NOT numbered. "save #N" always refers to the RSS digest only.
News articles are for reading, not saving to Linkding.

## Rules
- **CHECK THIS FILE before making any changes to the evening news report**
- Do not dump raw feeds — synthesize top 5
- Cross-spectrum (🟪) stories are the most valuable signal
- Deliver to Discord at 6 PM EDT (10 PM UTC) daily
- Script: `/home/feoh/.openclaw/workspace/scripts/news-digest.py`

## Version History
- 2026-03-31: Initial spec written per Chris's request
