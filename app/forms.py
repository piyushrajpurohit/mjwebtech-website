"""
app/forms.py — Flask-WTF form classes with full validation.
All fields use CSRF protection, length limits, and type validators.
"""

import re
from flask_wtf         import FlaskForm
from flask_wtf.file    import FileField, FileAllowed, FileRequired
from wtforms           import (
    StringField, TextAreaField, SelectField,
    TelField, EmailField, SubmitField, BooleanField,
)
from wtforms.validators import (
    DataRequired, Email, Length, Optional, Regexp, ValidationError,
)

def _strip(v):
    return v.strip() if v else v

PHONE_RE = re.compile(r'^[\d\s\+\-\(\)]{7,20}$')

SUBJECT_CHOICES = [
    ('',                            '— Select a topic —'),
    ('Free Consultation',           'Free Consultation'),
    ('Talk to an Expert',           'Talk to an Expert'),
    ('Newsletter Subscription',     'Newsletter Subscription'),
    ('Software Development',        'Software Development Enquiry'),
    ('Cloud Services',              'Cloud Services'),
    ('IT Consulting',               'IT Consulting'),
    ('Technical Support',           'Technical Support'),
    ('Digital Marketing',           'Digital Marketing'),
    ('Manpower / Staffing',         'Manpower / Staffing'),
    ('Partnership',                 'Partnership / Collaboration'),
    ('General Enquiry',             'General Enquiry'),
]

class ContactForm(FlaskForm):
    name    = StringField('Full Name',
        filters=[_strip],
        validators=[DataRequired('Name is required.'), Length(2, 120)])
    email   = EmailField('Email Address',
        filters=[_strip],
        validators=[DataRequired('Email is required.'), Email('Enter a valid email.'), Length(max=254)])
    company = StringField('Company',
        filters=[_strip],
        validators=[Optional(), Length(max=200)])
    phone   = TelField('Phone Number',
        filters=[_strip],
        validators=[Optional(), Regexp(PHONE_RE, message='Enter a valid phone number.')])
    subject = SelectField('Subject',
        choices=SUBJECT_CHOICES,
        validators=[DataRequired('Please select a subject.')])
    message = TextAreaField('Message',
        filters=[_strip],
        validators=[DataRequired('Message is required.'), Length(min=10, max=3000, message='Message must be 10–3000 characters.')])
    privacy = BooleanField('I agree to the privacy policy.',
        validators=[DataRequired('You must accept the privacy policy.')])
    submit  = SubmitField('Send Message')


EXPERIENCE_CHOICES = [
    ('',          '— Select Experience —'),
    ('fresher',   'Fresher (0 Years)'),
    ('0-1',       '0 – 1 Year'),
    ('1-3',       '1 – 3 Years'),
    ('3-5',       '3 – 5 Years'),
    ('5-10',      '5 – 10 Years'),
    ('10+',       '10+ Years'),
]

POSITION_CHOICES = [
    ('',                        '— Select Position —'),
    ('Full Stack Developer',    'Full Stack Developer'),
    ('Frontend Developer',      ' Developer (React / Vue)'),
    ('Backend Developer',       'Backend Developer (Python / Node)'),
    ('Mobile App Developer',    'Mobile App Developer'),
    ('UI/UX Designer',          'UI/UX Designer'),
    ('Cloud & DevOps Engineer', 'Cloud & DevOps Engineer'),
    ('IT Support Engineer',     'IT Support Engineer'),
    ('System Administrator',    'System Administrator'),
    ('Data Analyst',            'Data Analyst / BI'),
    ('Digital Marketing Executive', 'Digital Marketing Executive'),
    ('Business Development Executive', 'Business Development Executive'),
    ('HR & Administration',     'HR & Administration'),
    ('Open Application',        'Open Application (any role)'),
]

class CareerForm(FlaskForm):
    full_name    = StringField('Full Name',
        filters=[_strip],
        validators=[DataRequired('Full name is required.'), Length(2, 120)])
    email        = EmailField('Email Address',
        filters=[_strip],
        validators=[DataRequired('Email is required.'), Email('Enter a valid email.'), Length(max=254)])
    phone        = TelField('Phone Number',
        filters=[_strip],
        validators=[DataRequired('Phone number is required.'), Regexp(PHONE_RE, message='Enter a valid phone number.')])
    position     = SelectField('Position Applied For',
        choices=POSITION_CHOICES,
        validators=[DataRequired('Please select a position.')])
    experience   = SelectField('Years of Experience',
        choices=EXPERIENCE_CHOICES,
        validators=[Optional()])
    cover_letter = TextAreaField('Cover Letter',
        filters=[_strip],
        validators=[Optional(), Length(max=3000)])
    resume       = FileField('Resume (PDF / DOC / DOCX — max 5 MB)',
        validators=[
            FileRequired('Please upload your resume.'),
            FileAllowed(['pdf','doc','docx'], 'Only PDF, DOC, or DOCX files are allowed.'),
        ])
    submit = SubmitField('Submit Application')
