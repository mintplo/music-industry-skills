# Comment coding

Code each comment on independent axes. “Negative” describes attitude; it does not mean low quality, spam, or abuse.

## Analysis value

Choose exactly one:

| Label | Rule |
|---|---|
| `substantive` | Relevant claim, reason, comparison, question, or specific criticism |
| `affect_only` | Relevant short reaction, slogan, laughter, or emoji with interpretable affect |
| `off_topic` | Not about the post, subject, or requested question |
| `duplicate` | Same public author repeats the same or near-identical content in the sampling frame |
| `promotional_spam` | Advertising, scams, unsolicited links, follow-for-follow, or unrelated promotion |
| `suspected_automation` | Coordinated or automated behavior supported by more than text similarity alone |
| `unclear` | Meaning or relevance cannot be determined |

Do not mark identical emoji from different fans as duplicates. Use `suspected_automation` only when at least two signals agree, such as repeated text across accounts, implausible timing concentration, repeated link/template structure, or account-pattern evidence available in the collected frame.

## Sentiment

Choose exactly one attitude toward the defined target: `positive`, `negative`, `mixed`, `neutral`, or `unclear`. Fix the target before coding—for example the song, video, artist, or campaign. A question without attitude is neutral; ambiguous sarcasm is unclear.

Keep **negative substantive** criticism. “The vocal is buried in the chorus” is `substantive + negative`, even if rude language adds a toxicity flag. “This is terrible” is usually `affect_only + negative`. Neither is noise solely because it is negative.

Keep interpretable emoji reactions. `🔥❤️` is usually `affect_only + positive`; a context-dependent `😂` may be `affect_only + unclear`. Emoji reactions measure lightweight affect, not substantive reasoning.

## Toxicity

Assign zero or more flags independently: `abuse`, `hate`, `threat`, `sexual_harassment`, `privacy_exposure`, `self_harm`, or `other`. Toxic but relevant criticism can remain usable. Never infer hate or threat from negative sentiment alone.

## Confidence and provenance

Set `confidence` to `high`, `medium`, or `low`. Record coding method, model/version or human labeler, coding prompt/rubric version, and `coded_at` when reproducibility matters. Preserve original text; translated text is an additional field, not a replacement.

Set `coding_status: complete` only after all four label fields have been coded. API-only collection begins as `pending` with `unclear` analysis and sentiment, no toxicity flags, and low confidence; pending comments never enter the usable sentiment denominator.

## Aggregation

Use these denominators:

- `N_raw`: all collected comments
- `N_usable`: `substantive + affect_only`
- `N_polar`: usable `positive + negative + mixed`

Report sentiment distribution across `N_usable`, including neutral and unclear. If reporting positive, negative, or net sentiment among polar comments, show `N_polar` explicitly. Calculate noise/exclusion rates against `N_raw` and toxicity exposure against `N_raw`. Show results with and without `suspected_automation` when that category is material.

Do not call the excluded set “trash comments” in outputs. Use its observed reason: spam, off-topic, duplicate, suspected automation, or unclear.
