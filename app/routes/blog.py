"""
routes/blog.py — Blog / Insights page with dummy article data.
Can be replaced with a CMS / DB-driven approach later.
"""

from flask import Blueprint, render_template, abort

blog_bp = Blueprint("blog", __name__)

ARTICLES = [
    {
        "slug":     "cloud-migration-guide-2024",
        "title":    "Complete Guide to Cloud Migration for Indian SMEs",
        "category": "Cloud & Infrastructure",
        "date":     "15 Mar 2026",
        "author":   "Rupam Shree",
        "icon":     "bi-cloud-arrow-up",
        "color":    "primary",
        "summary":  "A practical, step-by-step guide for small and medium enterprises in India planning to migrate workloads to AWS, Azure, or GCP — covering cost analysis, security, and compliance.",
        "read_time": "8 min read",
        "body": """
<p>Cloud migration is no longer optional for businesses that want to remain competitive. For Indian SMEs, the cloud offers scalability, reduced capital expenditure, and access to enterprise-grade tools at fraction of the traditional cost.</p>
<h4>Why Migrate Now?</h4>
<p>With Indian data-centre costs rising and digital-first competitors emerging daily, delaying migration carries real business risk. AWS Mumbai, Azure India Central, and GCP Mumbai regions now offer low-latency options compliant with India's data-localisation guidelines.</p>
<h4>Step 1 — Assess Your Current Workloads</h4>
<p>Audit every application: categorise as Lift-and-Shift, Re-platform, or Re-architect. Most SMEs find that 60–70 % of workloads can be lifted and shifted in weeks with minimal downtime.</p>
<h4>Step 2 — Calculate TCO</h4>
<p>Use AWS Pricing Calculator or Azure TCO Calculator. Include egress costs — often underestimated by 30–40 %.</p>
<h4>Step 3 — Security & Compliance First</h4>
<p>Configure VPCs, IAM roles, and encryption at rest before the first workload moves. For RBI-regulated entities, ensure data residency in India.</p>
""",
    },
    {
        "slug":     "seo-local-business-india",
        "title":    "SEO Strategies That Actually Work for Indian Businesses",
        "category": "Digital Marketing",
        "date":     "02 Feb 2026",
        "author":   "Ranu Singh",
        "icon":     "bi-search",
        "color":    "success",
        "summary":  "Discover proven local SEO tactics tailored for Indian markets — from Google Business Profile optimisation to regional-language content strategies that drive qualified foot traffic.",
        "read_time": "6 min read",
        "body": """
<p>With over 700 million internet users in India, local SEO is the highest-ROI digital channel for businesses targeting specific geographies — whether Patna, Pune, or Patiala.</p>
<h4>Optimise Your Google Business Profile</h4>
<p>Claim and verify your GBP listing. Add photos, business hours, and respond to every review within 24 hours. Businesses with complete GBP listings are 70 % more likely to attract location visits.</p>
<h4>Regional Language Content</h4>
<p>Create a Hindi or regional-language version of key landing pages. Google now indexes Devanagari and other Indic scripts with equal priority to English.</p>
<h4>Hyper-Local Backlinks</h4>
<p>Get listed on Justdial, Sulekha, IndiaMart, and local chamber-of-commerce directories. These carry significant domain authority for India-specific SERPs.</p>
""",
    },
    {
        "slug":     "erp-implementation-pitfalls",
        "title":    "ERP Implementation Pitfalls & How We Help to Avoid Them",
        "category": "IT Consulting",
        "date":     "18 Jan 2026",
        "author":   "Nikhil Sharma",
        "icon":     "bi-exclamation-triangle",
        "color":    "warning",
        "summary":  "ERP projects have a notoriously high failure rate. Learn the five most common pitfalls from our consulting experience and the strategies we deploy to keep implementations on time and on budget.",
        "read_time": "7 min read",
        "body": """
<p>According to Panorama Consulting, 50–75 % of ERP projects experience significant overruns. In our experience across Bihar and eastern India, we have identified five recurring failure patterns.</p>
<h4>Pitfall 1 — Skipping the Process Audit</h4>
<p>Organisations rush to configure the ERP before documenting current workflows. The ERP then automates broken processes. Solution: spend at least 20 % of the project timeline on as-is process mapping.</p>
<h4>Pitfall 2 — Insufficient Change Management</h4>
<p>End-users resist change. Without executive sponsorship and role-specific training, adoption rates fall below 40 %. We embed a dedicated change-management workstream in every engagement.</p>
<h4>Pitfall 3 — Poor Data Quality</h4>
<p>Migrating dirty data from legacy systems poisons the new ERP from day one. Data cleansing and de-duplication must begin three months before go-live.</p>
""",
    },
    {
        "slug":     "cybersecurity-smb-checklist",
        "title":    "Cybersecurity Checklist for Small IT Teams in India",
        "category": "Cybersecurity",
        "date":     "05 Jan 2026",
        "author":   "Piyush Rajpurohit",
        "icon":     "bi-shield-check",
        "color":    "danger",
        "summary":  "A practical 20-point cybersecurity checklist that any SME with a small IT team can implement today — covering passwords, patching, backups, and incident response.",
        "read_time": "5 min read",
        "body": """
<p>Cyber attacks on Indian SMEs rose by 67 % in 2023 according to CERT-In. Most breaches exploit well-known, easily preventable vulnerabilities. This checklist addresses the top 20.</p>
<h4>Identity & Access</h4>
<ul>
<li>Enforce MFA on all admin accounts.</li>
<li>Audit user privileges quarterly — principle of least privilege.</li>
<li>Disable default credentials on all network devices.</li>
</ul>
<h4>Patching & Updates</h4>
<ul>
<li>Automate OS patching — critical patches within 72 hours of release.</li>
<li>Maintain a software inventory; remove end-of-life applications.</li>
</ul>
<h4>Backup & Recovery</h4>
<ul>
<li>Follow the 3-2-1 rule: 3 copies, 2 media types, 1 offsite.</li>
<li>Test restoration monthly — backups are useless if unrestorable.</li>
</ul>
""",
    },
    {
        "slug":     "python-flask-deployment-godaddy",
        "title":    "Deploying Python Flask Apps on GoDaddy Shared Hosting — A Complete Guide",
        "category": "Development",
        "date":     "22 Dec 2025",
        "author":   "Loni Priya",
        "icon":     "bi-rocket-takeoff",
        "color":    "info",
        "summary":  "A detailed, step-by-step tutorial for deploying a Flask web application on GoDaddy cPanel shared hosting using Passenger WSGI — including virtual environments and static files.",
        "read_time": "10 min read",
        "body": """
<p>GoDaddy shared hosting supports Python via Apache Passenger WSGI. While not as flexible as a VPS, it is a cost-effective choice for SME corporate websites. Here is the complete deployment workflow.</p>
<h4>Prerequisites</h4>
<ul>
<li>GoDaddy Linux shared hosting with cPanel access.</li>
<li>Python 3.9+ available in cPanel → Setup Python App.</li>
<li>SSH access enabled (Security → SSH Access in cPanel).</li>
</ul>
<h4>Step 1 — Create Python App in cPanel</h4>
<p>Navigate to Software → Setup Python App. Select Python 3.9, set application root to your domain folder, and note the virtual environment path.</p>
<h4>Step 2 — Upload Your Code</h4>
    <p>Use File Manager or SFTP to upload your project to your Python-capable host (Passenger WSGI or another WSGI server). Ensure the appropriate startup file and virtualenv are configured by your host.</p>
""",
    },
    {
        "slug":     "manpower-it-hiring-bihar",
        "title":    "Building Your IT Team in Bihar: Hiring Trends & Talent Landscape 2026",
        "category": "HR & Staffing",
        "date":     "10 Dec 2025",
        "author":   "Minakshi Shandilya",
        "icon":     "bi-people",
        "color":    "secondary",
        "summary":  "Bihar's IT talent pool is growing rapidly. This article explores hiring trends, salary benchmarks, and strategies for building high-performing IT teams in Tier-2 cities.",
        "read_time": "6 min read",
        "body": """
<p>Bihar's IT sector is experiencing a renaissance. With BIT Mesra, NIT Patna, and dozens of engineering colleges producing quality graduates, the talent pool is deeper than ever — and significantly more affordable than metros.</p>
<h4>Salary Benchmarks (2026)</h4>
<ul>
<li>Junior Developer (0–2 yrs): ₹2.4L – ₹4.8L per annum</li>
<li>Mid-level Developer (2–5 yrs): ₹5L – ₹10L per annum</li>
<li>Senior / Lead (5+ yrs): ₹10L – ₹18L per annum</li>
<li>Digital Marketing Executive: ₹2.4L – ₹5L per annum</li>
</ul>
<h4>Hiring Through MJ WebTech</h4>
<p>Our manpower division maintains a pre-vetted talent database of 500+ IT professionals across Bihar. We reduce time-to-hire to under 10 days for most roles.</p>
""",
    },
]


@blog_bp.route("/blog")
def blog():
    return render_template("blog.html", articles=ARTICLES)


@blog_bp.route("/blog/<slug>")
def article(slug):
    post = next((a for a in ARTICLES if a["slug"] == slug), None)
    if not post:
        abort(404)
    related = [a for a in ARTICLES if a["slug"] != slug][:3]
    return render_template("article.html", post=post, related=related)
