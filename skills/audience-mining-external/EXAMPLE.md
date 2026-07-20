# High-Potential Audience Mining — Examples (MAPI whitelist only)

## 1. Success case（enough pool + verified Shop context + complete insight signals）

- Input: advertiser is routed from a Shop / live-shopping workflow, reachable pool size = 120,000, report reach available, one valid custom audience exists, and insight includes interest / device price / geo / engagement signals.
- Output: S tier recommended; a reusable DMP audience pack can be created after confirmation.

## 2. Boundary / low-confidence case（pool barely qualifies or Shop context is not directly verified）

- Input: reachable pool size = 3,200, the host flow explicitly labels the scenario as LSA live-shopping, but Shop context is only indirectly supported and only 1–2 insight dimensions are available.
- Output: `[Low Confidence]` recommendation; the Skill may suggest a pack candidate, but must explain that evidence is limited and must not auto-write the audience pack.

## 3. Out-of-scope / refusal case（audience too small or Shop context missing）

- Input: no grounded Shop-context evidence is available and reachable pool size = 1,500.
- Output: clear refusal to run audience mining, with explanation that minimum audience size and a Shop-related operating context are required first.