from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, session, current_app, send_from_directory, abort
from sqlalchemy import or_
from io import StringIO
import csv
import os
from app import db
from app.auth_utils import admin_required
from app.models import Contact, ContactActionLog, JobApplication, User

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

STATUS_CHOICES = ["New", "In Progress", "Resolved", "Spam"]
APPLICATION_STATUS_CHOICES = ["pending", "reviewed", "shortlisted", "rejected"]


@admin_bp.route("/")
@admin_required
def dashboard():
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)
    week_start = today_start - timedelta(days=7)
    month_start = datetime(now.year, now.month, 1)

    summary = {
        "new_contacts": Contact.query.filter_by(status="New").count(),
        "career_applications": JobApplication.query.count(),
        "registered_users": User.query.count(),
        "total_inquiries": Contact.query.count(),
    }

    analytics = {
        "contacts": {
            "today": Contact.query.filter(Contact.created_at >= today_start).count(),
            "week": Contact.query.filter(Contact.created_at >= week_start).count(),
            "month": Contact.query.filter(Contact.created_at >= month_start).count(),
        },
        "applications": {
            "today": JobApplication.query.filter(JobApplication.created_at >= today_start).count(),
            "week": JobApplication.query.filter(JobApplication.created_at >= week_start).count(),
            "month": JobApplication.query.filter(JobApplication.created_at >= month_start).count(),
        },
    }

    recent_contacts = Contact.query.order_by(Contact.created_at.desc()).limit(5).all()
    recent_applications = JobApplication.query.order_by(JobApplication.created_at.desc()).limit(5).all()

    return render_template(
        "admin/dashboard.html",
        summary=summary,
        analytics=analytics,
        recent_contacts=recent_contacts,
        recent_applications=recent_applications,
        status_choices=STATUS_CHOICES,
    )


@admin_bp.route("/contacts")
@admin_required
def contacts_list():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "", type=str).strip()
    status = request.args.get("status", "", type=str).strip()

    query = Contact.query.order_by(Contact.created_at.desc())

    if search:
        query = query.filter(
            or_(
                Contact.name.ilike(f"%{search}%"),
                Contact.email.ilike(f"%{search}%"),
                Contact.company.ilike(f"%{search}%"),
                Contact.subject.ilike(f"%{search}%"),
            )
        )

    if status:
        query = query.filter(Contact.status == status)

    pagination = query.paginate(page=page, per_page=10, error_out=False)
    contacts = pagination.items

    return render_template(
        "admin/contacts_list.html",
        contacts=contacts,
        pagination=pagination,
        search=search,
        status=status,
        status_choices=STATUS_CHOICES,
    )


@admin_bp.route("/applications")
@admin_required
def applications_list():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "", type=str).strip()
    status = request.args.get("status", "", type=str).strip()
    position = request.args.get("position", "", type=str).strip()

    query = JobApplication.query.order_by(JobApplication.created_at.desc())

    if search:
        query = query.filter(
            or_(
                JobApplication.full_name.ilike(f"%{search}%"),
                JobApplication.email.ilike(f"%{search}%"),
                JobApplication.position.ilike(f"%{search}%"),
            )
        )

    if status:
        query = query.filter(JobApplication.status == status)

    if position:
        query = query.filter(JobApplication.position.ilike(f"%{position}%"))

    pagination = query.paginate(page=page, per_page=10, error_out=False)
    applications = pagination.items

    return render_template(
        "admin/applications_list.html",
        applications=applications,
        pagination=pagination,
        search=search,
        status=status,
        position=position,
        status_choices=APPLICATION_STATUS_CHOICES,
    )


@admin_bp.route("/applications/<int:application_id>")
@admin_required
def application_detail(application_id):
    application = JobApplication.query.get_or_404(application_id)
    return render_template(
        "admin/application_detail.html",
        application=application,
        status_choices=APPLICATION_STATUS_CHOICES,
    )


@admin_bp.route("/applications/<int:application_id>/update", methods=["POST"])
@admin_required
def update_application_status(application_id):
    application = JobApplication.query.get_or_404(application_id)
    status = request.form.get("status", "pending")
    if status not in APPLICATION_STATUS_CHOICES:
        flash("Invalid status selected.", "danger")
        return redirect(url_for("admin.application_detail", application_id=application.id))

    application.status = status
    db.session.commit()
    flash("Application status updated.", "success")
    return redirect(url_for("admin.application_detail", application_id=application.id))


@admin_bp.route("/applications/<int:application_id>/resume")
@admin_required
def download_application_resume(application_id):
    application = JobApplication.query.get_or_404(application_id)
    if not application.resume_filename:
        abort(404)

    upload_folder = current_app.config.get("UPLOAD_FOLDER")
    if not upload_folder:
        abort(404)

    return send_from_directory(
        upload_folder,
        application.resume_filename,
        as_attachment=True,
        download_name=application.resume_filename,
        mimetype="application/octet-stream",
    )


