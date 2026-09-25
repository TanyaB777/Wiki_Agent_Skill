# Wiki Agent Skill

**Description**  
Provide quantitative insight into how user interest in a subject varies across languages and time, using Wikipedia article pageview statistics.

**Parameters**  
- `topic: string` – Wikipedia page title (URL‑safe)  
- `languages: string[]` – ISO‑639‑1 codes (e.g., `["pl", "cs"]`)  
- `start_date: string` – ISO date (inclusive)  
- `end_date: string` – ISO date (inclusive)  
- `comparison: string` – “growth” | “difference”  

**Returns**  
- A PDF (`report.pdf`) – 1 page executive summary + chart  
- A JSON blob (`summary.json`) – numeric summary, growth %, confidence

**Permissions**  
- Internet access (Wikipedia API).  
- Local file write (artifact storage).  

