import os, re

repo = r'C:\Users\ljpri\OneDrive\Desktop\Learning Pathways\LearningPathways\Bhu Loka - भूलोक'
fpath = os.path.join(repo, 'Assets', 'vendor', 'bhu_loka_urban_studio.js')

with open(fpath, 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update hardcoded header and titles in renderSiteAnalyticsPanel
old_header_title = """              <span style="font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:800;color:#f8fafc;letter-spacing:0.02em;">🛰️ TELANGANA SATELLITE LAKE &amp; LAND ENFORCEMENT ENGINE</span>
              <span style="font-family:'JetBrains Mono',monospace;font-size:9px;font-weight:700;background:rgba(239,68,68,0.18);color:#fca5a5;border:1px solid rgba(239,68,68,0.4);padding:2px 7px;border-radius:4px;">CHALLENGE 03 &bull; HYDRAA</span>
              <span style="font-family:'JetBrains Mono',monospace;font-size:9px;font-weight:700;background:rgba(2,132,199,0.18);color:#38bdf8;border:1px solid rgba(56,189,248,0.4);padding:2px 7px;border-radius:4px;">REVENUE &bull; MA&amp;UD &bull; IRRIGATION</span>"""

new_header_title = """              <span style="font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:800;color:#f8fafc;letter-spacing:0.02em;">🛰️ BHU LOKA &bull; CADASTRAL &amp; WATERBODY SCREENING ENGINE</span>
              <span style="font-family:'JetBrains Mono',monospace;font-size:9px;font-weight:700;background:rgba(56,189,248,0.18);color:#7dd3fc;border:1px solid rgba(56,189,248,0.4);padding:2px 7px;border-radius:4px;">SOVEREIGN SPATIAL AUDIT</span>
              <span style="font-family:'JetBrains Mono',monospace;font-size:9px;font-weight:700;background:rgba(16,185,129,0.18);color:#6ee7b7;border:1px solid rgba(16,185,129,0.4);padding:2px 7px;border-radius:4px;">BSA 2023 §63 COMPLIANT SCREENING</span>"""

if old_header_title in code:
    code = code.replace(old_header_title, new_header_title)
    print("Replaced header title")
else:
    print("WARNING: old_header_title not matched exactly")

# 2. Replace the top right encroachment flagged box
old_flag_box = """            <div style="text-align:right;font-family:'JetBrains Mono',monospace;font-size:9.5px;">
              <div style="color:#fca5a5;font-weight:700;">🚨 10.95 ACRES ENCROACHMENT FLAGGED</div>
              <div style="color:#94a3b8;font-size:8.5px;">Section 23 Demolition Notices Prepared</div>
            </div>"""

new_flag_box = """            <div style="text-align:right;font-family:'JetBrains Mono',monospace;font-size:9.5px;">
              <div style="color:#fde047;font-weight:700;">⚠️ POTENTIAL SPATIAL OVERLAP IDENTIFIED</div>
              <div style="color:#94a3b8;font-size:8.5px;">Requires Official Cadastral &amp; Revenue Field Survey</div>
            </div>"""

if old_flag_box in code:
    code = code.replace(old_flag_box, new_flag_box)
    print("Replaced flag box")
else:
    print("WARNING: old_flag_box not matched exactly")

# 3. Replace STATUTORY ENFORCEMENT CALLOUT
old_callout = """        <!-- STATUTORY ENFORCEMENT CALLOUT -->
        <div style="background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.35);border-radius:8px;padding:8px 12px;display:flex;align-items:center;justify-content:space-between;gap:10px;font-family:'JetBrains Mono',monospace;font-size:9.5px;color:#cbd5e1;flex-wrap:wrap;">
          <div style="display:flex;align-items:center;gap:8px;">
            <span style="font-size:16px;">🚨</span>
            <div>
              <strong style="color:#fca5a5;">STATUTORY 30m LAKE FULL TANK LEVEL (FTL) VIOLATION DETECTED:</strong>
              <span> 3 illegal encroachments identified in Sy. Nos. 104/A, 108/2 &amp; 112 within the gazetted non-construction perimeter of ${activeSite.name}. Evidentiary Hash: <code style="color:#38bdf8;">SHA256:7f83b1657ff1fc53...</code></span>
            </div>
          </div>
          <span style="background:#ef4444;color:#ffffff;padding:2px 7px;border-radius:3px;font-weight:700;font-size:8.5px;white-space:nowrap;">DEMOLITION / NOTICE MANDATED</span>
        </div>"""

new_callout = """        <!-- SOVEREIGN SPATIAL SCREENING CALLOUT -->
        <div style="background:rgba(234,179,8,0.08);border:1px solid rgba(234,179,8,0.35);border-radius:8px;padding:8px 12px;display:flex;align-items:center;justify-content:space-between;gap:10px;font-family:'JetBrains Mono',monospace;font-size:9.5px;color:#cbd5e1;flex-wrap:wrap;">
          <div style="display:flex;align-items:center;gap:8px;">
            <span style="font-size:16px;">⚠️</span>
            <div>
              <strong style="color:#fde047;">POTENTIAL SPATIAL OVERLAP DETECTED (TECHNICAL SCREENING):</strong>
              <span> Potential boundary overlap observed in proximity to ${activeSite.name}. Official boundary status: <em>LEGAL BOUNDARY UNVERIFIED &mdash; Requires State Gazette &amp; Revenue Field Demarcation</em>. Evidentiary Hash: <code style="color:#38bdf8;">SHA256:7f83b1657ff1fc53...</code></span>
            </div>
          </div>
          <span style="background:rgba(234,179,8,0.2);color:#fde047;border:1px solid rgba(234,179,8,0.5);padding:2px 7px;border-radius:3px;font-weight:700;font-size:8.5px;white-space:nowrap;">REQUIRES OFFICIAL VERIFICATION</span>
        </div>"""

if old_callout in code:
    code = code.replace(old_callout, new_callout)
    print("Replaced callout banner")
else:
    print("WARNING: old_callout not matched exactly")

# 4. Replace 3D Buffer Analysis text
code = code.replace('✗ (ILLEGAL FTL VIOLATION)', '⚠️ (POTENTIAL BUFFER OVERLAP)')
code = code.replace('<div><span style="color:#ef4444;font-weight:700;">✗ ILLEGAL FTL ZONE:</span> Protected Water-Spread &bull; Demolition Mandated</div>',
                    '<div><span style="color:#fde047;font-weight:700;">⚠️ POTENTIAL BUFFER OVERLAP:</span> Protected Water-Spread &bull; Requires Field Demarcation</div>')
code = code.replace('■ RED SHIELD: PROTECTED 30m FTL ZONE (NO DEVELOPMENT)',
                    '■ AMBER/RED SHIELD: POTENTIAL PROXIMAL WATERBODY BUFFER (PENDING SURVEY)')

# 5. Replace popup text
code = code.replace('🚨 STATUTORY FTL VIOLATION FLAGGED', '⚠️ POTENTIAL SPATIAL OVERLAP IDENTIFIED')
code = code.replace('<div><strong>Action:</strong> Section 23 Demolition Mandated</div>',
                    '<div><strong>Action:</strong> Field Ground-Truthing &amp; Joint Inspection Recommended</div>')
code = code.replace('<div><strong>Violation:</strong> Within 30m Statutory FTL Buffer</div>',
                    '<div><strong>Observation:</strong> Spatial proximity overlap with waterbody perimeter</div>')

# 6. Replace dossier / print disclaimers & BSA 2023 update
code = code.replace('CRITICAL BUFFER VIOLATION', 'POTENTIAL SPATIAL OVERLAP (SCREENING LEVEL)')
code = code.replace('Mandated Statutory Action Plan for Enforcement Officers', 'Recommended Protocol for Official Field Ground-Truthing')
code = code.replace('Serve Statutory Section 23/24 Show-Cause Notices', 'Conduct Joint Physical Survey with Revenue Inspector & Cadastral Surveyor')
code = code.replace('3 Unauthorized Permanent / Semi-Permanent Structures', 'Potential Spatial Overlaps Identified (Requires Ground Verification)')
code = code.replace('Evidentiary Grade (Court Admissible)', 'Technical Screening Report (Subject to BSA 2023 §63 Certification)')
code = code.replace('EVIDENTIARY GRADE (COURT ADMISSIBLE)', 'TECHNICAL SCREENING REPORT (SUBJECT TO BSA 2023 §63)')

# 7. Add BSA 2023 §63 legal notice in dossier
bsa_notice_html = """  <div style="background:#f8fafc;border:1px solid #cbd5e1;border-radius:6px;padding:10px 14px;margin-top:16px;font-size:11px;color:#475569;line-height:1.4;">
    <strong>LEGAL &amp; SCIENTIFIC DISCLAIMER (Bharatiya Sakshya Adhiniyam, 2023 &bull; Section 63):</strong><br>
    This audit dossier is an automated preliminary spatial screening analysis derived from public Earth observation satellite imagery (Sentinel-2, Sentinel-1) and OpenStreetMap building/road vectors. It does NOT constitute a legal decree, conclusive cadastral determination, or proof of illegal encroachment. Statutory lake Full Tank Level (FTL) boundaries and buffer perimeters vary by state legislation (e.g. Telangana WALTA Act 2002, Karnataka KLCDA Act, state-specific irrigation gazettes). Official action requires joint field demarcation, verification of village revenue cadastral sheets (naksha / pahani), and formal electronic evidence certification under BSA 2023 §63.
  </div>"""

if '</body>' in code and bsa_notice_html not in code:
    # insert before the first </body> in exportSiteAuditDossier
    code = code.replace('</body>\n</html>`;', bsa_notice_html + '\n</body>\n</html>`;', 1)
    print("Inserted BSA 2023 disclaimer in HTML dossier")

# Write to root Assets
with open(fpath, 'w', encoding='utf-8') as f:
    f.write(code)
print("Updated root Assets/vendor/bhu_loka_urban_studio.js")

# Write to public Assets
pub_path = os.path.join(repo, 'public', 'Assets', 'vendor', 'bhu_loka_urban_studio.js')
with open(pub_path, 'w', encoding='utf-8') as f:
    f.write(code)
print("Updated public/Assets/vendor/bhu_loka_urban_studio.js")
