-- db/seed_playbook.sql
-- ============================================================================
--  Curated Playbook for the German Freelancer Contract Analyzer
-- ============================================================================
--
--  WHAT THIS FILE IS
--  -----------------
--  Layer 2 of the three-layer knowledge stack (Layer 1 = relational facts in
--  rate_benchmarks / statute_references; Layer 2 = this curated playbook of
--  risky-clause patterns; Layer 3 = transient session state). Each entry
--  describes a recognisable risky pattern in a German freelance contract,
--  the legal reasoning that flags it, and a concrete redline.
--
--  HOW TO RUN
--  ----------
--    psql -U postgres -d freelancer_analyzer -f db/init.sql           -- schema
--    psql -U postgres -d freelancer_analyzer -f db/seed_rates.sql     -- rate benchmarks
--    psql -U postgres -d freelancer_analyzer -f db/seed_playbook.sql  -- THIS FILE
--    python scripts/seed_vectors.py                                   -- compute embeddings
--
--  Rerunning is safe. The INSERT uses ON CONFLICT (id) DO UPDATE so edits to
--  this file propagate; the embedding column is reset to NULL only for rows
--  whose semantic content actually changed, so seed_vectors.py without
--  --force will re-embed exactly the rows that need it.
--
--  TAXONOMY (16 categories, 66 entries)
--  -------------------------------------
--  Coverage was scoped before authoring to ensure the corpus is methodical
--  rather than ad-hoc. Every category targets ~3-6 entries with a deliberate
--  mix of risk levels so the analyzer surfaces nuance, not a wall of red.
--
--    A. compensation_rate              (PB-006..PB-009)        4 entries
--    B. payment_terms                  (PB-002, PB-010..PB-012) 4 entries
--    C. late_payment_interest          (PB-001, PB-013)        2 entries
--    D. intellectual_property          (PB-004, PB-014..PB-018) 6 entries
--    E. scheinselbstständigkeit        (PB-003, PB-019..PB-023) 6 entries
--    F. termination                    (PB-024..PB-029)        6 entries
--    G. liability                      (PB-005, PB-030..PB-033) 5 entries
--    H. agb_kontrolle                  (PB-034..PB-038)        5 entries
--    I. confidentiality                (PB-039..PB-042)        4 entries
--    J. non_compete                    (PB-043..PB-046)        4 entries
--    K. acceptance_werkvertrag         (PB-047..PB-050)        4 entries
--    L. warranty_maengel               (PB-051..PB-054)        4 entries
--    M. data_protection                (PB-055..PB-058)        4 entries
--    N. working_time                   (PB-059..PB-061)        3 entries
--    O. dispute_resolution             (PB-062..PB-064)        3 entries
--    P. force_majeure                  (PB-065..PB-066)        2 entries
--                                                              ---------
--                                                              66 entries
--
--  PROVENANCE FIELDS
--  -----------------
--  Every entry carries:
--    - statute_ref : pinpoint citation (e.g. "§271a BGB", "BAG 5 AZR 251/08")
--    - source_url  : link to the primary source (gesetze-im-internet.de,
--                    bundesarbeitsgericht.de, deutsche-rentenversicherung.de,
--                    BITKOM template repo, etc.)
--    - source_type : one of {statute, case, agency, template, custom}
--                    statute  -> grounded in a specific statutory paragraph
--                    case     -> grounded in a court ruling (BAG/BGH/BFH)
--                    agency   -> grounded in regulator guidance
--                                (DRV Statusfeststellung, BMJ, BfDI, etc.)
--                    template -> reflects industry-standard model contracts
--                                (BITKOM, DAV Mustervertrag)
--                    custom   -> team-curated rule with no single primary
--                                source; reasoning explains derivation
--
--  An integrity script (scripts/check_playbook.py — TODO) will assert in CI
--  that every row has non-empty statute_ref, source_url, source_type within
--  the enum, and risk_level non-null. Adding it is the next step.
-- ============================================================================

INSERT INTO playbook (
    id,
    clause_type,
    risk_level,
    pattern_description,
    example_risky_wording,
    legal_reasoning,
    recommended_redline,
    statute_ref,
    source_url,
    source_type
)
VALUES

-- ============================================================================
-- C. LATE PAYMENT INTEREST
-- ============================================================================

('PB-001',
 'late_payment_interest',
 'medium',
 $$Contract specifies a late-payment interest rate below the B2B statutory default of 9 percentage points over the base rate.$$,
 $$Bei Zahlungsverzug werden Verzugszinsen in Höhe von 4 % p.a. berechnet.$$,
 $$§288 Abs. 2 BGB sets the default statutory late-payment interest for B2B (non-consumer) transactions at nine percentage points above the European Central Bank base rate. Agreeing to a fixed lower rate is enforceable but quietly removes a significant entitlement; over a 90-day delay on a five-figure invoice the foregone interest is non-trivial.$$,
 $$Bei Zahlungsverzug werden Verzugszinsen in gesetzlicher Höhe gemäß §288 Abs. 2 BGB (neun Prozentpunkte über dem Basiszinssatz) berechnet.$$,
 '§288 Abs. 2 BGB',
 'https://www.gesetze-im-internet.de/bgb/__288.html',
 'statute'),

('PB-013',
 'late_payment_interest',
 'low',
 $$Contract is silent on late-payment interest. Statutory default applies, no action needed.$$,
 NULL,
 $$Where the contract does not address Verzugszinsen, §288 Abs. 2 BGB applies automatically once the freelancer is in Verzug under §286 BGB. Silence is not risky — but flagging it as low-risk reassures the user instead of leaving the topic unaddressed in the report.$$,
 NULL,
 '§286, §288 Abs. 2 BGB',
 'https://www.gesetze-im-internet.de/bgb/__286.html',
 'statute'),

-- ============================================================================
-- B. PAYMENT TERMS
-- ============================================================================

('PB-002',
 'payment_terms',
 'medium',
 $$Payment term exceeds 30 days without clear justification.$$,
 $$Die Vergütung ist innerhalb von 45 Tagen nach Rechnungseingang zur Zahlung fällig.$$,
 $$Industry norms for German freelance contracts run 14-30 days. While §271a BGB allows up to 60 days in B2B without special justification, every additional week of payment delay materially impairs a one-person business's liquidity and is leverage given up for no consideration.$$,
 $$Die Vergütung ist innerhalb von 14 Kalendertagen nach Rechnungseingang ohne Abzug zur Zahlung fällig.$$,
 '§271a BGB',
 'https://www.gesetze-im-internet.de/bgb/__271a.html',
 'statute'),

('PB-010',
 'payment_terms',
 'high',
 $$Payment term exceeds 60 days, the statutory hard ceiling under §271a Abs. 1 BGB.$$,
 $$Die Vergütung ist 90 Tage nach Rechnungseingang zur Zahlung fällig.$$,
 $$§271a Abs. 1 BGB makes a payment term longer than 60 days valid only if it is "ausdrücklich getroffen" AND not "im Hinblick auf die Belange des Gläubigers grob unbillig". The burden of justifying both falls on the client; a generic 90-day term in a standard contract is presumptively unenforceable and exposes the freelancer to working-capital risk that should not exist.$$,
 $$Die Vergütung ist innerhalb von 30 Kalendertagen nach Rechnungseingang zur Zahlung fällig. Ein längeres Zahlungsziel wird nicht vereinbart.$$,
 '§271a Abs. 1 BGB',
 'https://www.gesetze-im-internet.de/bgb/__271a.html',
 'statute'),

('PB-011',
 'payment_terms',
 'high',
 $$"Pay-when-paid" clause: freelancer's invoice is only due once the client itself has been paid by its end customer.$$,
 $$Die Fälligkeit der Vergütung tritt erst ein, sobald der Auftraggeber die entsprechende Zahlung von seinem Endkunden erhalten hat.$$,
 $$German law has no equivalent of the Anglo-American "pay-when-paid" doctrine. A clause that defers payment by reference to a third-party transaction the freelancer has no visibility into is regularly held grob unbillig under §271a BGB and an unangemessene Benachteiligung under §307 Abs. 1 BGB. The freelancer carries the client's customer-credit risk for free.$$,
 $$Die Fälligkeit der Vergütung richtet sich ausschließlich nach Rechnungsstellung des Auftragnehmers und ist nicht von Zahlungen Dritter an den Auftraggeber abhängig.$$,
 '§271a BGB, §307 Abs. 1 BGB',
 'https://www.gesetze-im-internet.de/bgb/__307.html',
 'statute'),

('PB-012',
 'payment_terms',
 'medium',
 $$Invoice can be rejected for trivial formal defects, restarting the payment clock indefinitely.$$,
 $$Bei formalen Mängeln einer Rechnung beginnt die Zahlungsfrist erst mit Eingang einer berichtigten Rechnung neu zu laufen.$$,
 $$Resetting the clock for any "formal defect" is open to abuse: a missing reference number can stall payment by weeks. §14 UStG defines what an invoice must contain; the redline limits restarts to actual UStG-relevant defects, not arbitrary client preferences.$$,
 $$Die Zahlungsfrist beginnt mit Rechnungseingang. Ist eine Rechnung wegen eines wesentlichen Mangels im Sinne von §14 UStG zu berichtigen, beginnt die Frist mit Eingang der berichtigten Rechnung neu; geringfügige formale Abweichungen lassen den Fristlauf unberührt.$$,
 '§14 UStG, §271a BGB',
 'https://www.gesetze-im-internet.de/ustg_1980/__14.html',
 'statute'),

-- ============================================================================
-- A. COMPENSATION & RATE STRUCTURE
-- ============================================================================

