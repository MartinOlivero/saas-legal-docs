# legal-docs

**Your privacy policy probably promises things your code doesn't do.**

A Claude Code plugin that writes and audits the legal documents of a SaaS — terms of service,
privacy policy, security policy, consumer buttons — by reading the actual schema, providers and
pixels, instead of filling in a template.

And in audit mode, it does the thing nothing else does: **it compares what your published legal
text promises against what your codebase actually does.**

```
[🔴 CONTRADICTION] Promises it doesn't share data with third parties, but loads the Meta pixel
  Document says: "We never share your information with third parties"  — privacy.html:64
  Code says:     fbq('init', ...) in index.html:212; GA4 in layout.tsx:31
  Why it matters: the pixel sends visitor identifiers to Meta (US). That's an undeclared
                  disclosure and an undeclared international transfer.
  What to do:    remove the pixel, or declare it — provider table, purpose, legal basis.
```

---

## Why this exists

Legal document generators have been around for twenty years. You fill a form, you get generic
text describing a product that isn't yours. The most popular one on GitHub has 4.6k stars and
produces the same paragraph for every app.

That's not the hard part. The hard part is that **the document and the product drift apart**:

- The policy says data is encrypted at rest. Nobody ever turned encryption on.
- It says deleting your account deletes your data. Deletion sets `active = false`.
- It says "we don't share your data with anyone". There's a Meta pixel on the landing page.
- It lists three providers. The codebase talks to eight.
- It promises backups. There's no backup job, and nobody has tested a restore.

Every one of those is **a false statement signed by the product owner**. In the US, the FTC
treats exactly this as a deceptive practice under Section 5 — the examples it has pursued are
literally *"we never sell your data"*, *"your information is encrypted"*, and *"we comply with
GDPR"* from companies that didn't.

This plugin reads the code first, and refuses to write what it can't verify.

## What it does differently

**It reads the product before writing a word.** Database schema, code that receives user input,
providers and what country each one is in, pixels and cookies in the HTML, and what the account
deletion flow actually does. The document describes *that* product.

**It doesn't promise what the product doesn't do.** No verified backups → the policy doesn't
claim backups. It generates a "what this policy does not promise" section instead, which is
worth more to a technical buyer than the marketing version — and reduces real exposure, since
every promise you remove is one the FTC can't call deceptive.

**It stops without the responsible party.** Legal name, tax ID and address are mandatory. Miss
them and you get a draft marked `[MISSING]` that does not ship.

**It verifies the law is still the law, every run.** It does not trust what the model remembers.
That is not paranoia — see below.

## Two modes

### Generate

Asks which jurisdictions apply (this is **not** deducible from code — a product hosted on Vercel
with a Spanish UI can sell to thirty countries), verifies the normative tables are current, reads
the product, asks only what can't be deduced, and writes the documents in whatever format the
stack uses: plain HTML for a static landing, a route for Next/Astro/Remix, Markdown if there's no
site yet.

### Audit

Four passes over the published documents:

1. **What's missing** — against the checklist for the jurisdictions that apply.
2. **What's written for another country** — the most common sign of a copied policy. GDPR
   language in an Argentine policy, CCPA boilerplate in a European one.
3. **What it cites that no longer applies** — repealed rules, agencies that changed names, and
   the hard case: *the right rule, frozen in its previous version*.
4. **What it promises that the product doesn't do** — the one that matters.

Findings are split into two categories, and the order is deliberate:

- 🔴 **CONTRADICTION** — the document asserts something the code disproves.
- 🟠 **NON-COMPLIANCE** — something required is missing.

The first is missing something. The second says something untrue, and that's considerably worse.

## Jurisdictions

| | Coverage | Verified |
| --- | --- | --- |
| 🇦🇷 **Argentina** — Ley 25.326, Ley 24.240, Disp. 954/2025 | full | 2026-08-17 |
| 🇪🇺 **European Union** — GDPR + ePrivacy | full | 2026-08-18 |
| 🇺🇸 **United States** — state privacy laws, call-recording consent, BIPA, FTC §5, TCPA | full | 2026-08-18 |
| 🇧🇷 **Brazil** — LGPD + ANPD resolutions | full | 2026-08-18 |
| 🇬🇧 **United Kingdom** — UK GDPR + DUAA 2025 + PECR | differences only, reads alongside the EU table | 2026-08-18 |

Every rule carries its article and its deadline, checked against InfoLeg, EUR-Lex, the Boletín
Oficial, gov.br/anpd, legislation.gov.uk and the regulators' own sites — not against memory.

**What it does not cover, it names.** Canada, Switzerland, India, China, Japan and the rest are
absent, and the skill says so instead of improvising. A régime written from recall doesn't have
the guarantee that makes the rest of this useful.

## ⚠️ Legal content expires

This is the honest part, and you should read it before relying on the plugin.

In the eighteen months before the verification dates above, **three central rules changed in
Argentina alone**: Res. 424/2020 was repealed by Disposición 954/2025 (which also added a second
mandatory button), COPREC was dissolved by Decreto 55/2025, and the sanctions regime moved to
Res. AAIP 126/2024. The UK raised its cookie-and-marketing fine ceiling from £500,000 to £17.5M.
The EU-US transfer framework is on its third attempt, with an appeal pending before the CJEU.

A document citing any of the repealed ones is proof nobody reviewed it.

That's why every normative table carries its verification date at the top and a mandatory
currency check the skill runs **before writing anything**. If you're reading this long after the
dates above, re-verify. And if a table turns out to be stale, please open an issue — that's the
single most useful contribution to this repo.

## Install

```bash
/plugin marketplace add MartinOlivero/saas-legal-docs
/plugin install legal-docs
```

Then just ask, in English or Spanish:

```
necesito los legales para mi SaaS
audit my privacy policy against the code
¿me falta algo para vender en Europa?
can I record these calls?
```

## What this is not

**It does not replace a lawyer.** It produces an informed, verifiable draft — one grounded in the
actual architecture and in rules checked against primary sources. That's a much better starting
point than a template, and a much worse one than professional review. Every document it generates
says so in its own footer.

Products that need a lawyer regardless of what this plugin outputs:

- Anything that **records or transcribes calls.** Eleven US states require all-party consent and
  recording without it can be a **criminal offence**, not a fine. Illinois treats voiceprints as
  biometric data under BIPA — with a private right of action and damages *per person, per
  occurrence* — and recent case law reaches AI transcription tools that distinguish speakers,
  which is what speaker diarization does in nearly every modern meeting tool.
- Anything that **evaluates people with AI** in ways that affect them.
- Anything touching **health, minors, or financial data.**

Use the draft to arrive at that conversation prepared. Not to skip it.

## License

MIT. See [LICENSE](LICENSE).

Built with [Claude Code](https://claude.com/claude-code). Companion to
[saas-builder](https://github.com/MartinOlivero/saas-builder).
