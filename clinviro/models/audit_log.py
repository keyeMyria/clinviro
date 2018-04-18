# ClinViro
# Copyright (C) 2018 Stanford HIVDB team.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pytz
from datetime import datetime
from sqlalchemy_utils.types.choice import ChoiceType
from flask import current_app as app
from flask_login import current_user

db = app.db

OPERATION_TYPE_CHOICES = [
    ('CREATE', 'CREATE'),
    ('MODIFY', 'MODIFY'),
    ('DELETE', 'DELETE'),
]

TARGET_CHOICES = [
    ('PATIENT', 'PATIENT'),
    ('PATIENT_VISIT', 'PATIENT_VISIT'),
    ('PATIENT_SAMPLE', 'PATIENT_SAMPLE'),
    ('PROFICIENCY_SAMPLE', 'PROFICIENCY_SAMPLE'),
    ('POSITIVE_CONTROL', 'POSITIVE_CONTROL'),
    ('REPORT', 'REPORT'),
    ('USER', 'USER'),
    ('CLINIC', 'CLINIC'),
    ('PHYSICIAN', 'PHYSICIAN'),
]


class AuditLog(db.Model):

    __tablename__ = 'tbl_audit_logs'

    id = db.Column(
        db.Integer, primary_key=True, nullable=False,
        doc='audit log UID')
    user_id = db.Column(
        db.Integer, db.ForeignKey('tbl_users.id'),
        index=True, nullable=False)
    operation_type = db.Column(
        ChoiceType(OPERATION_TYPE_CHOICES, db.Unicode(8)),
        nullable=False, doc='operation type')
    target = db.Column(
        ChoiceType(TARGET_CHOICES, db.Unicode(32)),
        nullable=False, doc='operation target')
    payload = db.Column(
        db.JSON(), nullable=False, doc='structured data of this log')
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, index=True,
        doc='date and time this log was created')

    user = db.relationship(
        'User', back_populates='audit_logs',
        doc='user who performed this operation')

    def __init__(self, user, operation_type, target, payload):
        self.user = user
        self.operation_type = operation_type
        self.target = target
        self.payload = payload
        self.created_at = datetime.now(pytz.utc)

    @classmethod
    def for_current_user(cls, operation_type, target, payload):
        return cls(current_user, operation_type, target, payload)