('PB-006',
 'compensation_rate',
 'medium',
 $$Hourly or daily rate sits well below the p25 benchmark for the freelancer's skill category and experience tier.$$,
 $$Der Auftragnehmer erhält für seine Leistung ein Honorar in Höhe von 45,00 € pro Stunde.$$,
 $$The Freelancer-Kompass 2025 (freelancermap GmbH, n≈5,000) reports median hourly rates by skill family; the analyzer's rate_benchmarks table interpolates p25/p75 around those medians. A rate beneath p25 is not unlawful, but it is a pricing failure the freelancer should know about — especially since the same survey shows that under-pricing is correlated with longer collection cycles, not shorter ones.$$,
 NULL,
 'Freelancer-Kompass 2025 / rate_benchmarks',
 'https://www.freelancermap.de/freelancer-kompass',
 'agency'),

('PB-007',
 'compensation_rate',
 'low',
 $$Currency or VAT treatment is not specified.$$,
 $$Der Stundensatz beträgt 95.$$,
 $$Standard German freelance contracts denominate in EUR and treat the rate as net (zzgl. USt.). Silence does not legally change anything for a German-resident freelancer invoicing a German client, but it is a hygiene issue: cross-border or EU-to-EU situations can be argued either direction. Always nail down currency and net/gross.$$,
 $$Der Stundensatz beträgt 95,00 € netto zzgl. der gesetzlichen Umsatzsteuer.$$,
 'Contract-hygiene rule (no single statutory cite)',
 'https://www.bitkom.org/Bitkom/Publikationen',
 'custom'),

('PB-008',
 'compensation_rate',
 'medium',
 $$Reasonable project expenses (travel, software licences, third-party services) are excluded from reimbursement without offsetting rate uplift.$$,
 $$Reisekosten und sonstige Auslagen sind mit dem vereinbarten Honorar abgegolten.$$,
 $$§670 BGB (Aufwendungsersatz) is dispositive — parties can contract out of it — so this clause is enforceable. But for an on-site engagement the foregone reimbursement can erode the effective rate by 10-20 %. The redline restores the default reimbursement principle and aligns with industry practice (BITKOM model contract §6).$$,
 $$Notwendige projektbezogene Auslagen (insbesondere Reise-, Übernachtungs- und Lizenzkosten) werden nach Vorlage von Belegen zusätzlich zum vereinbarten Honorar erstattet.$$,
 '§670 BGB',
 'https://www.gesetze-im-internet.de/bgb/__670.html',
 'statute'),

('PB-009',
 'compensation_rate',
 'high',
 $$Fixed-fee project with no kill-fee or pro-rata payment on early termination by the client.$$,
 $$Bei vorzeitiger Beendigung des Vertragsverhältnisses durch den Auftraggeber besteht kein Anspruch auf Vergütung der bis dahin erbrachten Leistungen.$$,
 $$Under §649 a.F. BGB / §648 BGB n.F. (Kündigung des Werkvertrags durch den Besteller) the freelancer retains a Vergütungsanspruch for completed work, less saved expenses; that right is dispositive but waiving it without consideration is a substantial economic giveaway. Even worse, a clause excluding pro-rata payment can be void under §307 BGB as unangemessene Benachteiligung.$$,
 $$Bei Kündigung des Vertrags durch den Auftraggeber vor Fertigstellung erhält der Auftragnehmer die anteilige Vergütung für die bis zur Kündigung erbrachten Leistungen sowie 50 % des auf den noch nicht erbrachten Teil entfallenden Honorars als pauschalierter Schadensersatz, vorbehaltlich des Nachweises höherer ersparter Aufwendungen gemäß §648 Satz 3 BGB.$$,
 '§648 BGB',
 'https://www.gesetze-im-internet.de/bgb/__648.html',
 'statute'),

-- ============================================================================
-- D. INTELLECTUAL PROPERTY (UrhG)
-- ============================================================================

('PB-004',
 'intellectual_property',
 'medium',
 $$Contract transfers Background IP or tools developed prior to the project.$$,
 $$Sämtliche vom Auftragnehmer im Rahmen oder im Zusammenhang mit dem Projekt eingesetzten Werke, einschließlich vorbestehender Tools, gehen in das ausschließliche Eigentum des Auftraggebers über.$$,
 $$Under §31 UrhG Nutzungsrechte must be specifically described; a sweeping grant that pulls in pre-existing libraries, frameworks, or templates the freelancer will reuse on future engagements destroys the freelancer's reusable asset base. Background IP should be carved out and licensed, not assigned.$$,
 $$Die Einräumung von Nutzungsrechten beschränkt sich auf die im Rahmen dieses Vertrages neu geschaffenen Arbeitsergebnisse (Foreground IP). Vorbestehende Werke, Tools, Bibliotheken und Methoden des Auftragnehmers (Background IP) verbleiben in dessen Eigentum; an ihnen wird dem Auftraggeber lediglich ein einfaches, nicht-ausschließliches Nutzungsrecht eingeräumt, soweit für die Verwertung der Arbeitsergebnisse erforderlich.$$,
 '§31 UrhG',
 'https://www.gesetze-im-internet.de/urhg/__31.html',
 'statute'),

('PB-014',
 'intellectual_property',
 'high',
 $$Exclusive, worldwide, perpetual transfer of rights "for all known and unknown future uses" without separate compensation.$$,
 $$Der Auftragnehmer überträgt dem Auftraggeber sämtliche ausschließlichen, räumlich, zeitlich und inhaltlich unbeschränkten Nutzungsrechte an den Arbeitsergebnissen für alle bekannten und unbekannten Nutzungsarten.$$,
 $$§31a UrhG requires that any grant of rights for unknown future uses ("noch nicht bekannte Nutzungsarten") be in written form AND grants the author a Widerrufsrecht for three months. A boilerplate clause that purports to dispose of unknown uses without the §31a-compliant procedure is, in that part, void. Independently, §32 UrhG requires "angemessene Vergütung" — a flat project fee covering all conceivable future exploitation is regularly held inadequate.$$,
 $$Der Auftragnehmer räumt dem Auftraggeber an den im Rahmen dieses Vertrages geschaffenen Arbeitsergebnissen die für den Vertragszweck erforderlichen ausschließlichen, zeitlich und räumlich unbeschränkten Nutzungsrechte für die im Anhang abschließend bezeichneten Nutzungsarten ein. Eine Einräumung für derzeit unbekannte Nutzungsarten erfolgt nicht; eine spätere Einräumung bedarf der Schriftform und einer gesonderten angemessenen Vergütung gemäß §§31a, 32 UrhG.$$,
 '§31a UrhG, §32 UrhG',
 'https://www.gesetze-im-internet.de/urhg/__31a.html',
 'statute'),

('PB-015',
 'intellectual_property',
 'medium',
 $$Lump-sum buy-out of all rights with no provision for fairness adjustment if the work generates extraordinary returns.$$,
 $$Mit Zahlung des vereinbarten Pauschalhonorars sind sämtliche Ansprüche des Auftragnehmers, gleich aus welchem Rechtsgrund, abgegolten.$$,
 $$§32a UrhG (the "Bestseller-Paragraph") gives the author a non-waivable claim to a Fairnessausgleich if the originally agreed remuneration turns out to be conspicuously disproportionate to the proceeds from the use of the work. Contracts cannot waive this; a clause that purports to do so is void in that part. Surfacing the right (rather than waiving it) is the correct move.$$,
 $$Mit Zahlung des vereinbarten Honorars sind die laufenden Vergütungsansprüche des Auftragnehmers abgegolten. Der gesetzliche Anspruch auf weitere Beteiligung gemäß §32a UrhG bleibt hiervon unberührt.$$,
 '§32a UrhG',
 'https://www.gesetze-im-internet.de/urhg/__32a.html',
 'statute'),

('PB-016',
 'intellectual_property',
 'high',
 $$Waiver of the author's right of attribution (Urheberbenennungsrecht).$$,
 $$Der Auftragnehmer verzichtet auf jede Form der Urhebernennung im Zusammenhang mit den Arbeitsergebnissen.$$,
 $$§13 UrhG grants the author the right to be named as author of the work. This Persönlichkeitsrecht is not freely waivable; case law (BGH I ZR 158/06 — "Bauamtsleiter") permits limited contractual restrictions only where the parties' interests, the customary practice in the industry, and the type of work justify it. A blanket waiver fails that test.$$,
 $$Der Auftragnehmer ist berechtigt, in branchenüblicher Form als Urheber der Arbeitsergebnisse genannt zu werden. Die Parteien werden Form und Umfang der Urhebernennung in Bezug auf die jeweilige Verwertungsart einvernehmlich abstimmen.$$,
 '§13 UrhG',
 'https://www.gesetze-im-internet.de/urhg/__13.html',
 'statute'),

('PB-017',
 'intellectual_property',
 'medium',
 $$Client may modify, adapt, or create derivative works without the freelancer's consent.$$,
 $$Der Auftraggeber ist berechtigt, die Arbeitsergebnisse beliebig zu bearbeiten, zu kürzen, zu ergänzen und in andere Werke einzubinden.$$,
 $$§23 UrhG requires the author's consent for the publication and exploitation of Bearbeitungen of a work. The right can be granted contractually but should be calibrated — a freelance designer typically wants veto power over use that distorts their portfolio piece. The redline preserves the client's commercial flexibility while protecting against reputationally damaging modifications.$$,
 $$Der Auftraggeber darf die Arbeitsergebnisse zur Erreichung des Vertragszwecks bearbeiten, kürzen und in andere Werke einbinden. Bearbeitungen, die geeignet sind, die berechtigten geistigen oder persönlichen Interessen des Auftragnehmers am Werk zu beeinträchtigen (§14 UrhG), bedürfen seiner vorherigen Zustimmung.$$,
 '§23 UrhG, §14 UrhG',
 'https://www.gesetze-im-internet.de/urhg/__23.html',
 'statute'),

