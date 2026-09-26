```markdown
# Wikipedia Traffic Data Interpretation Guide

## 1. Normalization (PPM - Parts Per Million)
* **Raw Pageviews:** Best for estimating absolute addressable market size within a single language region.
* **Normalized Metric (PPM):** $\text{PPM} = \frac{\text{Article Views}}{\text{Total Language Views}} \times 1,000,000$.
* **When to use PPM:** Crucial when comparing different language editions (e.g., Polish `pl` vs. Czech `cs`). English Wikipedia gets orders of magnitude more views, so raw numbers misrepresent comparative interest.

## 2. Growth Trend Calculation & Smoothing
* **7-Day Moving Average:** Applied for daily granularities (>14 days) to eliminate weekend noise and transient media spikes.
* **Interpretation Thresholds:**
  * **> +20% Growth:** Strong emerging interest / expansion opportunity.
  * **-10% to +10%:** Stable baseline interest.
  * **Untranslated / Low Activity (<100 views):** Market gap or lack of organic search awareness.

## 3. Business Limitations (B2C Context)
* Wikipedia pageviews indicate **informational curiosity**, not immediate **commercial willingness-to-pay**.
* External events (news, viral social media trends) cause temporary traffic spikes that should not be confused with long-term baseline growth.