"""
routes/main.py — Public pages: Home, About, Services.
"""

from flask import Blueprint, render_template
from app.auth_utils import login_required

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    testimonials = [
        {"name": "Rajesh Kumar",    "company": "Infobiz Solutions",    "text": "MJ WebTech delivered our ERP system 2 weeks ahead of schedule. Exceptional quality and communication throughout.", "rating": 5},
        {"name": "Priya Sharma",    "company": "FinServe India Ltd.",  "text": "Their cloud migration saved us 40% on infrastructure costs. Highly professional and knowledgeable team.", "rating": 5},
        {"name": "Amit Tiwari",     "company": "RetailEdge Pvt. Ltd.", "text": "Outstanding digital marketing results — 3x increase in organic leads within 4 months.", "rating": 5},
        {"name": "Sunita Verma",    "company": "HealthFirst Clinics",  "text": "Seamless implementation of our patient management system. Support team is always responsive.", "rating": 5},
        {"name": "Vikram Pandey",   "company": "LogiTrack Systems",    "text": "Best IT consulting partner we have worked with. They understood our needs perfectly.", "rating": 5},
    ]
    return render_template("index.html", testimonials=testimonials)


@main_bp.route("/about")
def about():
    team = [
        {"name": "Mahima Kumari", "role": "Founder & CEO", "photo": "images/leadership/mahima-kumari.png"},
        {"name": "Geeta Devi",    "role": "Founder & CEO", "photo": "images/leadership/geeta-devi.png"},
    ]
    return render_template("about.html", team=team)


@main_bp.route("/services")
def services():
    services_list = [
        {
            "title":   "Software Development",
            "icon":    "bi-code-slash",
            "color":   "primary",
            "short":   "Custom web, mobile & enterprise apps built to scale.",
            "details": [
                "Custom web application development (Django, Flask, Node.js, React)",
                "Mobile app development (Android, iOS, React Native)",
                "Enterprise software & ERP solutions",
                "API design, integration & microservices architecture",
                "QA testing, code review & DevOps pipelines",
            ],
        },
        {
            "title":   "Installation & Implementation",
            "icon":    "bi-boxes",
            "color":   "success",
            "short":   "End-to-end setup of software, hardware & networks.",
            "details": [
                "Server & network infrastructure setup",
                "ERP & CRM system implementation (SAP, Zoho, Tally)",
                "Hardware installation & configuration",
                "OS deployment, Active Directory & GPO management",
                "On-site & remote implementation support",
            ],
        },
        {
            "title":   "Maintenance & Customization",
            "icon":    "bi-tools",
            "color":   "warning",
            "short":   "Keep your systems optimised and evolving with your business.",
            "details": [
                "Annual maintenance contracts (AMC)",
                "Bug fixing & performance tuning",
                "Feature additions & UI/UX upgrades",
                "Database optimisation & backup management",
                "24/7 monitoring & alert systems",
            ],
        },
        {
            "title":   "Technical Support",
            "icon":    "bi-headset",
            "color":   "info",
            "short":   "Reliable helpdesk & on-site support when you need it.",
            "details": [
                "L1 / L2 / L3 helpdesk support",
                "Remote desktop assistance",
                "On-site technician deployment",
                "SLA-driven incident management",
                "User training & documentation",
            ],
        },
        {
            "title":   "IT Consulting & System Integration",
            "icon":    "bi-diagram-3",
            "color":   "danger",
            "short":   "Strategic advisory to align technology with your goals.",
            "details": [
                "IT infrastructure audits & roadmaps",
                "Digital transformation consulting",
                "Third-party system integration (REST, SOAP, EDI)",
                "Cybersecurity assessment & policy drafting",
                "Vendor evaluation & procurement support",
            ],
        },
        {
            "title":   "Data Processing & Cloud Services",
            "icon":    "bi-cloud-upload",
            "color":   "secondary",
            "short":   "Harness the power of cloud and data intelligence.",
            "details": [
                "Cloud migration (AWS, Azure, GCP)",
                "Data warehousing & ETL pipelines",
                "Business intelligence & analytics dashboards",
                "Backup, disaster recovery & business continuity",
                "Cloud cost optimisation & governance",
            ],
        },
        {
            "title":   "Social Media & Digital Marketing",
            "icon":    "bi-graph-up-arrow",
            "color":   "primary",
            "short":   "Grow your brand across every digital channel.",
            "details": [
                "SEO / SEM & Google Ads management",
                "Social media marketing (LinkedIn, Instagram, Facebook)",
                "Content creation, blogging & email campaigns",
                "Brand identity design & video production",
                "Performance analytics & monthly reporting",
            ],
        },
        {
            "title":   "Manpower Supply",
            "icon":    "bi-people",
            "color":   "success",
            "short":   "Skilled & unskilled IT, admin & business talent on demand.",
            "details": [
                "IT professionals — developers, QA engineers, SysAdmins",
                "Administrative & data-entry staff",
                "Technical support & field engineers",
                "Business process outsourcing (BPO) teams",
                "Contract, permanent & project-based hiring",
            ],
        },
    ]
    return render_template("services.html", services=services_list)


@main_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")