('PB-018',
 'intellectual_property',
 'medium',
 $$Rights grant covers works the freelancer has not yet created, beyond the scope of the present project.$$,
 $$Diese Rechtseinräumung umfasst auch sämtliche zukünftigen Werke des Auftragnehmers, die im weiteren Verlauf der Geschäftsbeziehung entstehen.$$,
 $$§40 UrhG specifically addresses Verträge über künftige Werke: such contracts must be in written form AND can be terminated by either party after five years on six months' notice. A clause purporting to bind the freelancer indefinitely fails the §40 form/duration regime.$$,
 $$Diese Rechtseinräumung bezieht sich ausschließlich auf die im Rahmen des vorliegenden Projektauftrags geschaffenen Arbeitsergebnisse. Für künftige Werke außerhalb dieses Auftrags bedarf es einer gesonderten schriftlichen Vereinbarung; das Kündigungsrecht gemäß §40 UrhG bleibt unberührt.$$,
 '§40 UrhG',
 'https://www.gesetze-im-internet.de/urhg/__40.html',
 'statute'),

-- ============================================================================
-- E. SCHEINSELBSTSTAENDIGKEIT (DISGUISED EMPLOYMENT)
-- ============================================================================

('PB-003',
 'scheinselbstständigkeit',
 'high',
 $$Clause requires the freelancer to follow daily instructions or fixed working hours set by the client.$$,
 $$Der Auftragnehmer hat die Tätigkeit montags bis freitags von 09:00 bis 17:00 Uhr in den Räumlichkeiten des Auftraggebers zu erbringen und unterliegt den Weisungen des Projektleiters.$$,
 $$§7 Abs. 1 SGB IV defines Beschäftigung by reference to "Tätigkeit nach Weisungen" and "Eingliederung in die Arbeitsorganisation des Weisungsgebers". A clause that imposes fixed hours and direct instructions creates two of the canonical Schein indicators in writing — the Deutsche Rentenversicherung's Statusfeststellungsverfahren will read this as employment, with retroactive social-security liability for both sides.$$,
 $$Der Auftragnehmer ist in der Wahl von Arbeitsort, Arbeitszeit und Arbeitsweise frei. Er unterliegt keinen Weisungen des Auftraggebers; fachliche Abstimmung erfolgt im Rahmen einer projektbezogenen Zusammenarbeit unter Wahrung der Weisungsfreiheit.$$,
 '§7 Abs. 1 SGB IV',
 'https://www.gesetze-im-internet.de/sgb_4/__7.html',
 'statute'),

('PB-019',
 'scheinselbstständigkeit',
 'high',
 $$Exclusivity clause: freelancer may not accept other engagements during the contract term.$$,
 $$Der Auftragnehmer verpflichtet sich, während der Laufzeit dieses Vertrags ausschließlich für den Auftraggeber tätig zu sein.$$,
 $$The DRV's Statusfeststellungs-Katalog lists "Tätigkeit für nur einen Auftraggeber" and the absence of unternehmerisches Risiko as primary Schein indicators. Contractual exclusivity makes single-client status involuntary and is therefore stronger evidence than mere fact-pattern exclusivity. The redline preserves a reasonable confidentiality interest without locking out other clients.$$,
 $$Der Auftragnehmer ist berechtigt, parallel für weitere Auftraggeber tätig zu sein, soweit dies die ordnungsgemäße Erfüllung dieses Vertrags nicht beeinträchtigt und keine konkreten Geschäftsgeheimnisse des Auftraggebers betrifft.$$,
 '§7 Abs. 1 SGB IV',
 'https://www.deutsche-rentenversicherung.de/SharedDocs/Downloads/DE/Experten/infos_fuer_arbeitgeber/summa_summarum/lexikon/s/scheinselbststaendigkeit.html',
 'agency'),

('PB-020',
 'scheinselbstständigkeit',
 'high',
 $$Freelancer is integrated into the client's organisation chart, reports to a line manager, attends mandatory team meetings.$$,
 $$Der Auftragnehmer berichtet an den Teamleiter Engineering und nimmt verpflichtend an den wöchentlichen Abteilungs-Jour-fixes teil.$$,
 $$"Eingliederung in die Arbeitsorganisation des Weisungsgebers" is the second prong of §7 Abs. 1 SGB IV alongside Weisungsgebundenheit. The DRV explicitly cites reporting lines, mandatory meetings, and use of the client's IT infrastructure as integration markers. Optional participation in coordination meetings is fine; mandatory attendance with reporting obligations crosses the line.$$,
 $$Der Auftragnehmer ist nicht in die Aufbau- oder Ablauforganisation des Auftraggebers eingegliedert. An Koordinationsterminen kann er auf eigene Einladung beratend teilnehmen; eine Teilnahmepflicht und Berichtslinien werden nicht begründet.$$,
 '§7 Abs. 1 SGB IV',
 'https://www.deutsche-rentenversicherung.de/SharedDocs/Downloads/DE/Experten/infos_fuer_arbeitgeber/summa_summarum/lexikon/s/scheinselbststaendigkeit.html',
 'agency'),

('PB-021',
 'scheinselbstständigkeit',
 'medium',
 $$Client provides all working equipment (laptop, software licences, corporate email, access badge) at its own cost.$$,
 $$Der Auftragnehmer erhält vom Auftraggeber einen Laptop, eine E-Mail-Adresse @auftraggeber.de sowie einen Werksausweis zur Verfügung gestellt.$$,
 $$Use of client-provided equipment is one of the secondary Schein indicators in the DRV catalogue. Standalone it is not decisive — client-supplied access to internal systems can be operationally necessary. But combined with other indicators (fixed hours, integration), it tips the analysis. The redline keeps necessary system access while making it clear the freelancer's primary work environment is their own.$$,
 $$Der Auftragnehmer arbeitet grundsätzlich auf eigener Hardware mit eigener Software. Soweit der Zugriff auf interne Systeme des Auftraggebers für den Projekterfolg erforderlich ist, stellt der Auftraggeber die hierfür notwendigen Zugänge bereit; eine darüber hinausgehende Ausstattung wird nicht zur Verfügung gestellt.$$,
 '§7 Abs. 1 SGB IV',
 'https://www.deutsche-rentenversicherung.de/SharedDocs/Downloads/DE/Experten/infos_fuer_arbeitgeber/summa_summarum/lexikon/s/scheinselbststaendigkeit.html',
 'agency'),

('PB-022',
 'scheinselbstständigkeit',
 'medium',
 $$Minimum on-site presence per week is contractually required.$$,
 $$Der Auftragnehmer ist verpflichtet, mindestens drei Arbeitstage pro Woche in den Räumlichkeiten des Auftraggebers zu erbringen.$$,
 $$Mandatory on-site presence is "Eingliederung" evidence. Voluntary on-site work is fine; a written minimum that the freelancer cannot deviate from is precisely the kind of evidence the DRV cites in Statusfeststellungs-Bescheide. The redline keeps client preferences for on-site collaboration without making it a contractual obligation.$$,
 $$Der Auftragnehmer kann nach eigenem Ermessen vor Ort beim Auftraggeber arbeiten. Eine vertragliche Verpflichtung zur Anwesenheit zu festen Zeiten oder an bestimmten Tagen besteht nicht; konkrete Termine vor Ort werden anlassbezogen abgestimmt.$$,
 '§7 Abs. 1 SGB IV',
 'https://www.gesetze-im-internet.de/sgb_4/__7.html',
 'statute'),

('PB-023',
 'scheinselbstständigkeit',
 'high',
 $$Contract structure indicates a single-client engagement of >5/6 of the freelancer's revenue and >75% of working time.$$,
 NULL,
 $$§2 Satz 1 Nr. 9 SGB VI ("arbeitnehmerähnliche Selbständige") triggers compulsory pension insurance for self-employed persons working "im Wesentlichen nur für einen Auftraggeber". The threshold the DRV applies in practice is 5/6 of revenue from one client. This is not Scheinselbstständigkeit per se but it is the adjacent risk: even genuine freelancers in a single-client engagement become rentenversicherungspflichtig. The freelancer should know before signing.$$,
 NULL,
 '§2 Satz 1 Nr. 9 SGB VI, §7 SGB IV',
 'https://www.gesetze-im-internet.de/sgb_6/__2.html',
 'statute'),

-- ============================================================================
-- F. TERMINATION
-- ============================================================================

('PB-024',
 'termination',
 'medium',
 $$Asymmetric notice periods: freelancer must give a longer notice than the client.$$,
 $$Der Auftraggeber kann den Vertrag mit einer Frist von 14 Tagen kündigen; der Auftragnehmer mit einer Frist von 3 Monaten.$$,
 $$An asymmetric notice regime in standard terms is regularly held an unangemessene Benachteiligung under §307 Abs. 1 BGB. Symmetry, or asymmetry the other way (client gives more notice than freelancer), is the defensible position. The redline aligns both sides to a customary 30-day window.$$,
 $$Beide Parteien können diesen Vertrag mit einer Frist von 30 Kalendertagen zum Monatsende ordentlich kündigen. Das Recht zur außerordentlichen Kündigung aus wichtigem Grund (§314 BGB) bleibt unberührt.$$,
 '§307 Abs. 1 BGB, §314 BGB',
 'https://www.gesetze-im-internet.de/bgb/__307.html',
 'statute'),