def _log_contact_action(contact: Contact, action: str, performed_by: str, performed_by_id: int | None = None, notes: str | None = None):
    log_entry = ContactActionLog(
        contact_id=contact.id,
        action=action,
        performed_by=performed_by,
        performed_by_id=performed_by_id,
        notes=notes,
    )
    db.session.add(log_entry)


@admin_bp.route("/contacts/bulk", methods=["POST"])
@admin_required
def bulk_contacts_action():
    selected_ids = [int(contact_id) for contact_id in request.form.getlist("selected_contacts") if contact_id.isdigit()]
    action = request.form.get("bulk_action", "").strip()
    return_search = request.form.get("return_search", "")
    return_status = request.form.get("return_status", "")

    if not selected_ids:
        flash("Please select at least one contact to perform a bulk action.", "warning")
        return redirect(url_for("admin.contacts_list", search=return_search, status=return_status))

    if action not in {"mark_new", "mark_in_progress", "mark_resolved", "mark_spam", "delete"}:
        flash("Please choose a valid bulk action.", "danger")
        return redirect(url_for("admin.contacts_list", search=return_search, status=return_status))

    contacts = Contact.query.filter(Contact.id.in_(selected_ids)).all()
    if not contacts:
        flash("No matching contacts were found for the selected items.", "danger")
        return redirect(url_for("admin.contacts_list", search=return_search, status=return_status))

    admin_user = User.query.get(session.get("user_id"))
    performed_by = admin_user.email if admin_user else "Unknown"
    performed_by_id = admin_user.id if admin_user else None

    status_map = {
        "mark_new": "New",
        "mark_in_progress": "In Progress",
        "mark_resolved": "Resolved",
        "mark_spam": "Spam",
    }

    if action == "delete":
        for contact in contacts:
            _log_contact_action(
                contact,
                action="Deleted",
                performed_by=performed_by,
                performed_by_id=performed_by_id,
                notes="Bulk delete performed by admin.",
            )
            db.session.delete(contact)
        flash(f"Deleted {len(contacts)} contact(s).", "success")
    else:
        for contact in contacts:
            previous_status = contact.status
            contact.status = status_map[action]
            contact.is_read = True
            _log_contact_action(
                contact,
                action=f"Marked {status_map[action]}",
                performed_by=performed_by,
                performed_by_id=performed_by_id,
                notes=f"Status changed from {previous_status} to {status_map[action]}.",
            )
        flash(f"Updated status for {len(contacts)} contact(s).", "success")

    db.session.commit()
    return redirect(url_for("admin.contacts_list", search=return_search, status=return_status))


@admin_bp.route("/contacts/<int:contact_id>")
@admin_required
def contact_detail(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    admin_user = User.query.get(session.get("user_id"))
    performed_by = admin_user.email if admin_user else "Unknown"

    _log_contact_action(
        contact,
        action="Viewed",
        performed_by=performed_by,
        notes="Admin viewed the contact detail page.",
    )
    db.session.commit()

    contact_logs = ContactActionLog.query.filter_by(contact_id=contact.id).order_by(ContactActionLog.created_at.desc()).all()
    return render_template(
        "admin/contact_detail.html",
        contact=contact,
        status_choices=STATUS_CHOICES,
        contact_logs=contact_logs,
    )


@admin_bp.route("/contacts/<int:contact_id>/update", methods=["POST"])
@admin_required
def update_contact_status(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    status = request.form.get("status", "New")
    if status not in STATUS_CHOICES:
        flash("Invalid status selected.", "danger")
        return redirect(url_for("admin.contact_detail", contact_id=contact.id))

    contact.status = status
    contact.is_read = True
    db.session.commit()
    flash("Contact status updated.", "success")
    return redirect(url_for("admin.contact_detail", contact_id=contact.id))


@admin_bp.route("/contacts/<int:contact_id>/delete", methods=["POST"])
@admin_required
def delete_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    db.session.delete(contact)
    db.session.commit()
    flash("Contact inquiry deleted.", "success")
    return redirect(url_for("admin.contacts_list"))


@admin_bp.route("/contacts/export")
@admin_required
def export_contacts():
    search = request.args.get("search", "", type=str).strip()
    status = request.args.get("status", "", type=str).strip()

    query = Contact.query.order_by(Contact.created_at.desc())
    if search:
        query = query.filter(
            or_(
                Contact.name.ilike(f"%{search}%"),
                Contact.email.ilike(f"%{search}%"),
                Contact.company.ilike(f"%{search}%"),
                Contact.subject.ilike(f"%{search}%"),
            )
        )
    if status:
        query = query.filter(Contact.status == status)

    contacts = query.all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "Email", "Company", "Phone", "Subject", "Status", "Submitted At", "Message"])
    for c in contacts:
        writer.writerow([
            c.id,
            c.name,
            c.email,
            c.company or "",
            c.phone or "",
            c.subject,
            c.status,
            c.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            c.message.replace("\n", " "),
        ])

    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers.set("Content-Disposition", "attachment", filename="mjwebtech_contacts.csv")
    return response
