# Style guide: situation report (doc_type `sitrep`)

Header: `Situation report <unit> as of <DDHHMMZ MON YY>`; numbered paragraphs (situation, own
forces, adversary, logistics, assessment). Unit shorthand and aliases. May carry `hedge_drift`:
an informal synonym ("probable") for a likelihood, which the extractor must normalize to the
nearest ICD 203 term (truth stores the ICD term in `likelihood_icd203` and the surface phrase in
`likelihood_surface_term`). Confidence, when stated, is in its own sentence. No JRAM risk vocabulary.