('PB-025',
 'termination',
 'high',
 $$Client can terminate at will; freelancer can only terminate for cause.$$,
 $$Der Auftraggeber ist berechtigt, das Vertragsverhältnis jederzeit ohne Angabe von Gründen zu kündigen. Der Auftragnehmer kann nur aus wichtigem Grund kündigen.$$,
 $$A pure at-will/for-cause asymmetry maximises the imbalance §307 Abs. 1 BGB targets. It also strips the freelancer of basic exit optionality — they cannot leave a souring engagement without justifying it to the client. The redline mirrors the at-will right symmetrically.$$,
 $$Beide Parteien sind berechtigt, das Vertragsverhältnis ordentlich mit einer Frist von 30 Kalendertagen zu kündigen. Das Recht zur außerordentlichen Kündigung aus wichtigem Grund bleibt für beide Seiten gleichermaßen bestehen.$$,
 '§307 Abs. 1 BGB',
 'https://www.gesetze-im-internet.de/bgb/__307.html',
 'statute'),

('PB-026',
 'termination',
 'medium',
 $$Automatic renewal clause without express opt-out notice from the freelancer.$$,
 $$Der Vertrag verlängert sich jeweils um weitere 12 Monate, sofern er nicht spätestens 60 Tage vor Ablauf gekündigt wird.$$,
 $$§309 Nr. 9 BGB caps automatic renewal terms in consumer contracts (max 1-year extension, max 3-month notice). The provision applies directly only to consumer contracts, but B2B AGB are evaluated against the same yardstick under §307 BGB plus the Indizwirkung the BGH applies. Renewal terms longer than the original primary term, or notice periods over 3 months, are routinely struck down.$$,
 $$Der Vertrag verlängert sich jeweils um weitere 6 Monate, sofern er nicht von einer Partei mit einer Frist von 30 Tagen zum Ende der jeweiligen Laufzeit in Textform gekündigt wird.$$,
 '§309 Nr. 9 BGB, §307 BGB',
 'https://www.gesetze-im-internet.de/bgb/__309.html',
 'statute'),

('PB-027',
 'termination',
 'low',
 $$On termination, freelancer must return all confidential material and client-provided assets.$$,
 $$Mit Beendigung des Vertrags gibt der Auftragnehmer sämtliche überlassenen Unterlagen und Daten unverzüglich zurück oder vernichtet sie auf Wunsch des Auftraggebers nachweislich.$$,
 $$This is standard and not risky. The clause is included to demonstrate the analyzer reports nuance: not every termination clause is a problem, and surfacing standard provisions as low-risk reassures the user that the analyzer read them, rather than silently passing them over.$$,
 NULL,
 'BITKOM Mustervertrag freie Mitarbeit',
 'https://www.bitkom.org/Bitkom/Publikationen',
 'template'),

('PB-028',
 'termination',
 'medium',
 $$Fixed-term contract auto-converts to indefinite without renewed agreement.$$,
 $$Wird die Tätigkeit nach Ablauf der Vertragslaufzeit fortgesetzt, gilt das Vertragsverhältnis als auf unbestimmte Zeit verlängert.$$,
 $$For freelance contracts this is mostly a Schein-adjacent risk: an indefinite engagement with the same single client increases the integration evidence the DRV looks at. For Werkverträge, conversion to a Dienstvertrag-style engagement may also trigger different statutory regimes (§§611 vs §631 BGB). The redline forces a fresh agreement instead of automatic continuation.$$,
 $$Eine Fortsetzung der Tätigkeit nach Ablauf der vereinbarten Vertragslaufzeit setzt eine ausdrückliche schriftliche Verlängerungsvereinbarung der Parteien voraus. Eine stillschweigende Vertragsverlängerung ist ausgeschlossen.$$,
 '§7 SGB IV, §611, §631 BGB',
 'https://www.gesetze-im-internet.de/bgb/__611.html',
 'statute'),

('PB-029',
 'termination',
 'high',
 $$Post-termination obligation: freelancer must continue handover work for X days without compensation.$$,
 $$Der Auftragnehmer ist verpflichtet, nach Beendigung des Vertrags für einen Zeitraum von 30 Tagen unentgeltlich Übergabe- und Überleitungsleistungen zu erbringen.$$,
 $$Unpaid post-termination work is an unangemessene Benachteiligung under §307 Abs. 1 BGB and likely a surprising clause under §305c BGB if buried in standard terms. Handover obligations are reasonable; doing them for free is not. The redline preserves the client's transition interest at a fair daily rate.$$,
 $$Auf Wunsch des Auftraggebers leistet der Auftragnehmer auch nach Vertragsende Übergabe- und Überleitungsunterstützung im Umfang von bis zu 5 Personentagen, vergütet zu seinem regulären Tagessatz. Darüberhinausgehende Unterstützung ist gesondert zu vereinbaren.$$,
 '§305c BGB, §307 Abs. 1 BGB',
 'https://www.gesetze-im-internet.de/bgb/__305c.html',
 'statute'),

-- ============================================================================
-- G. LIABILITY
-- ============================================================================

('PB-005',
 'liability',
 'high',
 $$Contract specifies unlimited liability of the freelancer for simple negligence.$$,
 $$Der Auftragnehmer haftet unbeschränkt für sämtliche aus seiner Tätigkeit resultierenden Schäden, gleich aus welchem Rechtsgrund.$$,
 $$Under the Indizwirkung of §309 Nr. 7 BGB applied to B2B contracts via §307 BGB, an unlimited liability cap for simple negligence in standard terms is regularly held void, particularly where it is not balanced by other provisions. Even where enforceable, it is uninsurable in practice — Berufshaftpflicht-Policen cap at the policy sum, leaving the freelancer personally exposed beyond it.$$,
 $$Die Haftung des Auftragnehmers für einfache Fahrlässigkeit ist auf vertragstypische, vorhersehbare Schäden begrenzt, der Höhe nach maximal auf die jeweilige Deckungssumme seiner Berufshaftpflichtversicherung. Die Haftung für Vorsatz, grobe Fahrlässigkeit, sowie für Schäden aus der Verletzung des Lebens, des Körpers oder der Gesundheit bleibt unberührt.$$,
 '§307 BGB, §309 Nr. 7 BGB',
 'https://www.gesetze-im-internet.de/bgb/__307.html',
 'statute'),

('PB-030',
 'liability',
 'high',
 $$Liability extends to indirect, consequential, or lost-profit damages without cap.$$,
 $$Der Auftragnehmer haftet auch für mittelbare Schäden, Folgeschäden und entgangenen Gewinn.$$,
 $$Indirect and consequential damages are economically unbounded. A clause that exposes a one-person business to a client's lost-profit claim is the kind of terms-creep that bankrupts freelancers when a project goes sideways. §307 BGB controls; the redline mirrors the standard B2B carve-out used in BITKOM and DAV model contracts.$$,
 $$Die Haftung des Auftragnehmers für mittelbare Schäden, Folgeschäden, entgangenen Gewinn und sonstige reine Vermögensschäden ist ausgeschlossen, soweit nicht Vorsatz oder grobe Fahrlässigkeit vorliegt oder eine wesentliche Vertragspflicht (Kardinalpflicht) verletzt wurde.$$,
 '§307 BGB',
 'https://www.gesetze-im-internet.de/bgb/__307.html',
 'statute'),

('PB-031',
 'liability',
 'high',
 $$Clause excludes the freelancer's liability for damages to life, body, or health.$$,
 $$Eine Haftung des Auftragnehmers für Personenschäden ist ausgeschlossen.$$,
 $$§309 Nr. 7a BGB makes any AGB exclusion of liability for damages to life, body, or health absolutely void. Even though §309 applies directly only to consumer contracts, its Indizwirkung extends through §310 Abs. 1 BGB to B2B AGB. A clause framed this way is void; clients sometimes include it expecting the freelancer not to push back, then rely on the void clause as a shield in negotiation.$$,
 $$Die Haftung für Schäden aus der Verletzung des Lebens, des Körpers oder der Gesundheit, die auf einer fahrlässigen Pflichtverletzung des Auftragnehmers oder einer vorsätzlichen oder fahrlässigen Pflichtverletzung seiner gesetzlichen Vertreter oder Erfüllungsgehilfen beruhen, bleibt unberührt.$$,
 '§309 Nr. 7a BGB, §310 Abs. 1 BGB',
 'https://www.gesetze-im-internet.de/bgb/__309.html',
 'statute'),

('PB-032',
 'liability',
 'medium',
 $$Clause attempts to exclude or cap liability for gross negligence or wilful misconduct.$$,
 $$Eine Haftung des Auftragnehmers für grobe Fahrlässigkeit ist auf 10.000 € begrenzt.$$,
 $$§309 Nr. 7b BGB makes exclusion of liability for grobe Fahrlässigkeit and Vorsatz void in AGB; the Indizwirkung carries to B2B contracts via §310 Abs. 1 BGB. Capping is a softer move than outright exclusion but the BGH has held even narrow caps for grobe Fahrlässigkeit unenforceable when the cap is not tied to a meaningful insurance reality. The redline preserves the carve-out.$$,
 $$Die Haftung des Auftragnehmers für Vorsatz und grobe Fahrlässigkeit ist der Höhe nach unbeschränkt; eine vertragliche Begrenzung dieser Haftungsfälle wird ausdrücklich nicht vereinbart.$$,
 '§309 Nr. 7b BGB, §310 Abs. 1 BGB',
 'https://www.gesetze-im-internet.de/bgb/__309.html',
 'statute'),

('PB-033',
 'liability',
 'high',
 $$Indemnification of the client against third-party claims is uncapped.$$,
 $$Der Auftragnehmer stellt den Auftraggeber von sämtlichen Ansprüchen Dritter, die aus der Tätigkeit des Auftragnehmers resultieren, frei.$$,
 $$An indemnification clause without cap or fault prerequisite operates as a back-door unlimited-liability provision and faces the same §307 BGB scrutiny as a direct uncapped liability cap. Standalone Freistellungsklauseln are particularly dangerous because they bypass the negotiated direct-liability cap in another part of the contract.$$,
 $$Der Auftragnehmer stellt den Auftraggeber von Ansprüchen Dritter frei, soweit diese auf einer schuldhaften Verletzung wesentlicher Vertragspflichten durch den Auftragnehmer beruhen. Die Freistellungspflicht ist der Höhe nach auf den vereinbarten Haftungshöchstbetrag begrenzt; sie umfasst nicht Schäden aus mittelbaren Folgen oder entgangenem Gewinn.$$,
 '§307 BGB',
 'https://www.gesetze-im-internet.de/bgb/__307.html',
 'statute'),

-- ============================================================================
-- H. AGB-KONTROLLE (UNFAIR-TERMS CONTROL)
-- ============================================================================

('PB-034',
 'agb_kontrolle',
 'medium',
 $$Material clause is hidden in a long appendix or referenced document the freelancer cannot reasonably be expected to read.$$,
 $$Die Einzelheiten der Vergütungsanpassung ergeben sich aus Anlage 7 (Anpassungsrichtlinie), abrufbar im Lieferantenportal des Auftraggebers.$$,
 $$§305c Abs. 1 BGB makes "überraschende Klauseln" — terms that, given the appearance of the contract, are so unusual the other party need not reasonably expect them — invalid as part of the contract. Burying a material economic term (rate adjustment, exclusivity, IP transfer) in an appendix while the headline contract reads benignly is the textbook §305c case.$$,
 $$Wesentliche Vertragsbestandteile (Vergütung, Laufzeit, Kündigungsregelung, Haftungsbegrenzung, Rechteeinräumung) werden ausdrücklich im Hauptvertrag geregelt. Verweise auf Anlagen sind zulässig, sofern die Anlage dem Auftragnehmer vor Vertragsschluss vorgelegen hat und auf die wesentlichen Regelungen im Hauptvertrag deutlich hingewiesen wird.$$,
 '§305c Abs. 1 BGB',
 'https://www.gesetze-im-internet.de/bgb/__305c.html',
 'statute'),

('PB-035',
 'agb_kontrolle',
 'medium',
 $$Client reserves the right to unilaterally amend material terms during the contract.$$,
 $$Der Auftraggeber behält sich vor, einzelne Bestimmungen dieses Vertrags jederzeit nach billigem Ermessen anzupassen.$$,
 $$§308 Nr. 4 BGB bars Änderungsvorbehalte that are not reasonable for the user given the customer's interests. Amendments to material terms (rate, scope, IP) cannot be unilateral. The redline allows necessary technical adjustments while requiring agreement on anything material.$$,
 $$Änderungen an den vertragswesentlichen Regelungen (Vergütung, Leistungsumfang, Laufzeit, Rechteeinräumung, Haftung) bedürfen einer einvernehmlichen schriftlichen Vereinbarung beider Parteien. Anpassungen technischer oder organisatorischer Vorgaben kann der Auftraggeber einseitig vornehmen, soweit dies für den Auftragnehmer zumutbar ist.$$,
 '§308 Nr. 4 BGB',
 'https://www.gesetze-im-internet.de/bgb/__308.html',
 'statute'),

('PB-036',
 'agb_kontrolle',
 'medium',
 $$Silence is treated as consent to future amendments.$$,
 $$Widerspricht der Auftragnehmer einer mitgeteilten Vertragsänderung nicht innerhalb von 14 Tagen, gilt seine Zustimmung als erteilt.$$,
 $$§308 Nr. 5 BGB invalidates "fingierte Erklärungen" — clauses that treat a customer's silence as a positive declaration — unless the customer is expressly told what their silence will mean and given an appropriate period to react. The redline either removes the fiction or attaches the §308 Nr. 5 safeguards explicitly.$$,
 $$Änderungen werden nur mit ausdrücklicher Zustimmung des Auftragnehmers wirksam. Eine Zustimmungsfiktion durch Schweigen ist ausgeschlossen.$$,
 '§308 Nr. 5 BGB',
 'https://www.gesetze-im-internet.de/bgb/__308.html',
 'statute'),

('PB-037',
 'agb_kontrolle',
 'medium',
 $$Vertragsstrafe (penalty) clause without cap or with a cap unrelated to the protected interest.$$,
 $$Bei Verstoß gegen die Vertraulichkeitspflicht zahlt der Auftragnehmer eine Vertragsstrafe von 25.000 € pro Verstoß.$$,
 $$BGH case law (e.g. BGH X ZR 165/03) requires Vertragsstrafen in AGB to be reasonable in relation to the protected interest and not function as a one-sided sanction mechanism. A flat amount unrelated to actual damage exposure regularly fails §307 BGB. The redline ties the penalty to demonstrable damage and caps total exposure.$$,
 $$Bei einer schuldhaften Verletzung der Vertraulichkeitspflicht wird der nach §339 BGB verwirkten Vertragsstrafe in Höhe von 5.000 € je Einzelfall vereinbart. Der Auftragnehmer behält sich den Nachweis vor, dass dem Auftraggeber kein oder ein wesentlich geringerer Schaden entstanden ist; die Gesamtsumme aller Vertragsstrafen ist auf das einfache Jahreshonorar begrenzt.$$,
 '§307 BGB, §339 BGB',
 'https://www.gesetze-im-internet.de/bgb/__339.html',
 'statute'),

('PB-038',
 'agb_kontrolle',
 'medium',
 $$Price escalation indexed to a vague or unilaterally controlled metric.$$,
 $$Der Auftraggeber kann die Vergütung jährlich nach billigem Ermessen anpassen.$$,
 $$Preisanpassungsklauseln in AGB are reviewed under §307 Abs. 1 BGB for transparency: the customer must be able to predict and verify changes. "Billiges Ermessen" of the user fails the test (BGH VIII ZR 199/12). A defensible escalation references an external, published index (Verbraucherpreisindex of the Statistisches Bundesamt is the conventional choice).$$,
 $$Die Vergütung kann einmal jährlich entsprechend der Veränderung des Verbraucherpreisindex für Deutschland (Statistisches Bundesamt) gegenüber dem Vormonat des Vertragsschlusses angepasst werden. Die Anpassung erfolgt automatisch zum 1. Januar; die Berechnungsgrundlage ist auf Verlangen offenzulegen.$$,
 '§307 Abs. 1 BGB',
 'https://www.gesetze-im-internet.de/bgb/__307.html',
 'statute'),

-- ============================================================================
-- I. CONFIDENTIALITY
-- ============================================================================

('PB-039',
 'confidentiality',
 'medium',
 $$Confidentiality obligation is perpetual ("zeitlich unbegrenzt") for all information received during the project.$$,
 $$Die Vertraulichkeitspflicht gilt zeitlich unbegrenzt über das Vertragsende hinaus.$$,
 $$§3 GeschGehG defines Geschäftsgeheimnis narrowly — information must have economic value, be subject to reasonable protective measures, and there must be a legitimate interest in secrecy. A blanket perpetual obligation extending to non-secret operational information is regularly trimmed to the GeschGehG core. The redline mirrors the §3 GeschGehG categories and time-limits the rest.$$,
 $$Die Vertraulichkeitspflicht für Geschäftsgeheimnisse im Sinne von §3 GeschGehG gilt bis zu deren öffentlicher Bekanntmachung oder dem Wegfall des Geheimhaltungsinteresses. Für sonstige als vertraulich gekennzeichnete Informationen besteht die Vertraulichkeitspflicht für die Dauer von 3 Jahren nach Vertragsende.$$,
 '§3 GeschGehG',
 'https://www.gesetze-im-internet.de/geschgehg/__3.html',
 'statute'),

('PB-040',
 'confidentiality',
 'low',
 $$Standard mutual NDA covering project information for a defined period.$$,
 $$Jede Partei verpflichtet sich, die ihr im Rahmen der Vertragsdurchführung bekannt gewordenen vertraulichen Informationen der anderen Partei nicht ohne deren Zustimmung an Dritte weiterzugeben.$$,
 $$Standard mutual NDA — surfaced as low risk so the analyzer's report acknowledges the clause was reviewed rather than skipped. Mirrors the BITKOM Mustervertrag freie Mitarbeit §9 (Vertraulichkeit).$$,
 NULL,
 'BITKOM Mustervertrag freie Mitarbeit §9',
 'https://www.bitkom.org/Bitkom/Publikationen',
 'template'),

('PB-041',
 'confidentiality',
 'medium',
 $$NDA scope lacks the standard carve-outs for publicly known, independently developed, or already-known information.$$,
 $$Sämtliche Informationen, die der Auftragnehmer im Zusammenhang mit der Tätigkeit erhält, gelten als vertraulich.$$,
 $$Without carve-outs the freelancer is technically in breach for talking about generally-known facts (e.g., the client's industry, public product launches). §3 GeschGehG requires that protected information actually be secret; the BGH (I ZR 152/15) has read appropriate carve-outs into NDAs even when not stated, but relying on judicial implication is bad hygiene. State the carve-outs explicitly.$$,
 $$Die Vertraulichkeitspflicht erstreckt sich nicht auf Informationen, die (i) allgemein bekannt sind oder ohne Verschulden des Auftragnehmers werden, (ii) dem Auftragnehmer bei Empfang nachweislich bereits bekannt waren, (iii) vom Auftragnehmer unabhängig entwickelt werden, oder (iv) dem Auftragnehmer rechtmäßig durch Dritte ohne Vertraulichkeitsbeschränkung bekannt gegeben werden.$$,
 '§3 GeschGehG',
 'https://www.gesetze-im-internet.de/geschgehg/__3.html',
 'statute'),

('PB-042',
 'confidentiality',
 'medium',
 $$NDA forbids the freelancer from naming the client as a reference or showing the work in their portfolio.$$,
 $$Der Auftragnehmer ist nicht berechtigt, das Vertragsverhältnis oder die für den Auftraggeber erbrachten Leistungen Dritten gegenüber zu erwähnen oder als Referenz zu nutzen.$$,
 $$Reference rights are the freelancer's main marketing asset. A blanket prohibition is rarely necessary to protect a legitimate Geschäftsgeheimnis interest — the existence of the engagement and the type of work performed is usually not itself secret. The redline preserves the client's veto over sensitive specifics while securing the freelancer's right to name the engagement.$$,
 $$Der Auftragnehmer ist berechtigt, den Auftraggeber als Referenzkunden zu nennen und allgemeine Angaben zur Art der erbrachten Leistung in seinem Portfolio zu verwenden. Die Veröffentlichung konkreter Projektergebnisse oder vertraulicher Details bedarf der vorherigen schriftlichen Zustimmung des Auftraggebers, die nicht ohne sachlichen Grund verweigert werden darf.$$,
 'Custom rule (industry norm; no single statute)',
 'https://www.vgsd.de',
 'custom'),

-- ============================================================================
-- J. NON-COMPETE / KUNDENSCHUTZ
-- ============================================================================

('PB-043',
 'non_compete',
 'high',
 $$Post-contractual non-compete obligation without compensation (Karenzentschädigung).$$,
 $$Der Auftragnehmer verpflichtet sich, für einen Zeitraum von 24 Monaten nach Beendigung des Vertrags nicht für Wettbewerber des Auftraggebers tätig zu sein.$$,
 $$For Handelsvertreter §90a HGB requires Karenzentschädigung of at least half the most recent contractual remuneration; the BGH and BAG apply the principle by analogy to other "arbeitnehmerähnliche" self-employed persons (BAG 10 AZR 358/03, BGH VII ZR 25/19). A non-compete without compensation is unenforceable; a freelancer who signs may comply unnecessarily, foreclosing legitimate work.$$,
 $$Verpflichtet sich der Auftragnehmer auf Wunsch des Auftraggebers zu einem nachvertraglichen Wettbewerbsverbot, so zahlt der Auftraggeber für die Dauer des Verbots eine monatliche Karenzentschädigung in Höhe von mindestens 50 % der zuletzt durchschnittlich gezahlten monatlichen Vergütung. Ohne entsprechende Vereinbarung über die Karenzentschädigung besteht kein nachvertragliches Wettbewerbsverbot.$$,
 '§90a HGB (analog)',
 'https://www.gesetze-im-internet.de/hgb/__90a.html',
 'statute'),

('PB-044',
 'non_compete',
 'high',
 $$Non-compete extends beyond the §74a HGB statutory maximum of two years post-contract.$$,
 $$Der Auftragnehmer verpflichtet sich, für einen Zeitraum von 5 Jahren nach Vertragsende keine konkurrierende Tätigkeit aufzunehmen.$$,
 $$§74a Abs. 1 HGB caps post-contractual non-competes for Handlungsgehilfen at two years; applied by analogy to arbeitnehmerähnliche freelancers, anything longer is unverbindlich. Two years is also the practical economic ceiling: beyond that, the freelancer's market knowledge is stale and the client's protection interest has dissipated.$$,
 $$Das nachvertragliche Wettbewerbsverbot ist auf einen Zeitraum von höchstens 24 Monaten ab Vertragsende begrenzt. Eine darüberhinausgehende Verpflichtung ist unwirksam.$$,
 '§74a Abs. 1 HGB',
 'https://www.gesetze-im-internet.de/hgb/__74a.html',
 'statute'),

('PB-045',
 'non_compete',
 'medium',
 $$Non-compete has no geographic or sectoral limitation.$$,
 $$Der Auftragnehmer wird in keiner Weise für Wettbewerber tätig.$$,
 $$§74a Abs. 1 Satz 2 HGB requires the non-compete to be reasonably limited "nach Ort, Zeit und Gegenstand". An unlimited geographical and sectoral scope is, in that part, void. The redline narrows to the actual market overlap — typically the client's products in the territories it operates.$$,
 $$Das Wettbewerbsverbot beschränkt sich auf Tätigkeiten in unmittelbarem sachlichen Wettbewerb mit dem konkreten Geschäftsfeld des Auftraggebers, in dem der Auftragnehmer eingesetzt war, und auf das Gebiet der Bundesrepublik Deutschland.$$,
 '§74a Abs. 1 Satz 2 HGB',
 'https://www.gesetze-im-internet.de/hgb/__74a.html',
 'statute'),

('PB-046',
 'non_compete',
 'medium',
 $$Customer-protection clause covers customers the freelancer never served or learned about.$$,
 $$Der Auftragnehmer wird für einen Zeitraum von 24 Monaten keine Kunden des Auftraggebers betreuen.$$,
 $$A Kundenschutzklausel covering the client's entire customer base — rather than the customers the freelancer actually contacted or learned material non-public information about — is regularly struck under §307 BGB as overbroad. The legitimate protection interest extends only to relationships the freelancer can plausibly trade on.$$,
 $$Der Auftragnehmer wird für einen Zeitraum von 12 Monaten nach Vertragsende keine aktiven Akquise-Maßnahmen gegenüber denjenigen Kunden des Auftraggebers ergreifen, mit denen er im Rahmen seiner Tätigkeit für den Auftraggeber unmittelbar zusammengearbeitet hat. Die Beratung von Kunden, die sich aus eigener Initiative an den Auftragnehmer wenden, bleibt zulässig.$$,
 '§307 BGB',
 'https://www.gesetze-im-internet.de/bgb/__307.html',
 'statute'),

-- ============================================================================
-- K. ACCEPTANCE / WERKVERTRAG
-- ============================================================================

('PB-047',
 'acceptance_werkvertrag',
 'medium',
 $$Fictitious acceptance (fiktive Abnahme) is triggered without the §640 Abs. 2 BGB Aufforderung-with-Frist procedure.$$,
 $$Erfolgt innerhalb von 14 Tagen nach Lieferung keine Abnahmeerklärung, gilt das Werk als abgenommen.$$,
 $$§640 Abs. 2 BGB allows fictitious acceptance only if the contractor sets a reasonable deadline to the client AND the client neither accepts nor refuses with at least one specific defect within the deadline. A clause that deems acceptance after a flat period without the Aufforderung is void in that part. The redline tracks the §640 Abs. 2 procedure precisely.$$,
 $$Fordert der Auftragnehmer den Auftraggeber nach Fertigstellung zur Abnahme auf und setzt ihm hierzu eine angemessene Frist, gilt das Werk als abgenommen, wenn der Auftraggeber innerhalb der Frist die Abnahme nicht unter Angabe mindestens eines konkreten Mangels verweigert (§640 Abs. 2 BGB).$$,
 '§640 Abs. 2 BGB',
 'https://www.gesetze-im-internet.de/bgb/__640.html',
 'statute'),

('PB-048',
 'acceptance_werkvertrag',
 'medium',
 $$Acceptance can be withheld for "subjective dissatisfaction" without reference to objective defect criteria.$$,
 $$Die Abnahme erfolgt nach Maßgabe der Zufriedenheit des Auftraggebers.$$,
 $$The Werkvertrag-Abnahmeprüfung under §640 Abs. 1 BGB is objective: the client must accept if the work is substantially free of defects; a subjective satisfaction standard contradicts that and is regularly held an unangemessene Benachteiligung. The redline restores the objective standard and ties non-acceptance to documented defects.$$,
 $$Die Abnahme erfolgt anhand objektiver Kriterien gemäß den im Anhang definierten Abnahmekriterien. Eine Verweigerung der Abnahme setzt einen wesentlichen Mangel im Sinne von §634 BGB voraus, der schriftlich zu rügen ist.$$,
 '§640 Abs. 1 BGB',
 'https://www.gesetze-im-internet.de/bgb/__640.html',
 'statute'),

('PB-049',
 'acceptance_werkvertrag',
 'medium',
 $$"Minor changes" can be requested by the client at any time without renegotiation of scope or fee.$$,
 $$Der Auftraggeber kann jederzeit unwesentliche Änderungen am Leistungsumfang verlangen, ohne dass dies eine Anpassung der Vergütung rechtfertigt.$$,
 $$"Unwesentlich" is undefined and operates as a one-way ratchet for scope creep. §650b BGB (introduced 2018) actually gives the client a Anordnungsrecht for changes in Werkverträgen, but specifically requires renegotiation of remuneration under §650c BGB. The redline aligns the contract with the §§650b-c regime.$$,
 $$Änderungen am vereinbarten Leistungsumfang erfolgen im Rahmen des §650b BGB. Der Auftragnehmer hat Anspruch auf Anpassung der Vergütung gemäß §650c BGB; bei Mehraufwand ist vor Ausführung Einvernehmen über die zusätzliche Vergütung herzustellen.$$,
 '§650b, §650c BGB',
 'https://www.gesetze-im-internet.de/bgb/__650b.html',
 'statute'),

('PB-050',
 'acceptance_werkvertrag',
 'low',
 $$Milestone-based partial acceptance with defined deliverables.$$,
 $$Die Leistung wird in den im Projektplan definierten Meilensteinen erbracht und jeweils nach Fertigstellung eines Meilensteins gesondert abgenommen.$$,
 $$Standard, freelancer-friendly structure — partial acceptances reduce the freelancer's exposure to a late-stage rejection of the entire deliverable. Surfacing it as a low-risk "well-drafted" finding gives the report positive content alongside the warnings.$$,
 NULL,
 'BITKOM Mustervertrag freie Mitarbeit §4',
 'https://www.bitkom.org/Bitkom/Publikationen',
 'template'),

-- ============================================================================
-- L. WARRANTY / MAENGELHAFTUNG
-- ============================================================================

('PB-051',
 'warranty_maengel',
 'medium',
 $$Warranty period (Verjährungsfrist für Mängelansprüche) extended beyond the §634a BGB defaults.$$,
 $$Die Verjährungsfrist für Mängelansprüche beträgt 5 Jahre ab Abnahme.$$,
 $$§634a Abs. 1 Nr. 1 BGB sets the default Verjährungsfrist at 2 years for Werke not connected to a building. Extending the period in AGB is contractually possible but stacks long-tail liability on the freelancer; the BGH applies §307 BGB scrutiny to extensions beyond what the protected interest justifies. The redline restores the statutory two-year period.$$,
 $$Die Verjährungsfrist für Mängelansprüche beträgt 24 Monate ab Abnahme entsprechend §634a Abs. 1 Nr. 1 BGB.$$,
 '§634a BGB',
 'https://www.gesetze-im-internet.de/bgb/__634a.html',
 'statute'),

('PB-052',
 'warranty_maengel',
 'medium',
 $$Cure period (Nacherfüllungsfrist) is set unreasonably short, e.g. 24 hours for software defects.$$,
 $$Der Auftragnehmer hat festgestellte Mängel innerhalb von 24 Stunden nach Mangelanzeige zu beheben.$$,
 $$§635 Abs. 2 BGB obliges the contractor to bear the cure costs but does not impose a hard deadline; the deadline must be reasonable in light of the defect's complexity. A 24-hour blanket period is the kind of "unangemessen kurze Frist" §307 BGB strikes down, and creates an immediate Rücktritt/Minderung trigger if the freelancer cannot meet it.$$,
 $$Der Auftragnehmer behebt festgestellte Mängel im Rahmen der Nacherfüllung innerhalb einer angemessenen, vom Auftraggeber gesetzten Frist. Die Frist beträgt mindestens 5 Werktage; bei kritischen Mängeln, die einen Produktivbetrieb beeinträchtigen, vereinbaren die Parteien eine angemessene kürzere Frist.$$,
 '§635 BGB, §307 BGB',
 'https://www.gesetze-im-internet.de/bgb/__635.html',
 'statute'),

('PB-053',
 'warranty_maengel',
 'medium',
 $$Client's right of withdrawal (Rücktritt) and price reduction (Minderung) is excluded.$$,
 $$Bei Mängeln stehen dem Auftraggeber ausschließlich Nacherfüllungsansprüche zu; das Recht zum Rücktritt und zur Minderung ist ausgeschlossen.$$,
 $$§634 BGB lists Nacherfüllung, Selbstvornahme, Rücktritt, Minderung, and Schadensersatz as the cumulative warranty toolkit. Excluding Rücktritt and Minderung in AGB is regularly held an unangemessene Benachteiligung under §307 BGB and arguably contradicts §309 Nr. 8b BGB by analogy. From the freelancer's side, the clause may look client-unfriendly, but it is also unlikely to hold up — meaning the client retains the rights anyway.$$,
 $$Bei Mängeln stehen dem Auftraggeber die gesetzlichen Mängelrechte gemäß §634 BGB nach erfolglosem Ablauf einer angemessenen Nacherfüllungsfrist zu, einschließlich des Rechts zu Rücktritt und Minderung.$$,
 '§634 BGB, §309 Nr. 8b BGB, §307 BGB',
 'https://www.gesetze-im-internet.de/bgb/__634.html',
 'statute'),

('PB-054',
 'warranty_maengel',
 'medium',
 $$Warranty clause includes consequential damages without cap.$$,
 $$Die Mängelhaftung des Auftragnehmers umfasst auch sämtliche Folgeschäden, die dem Auftraggeber aus dem Mangel entstehen.$$,
 $$Folgeschäden are not part of the warranty regime under §634 BGB — they fall under §634 Nr. 4 BGB Schadensersatzansprüche, which are subject to the general liability framework. Pulling consequential damages into the warranty clause without the §307-compliant carve-outs evades the negotiated liability cap. The redline restores the standard separation.$$,
 $$Die Mängelhaftung umfasst die in §634 Nr. 1-3 BGB genannten Rechte. Schadensersatzansprüche aus Mängeln richten sich nach den allgemeinen Haftungsregelungen dieses Vertrags; die dort vereinbarten Haftungsbegrenzungen gelten entsprechend.$$,
 '§634 Nr. 4 BGB, §307 BGB',
 'https://www.gesetze-im-internet.de/bgb/__634.html',
 'statute'),

-- ============================================================================
-- M. DATA PROTECTION (DSGVO)
-- ============================================================================

('PB-055',
 'data_protection',
 'high',
 $$Freelancer processes personal data of the client's customers without an Auftragsverarbeitungsvertrag (AVV) being concluded.$$,
 $$Der Auftragnehmer verarbeitet im Rahmen seiner Tätigkeit personenbezogene Daten des Auftraggebers; eine gesonderte Auftragsverarbeitungsvereinbarung ist nicht erforderlich.$$,
 $$Art. 28 DSGVO mandates an Auftragsverarbeitungsvertrag whenever a processor handles personal data on behalf of a controller. Operating without one is a Verstoß for both parties and triggers Bußgeld liability under Art. 83(4)(a) DSGVO. The redline points at the standard solution: a separate AVV.$$,
 $$Verarbeitet der Auftragnehmer im Rahmen seiner Tätigkeit personenbezogene Daten im Auftrag des Auftraggebers, schließen die Parteien vor Beginn der Verarbeitung eine gesonderte Auftragsverarbeitungsvereinbarung gemäß Art. 28 DSGVO ab. Diese ist Anlage 2 zu diesem Vertrag.$$,
 'Art. 28 DSGVO',
 'https://eur-lex.europa.eu/eli/reg/2016/679/oj',
 'statute'),

('PB-056',
 'data_protection',
 'medium',
 $$DSGVO breach-notification mechanics (who notifies whom, within what time) are not addressed.$$,
 NULL,
 $$Art. 33 DSGVO requires the controller to notify the supervisory authority within 72 hours of becoming aware of a personal-data breach; Art. 33(2) requires the processor to notify the controller "without undue delay" upon becoming aware. Silence on this in the contract leaves the freelancer-as-processor exposed if a breach occurs and the timeline becomes contested.$$,
 $$Der Auftragnehmer informiert den Auftraggeber unverzüglich, spätestens jedoch innerhalb von 24 Stunden nach Kenntniserlangung, über jede Verletzung des Schutzes personenbezogener Daten gemäß Art. 33 DSGVO; die Mitteilung enthält die in Art. 33 Abs. 3 DSGVO genannten Informationen, soweit sie zu diesem Zeitpunkt bereits verfügbar sind.$$,
 'Art. 33 DSGVO',
 'https://eur-lex.europa.eu/eli/reg/2016/679/oj',
 'statute'),

('PB-057',
 'data_protection',
 'high',
 $$Personal data may be transferred to a third country (e.g. for a US-based subprocessor) without DSGVO Art. 44-49 safeguards.$$,
 $$Der Auftragnehmer ist berechtigt, Subunternehmer im außereuropäischen Ausland einzuschalten.$$,
 $$After Schrems II (CJEU C-311/18) any transfer to a third country requires an Art. 44-49 DSGVO basis — adequacy decision (e.g. EU-US DPF), Standardvertragsklauseln plus a transfer impact assessment, or one of the narrow Art. 49 derogations. A clause that permits transfer in the abstract, without naming the safeguard, fails the AVV transparency requirement under Art. 28(3)(a) DSGVO.$$,
 $$Übermittlungen personenbezogener Daten in Drittländer erfolgen ausschließlich auf Grundlage eines Angemessenheitsbeschlusses gemäß Art. 45 DSGVO oder unter Verwendung der EU-Standardvertragsklauseln gemäß Art. 46 Abs. 2 DSGVO. Die Einschaltung von Unterauftragsverarbeitern in Drittländern bedarf der vorherigen schriftlichen Genehmigung des Auftraggebers.$$,
 'Art. 44-49 DSGVO',
 'https://eur-lex.europa.eu/eli/reg/2016/679/oj',
 'statute'),

('PB-058',
 'data_protection',
 'medium',
 $$DSGVO compliance burden (Datenschutzbeauftragter, Verzeichnis von Verarbeitungstätigkeiten, technical/organisational measures) is shifted entirely to the freelancer.$$,
 $$Der Auftragnehmer trägt die alleinige Verantwortung für die Einhaltung sämtlicher datenschutzrechtlicher Verpflichtungen.$$,
 $$Art. 28(3) DSGVO defines the processor's duties precisely; obligations the controller cannot delegate (e.g., the lawful basis for processing under Art. 6, the Art. 30 controller's Verzeichnis) cannot be contracted to the processor. The clause is partially void; meanwhile, the freelancer may believe they have undertaken obligations they cannot legally fulfil.$$,
 $$Der Auftragnehmer erfüllt die Pflichten eines Auftragsverarbeiters gemäß Art. 28 DSGVO. Die datenschutzrechtliche Verantwortlichkeit als Verantwortlicher (Controller) verbleibt beim Auftraggeber; insbesondere die Festlegung der Rechtsgrundlage und die Erfüllung der Informationspflichten gegenüber den betroffenen Personen.$$,
 'Art. 28 DSGVO',
 'https://eur-lex.europa.eu/eli/reg/2016/679/oj',
 'statute'),

-- ============================================================================
-- N. WORKING TIME
-- ============================================================================

('PB-059',
 'working_time',
 'medium',
 $$Contract specifies a maximum daily or weekly working time for the freelancer.$$,
 $$Der Auftragnehmer wird durchschnittlich 40 Stunden pro Woche, jedoch maximal 48 Stunden, für den Auftraggeber tätig.$$,
 $$The Arbeitszeitgesetz (ArbZG) does not apply to genuine freelancers; specifying maximum working times in a freelance contract is therefore either redundant (if the freelancer is genuinely self-determined) or a Schein-indicator showing the parties treat the engagement as employment-like. Either way it is a flag worth raising.$$,
 $$Die Tätigkeit erfolgt im selbstbestimmten Umfang. Der Auftragnehmer organisiert seine Arbeitszeit eigenverantwortlich; eine vertragliche Festlegung von Höchst- oder Mindestarbeitszeiten erfolgt nicht.$$,
 '§7 SGB IV, §2 ArbZG',
 'https://www.gesetze-im-internet.de/arbzg/__2.html',
 'statute'),

('PB-060',
 'working_time',
 'medium',
 $$MiLoG §17 Aufzeichnungspflicht: contract requires daily working-time records to be submitted to the client.$$,
 $$Der Auftragnehmer erfasst seine Arbeitszeit täglich und übermittelt sie dem Auftraggeber wöchentlich zur Prüfung.$$,
 $$§17 MiLoG documentation duties apply to employers in specific Branchen, not to genuine freelancers. A clause requiring time logs that go to the client for "Prüfung" mimics the employer-employee oversight relationship and is another Schein indicator. Time records for the freelancer's own invoicing are fine; submission for client review is not.$$,
 $$Der Auftragnehmer erstellt eigene Aufzeichnungen über die für die Vertragserfüllung aufgewendete Arbeitszeit ausschließlich zu eigenen Zwecken (Rechnungsstellung, Steuer). Eine Vorlagepflicht gegenüber dem Auftraggeber besteht nicht.$$,
 '§17 MiLoG, §7 SGB IV',
 'https://www.gesetze-im-internet.de/milog/__17.html',
 'statute'),

('PB-061',
 'working_time',
 'low',
 $$Contract is silent on working time; freelancer organises their own schedule.$$,
 NULL,
 $$Standard for genuine freelance arrangements — surfaced as low-risk so the report positively confirms the absence of Schein-indicators in this dimension. Mirrors the DRV Statusfeststellungs-Katalog's own framing of "Tätigkeit nach freiem Ermessen".$$,
 NULL,
 'DRV Statusfeststellungs-Katalog',
 'https://www.deutsche-rentenversicherung.de/SharedDocs/Downloads/DE/Experten/infos_fuer_arbeitgeber/summa_summarum/lexikon/s/scheinselbststaendigkeit.html',
 'agency'),

-- ============================================================================
-- O. DISPUTE RESOLUTION
-- ============================================================================

('PB-062',
 'dispute_resolution',
 'medium',
 $$Gerichtsstandsvereinbarung designates the client's seat without regard to §38 ZPO formal requirements.$$,
 $$Ausschließlicher Gerichtsstand für alle Streitigkeiten aus diesem Vertrag ist der Sitz des Auftraggebers.$$,
 $$§38 Abs. 1 ZPO permits Gerichtsstandsvereinbarungen between merchants (Kaufleute) and other defined groups; for freelancers who are not formally Kaufleute (i.e. not registered in the Handelsregister), Abs. 2 imposes additional requirements. A blanket clause that ignores the freelancer's legal status risks being void, leaving the §29 ZPO general jurisdiction in place.$$,
 $$Sind beide Parteien Kaufleute oder juristische Personen des öffentlichen Rechts, ist ausschließlicher Gerichtsstand für alle Streitigkeiten aus diesem Vertrag der Sitz des Auftraggebers. Andernfalls richtet sich der Gerichtsstand nach den gesetzlichen Bestimmungen (§§12 ff. ZPO).$$,
 '§38 ZPO',
 'https://www.gesetze-im-internet.de/zpo/__38.html',
 'statute'),

('PB-063',
 'dispute_resolution',
 'medium',
 $$Foreign applicable law without a clear nexus.$$,
 $$Auf diesen Vertrag findet das Recht der Republik Irland Anwendung.$$,
 $$Art. 3 Rom I-VO permits free choice of applicable law in B2B contracts, but designating a foreign jurisdiction without operational connection imposes search costs that fall asymmetrically on the freelancer (foreign-language case law, foreign legal counsel). The redline restores German law as the default and limits foreign-law choices to genuinely cross-border situations.$$,
 $$Auf diesen Vertrag findet das Recht der Bundesrepublik Deutschland unter Ausschluss der Kollisionsnormen Anwendung. Das UN-Kaufrecht (CISG) ist ausgeschlossen.$$,
 'Art. 3 Rom I-VO',
 'https://eur-lex.europa.eu/eli/reg/2008/593/oj',
 'statute'),

('PB-064',
 'dispute_resolution',
 'medium',
 $$Mandatory arbitration with cost burden falling on the freelancer.$$,
 $$Streitigkeiten werden ausschließlich durch ein Schiedsgericht entschieden; die Kosten des Schiedsverfahrens trägt der Auftragnehmer.$$,
 $$Schiedsklauseln are valid under §1029 ZPO but the cost-allocation must not de facto block court access. A clause loading arbitration costs entirely on the freelancer (Schiedsrichtervergütung, DIS-Gebühren can run €20-50k for a moderate dispute) is regularly held an unangemessene Benachteiligung under §307 BGB, especially where the disputed amounts are small relative to the arbitration cost.$$,
 $$Streitigkeiten aus diesem Vertrag werden zunächst in einem schriftlichen Mediationsverfahren beigelegt. Scheitert die Mediation, sind die ordentlichen Gerichte zuständig. Eine Schiedsabrede wird nicht getroffen.$$,
 '§1029 ZPO, §307 BGB',
 'https://www.gesetze-im-internet.de/zpo/__1029.html',
 'statute'),

-- ============================================================================
-- P. FORCE MAJEURE
-- ============================================================================

('PB-065',
 'force_majeure',
 'low',
 $$Standard force-majeure clause covering events beyond the parties' reasonable control.$$,
 $$Keine Partei haftet für die Nichterfüllung von Pflichten aus diesem Vertrag, soweit sie auf höherer Gewalt beruht (Naturkatastrophen, Krieg, behördliche Anordnungen, Pandemien).$$,
 $$Standard, balanced provision — surfaced as low-risk to confirm review. Mirrors the ICC Force Majeure Clause 2020 and the BITKOM model contract's höhere-Gewalt language.$$,
 NULL,
 'ICC Force Majeure Clause 2020 / BITKOM Mustervertrag §11',
 'https://iccwbo.org/business-solutions/force-majeure-clause/',
 'template'),

('PB-066',
 'force_majeure',
 'medium',
 $$Force majeure suspends the client's payment obligation for already-completed work.$$,
 $$Bei höherer Gewalt sind beide Parteien für die Dauer des Ereignisses von ihren Leistungspflichten, einschließlich der Zahlungspflicht, befreit.$$,
 $$Force majeure properly excuses non-performance of the affected obligation, not collateral monetary obligations for completed performance. A clause that suspends payment for already-delivered work effectively shifts the client's general business risk to the freelancer and is regularly held an unangemessene Benachteiligung under §307 BGB.$$,
 $$Bei höherer Gewalt sind die durch das Ereignis unmittelbar betroffenen Leistungspflichten für dessen Dauer suspendiert. Bereits erbrachte und abgrenzbar abnahmefähige Leistungen sind unabhängig vom Eintritt höherer Gewalt zu vergüten.$$,
 '§307 BGB',
 'https://www.gesetze-im-internet.de/bgb/__307.html',
 'statute')

ON CONFLICT (id) DO UPDATE SET
    clause_type           = EXCLUDED.clause_type,
    risk_level            = EXCLUDED.risk_level,
    pattern_description   = EXCLUDED.pattern_description,
    example_risky_wording = EXCLUDED.example_risky_wording,
    legal_reasoning       = EXCLUDED.legal_reasoning,
    recommended_redline   = EXCLUDED.recommended_redline,
    statute_ref           = EXCLUDED.statute_ref,
    source_url            = EXCLUDED.source_url,
    source_type           = EXCLUDED.source_type,
    -- Reset embedding only when the semantic content actually changed,
    -- so seed_vectors.py without --force re-embeds exactly the rows
    -- that need it. This avoids gratuitous OpenAI calls on every reseed.
    embedding             = CASE
        WHEN playbook.clause_type           IS DISTINCT FROM EXCLUDED.clause_type
          OR playbook.pattern_description   IS DISTINCT FROM EXCLUDED.pattern_description
          OR playbook.example_risky_wording IS DISTINCT FROM EXCLUDED.example_risky_wording
          OR playbook.legal_reasoning       IS DISTINCT FROM EXCLUDED.legal_reasoning
          OR playbook.recommended_redline   IS DISTINCT FROM EXCLUDED.recommended_redline
        THEN NULL
        ELSE playbook.embedding
    END;

-- ============================================================================
-- Sanity check: confirm 66 rows are present after seed.
-- This is a hint, not a hard assertion; the CI integrity script
-- (scripts/check_playbook.py — TODO) is the authoritative gate.
-- ============================================================================
-- Run manually:  SELECT COUNT(*) FROM playbook;       -- expect 66
--                SELECT COUNT(*) FROM playbook
--                  WHERE statute_ref IS NULL OR statute_ref = '';  -- expect 0
--                SELECT COUNT(*) FROM playbook
--                  WHERE source_type NOT IN
--                    ('statute','case','agency','template','custom'); -- expect 0
