# ClinViro
# Copyright (C) 2017 Stanford HIVDB team.
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

from datetime import datetime

import pytz
import graphene
from flask_login import login_required
from flask import current_app as app

from ..utils import get_numeric_id
from ..proficiency_sample import ProficiencySample
from .proficiency_sample_input import (ProficiencySampleInput,
                                       sample_input_to_args)

db = app.db
models = app.models


def create_proficiency_sample(input_):
    profsample = models.ProficiencySample(sample_input_to_args(input_))

    # generate report
    profsample.set_sequence(input_['sequence'], input_.get('filename'))
    return profsample


class UpdateProficiencySample(graphene.ClientIDMutation):

    class Input(ProficiencySampleInput):
        id = graphene.ID(required=True)

    updated_proficiency_sample = graphene.Field(ProficiencySample)

    @staticmethod
    @login_required
    def mutate_and_get_payload(root, info, **input_):
        profsample = (models.ProficiencySample
                      .query.get(get_numeric_id(input_['id'])))
        payload = {
            'proficiency_sample_id': profsample.id,
            'changed_fields': []
        }
        sample_args = sample_input_to_args(input_)
        for key, val in sample_args.items():
            old_value = getattr(profsample, key)
            if old_value != val:
                payload['changed_fields'].append({
                    'field': key,
                    'old_value': old_value,
                    'new_value': val
                })
                setattr(profsample, key, val)

        old_naseq = None
        old_filename = None
        naseq = input_.get('sequence')
        filename = input_.get('filename')
        if profsample.sequence:
            old_naseq = profsample.sequence.naseq
            old_filename = profsample.sequence.filename
        if old_naseq != naseq:
            payload['changed_fields'].append({
                'field': 'sequence_naseq',
                'old_value': old_naseq,
                'new_value': naseq
            })
        if old_filename != filename:
            payload['changed_fields'].append({
                'field': 'sequence_filename',
                'old_value': old_filename,
                'new_value': filename
            })
        # regenerate report
        profsample.set_sequence(naseq, filename)
        profsample.generate_reports(datetime.now(pytz.utc))
        log = models.AuditLog.for_current_user(
            'MODIFY', 'PROFICIENCY_SAMPLE', payload
        )
        db.session.add(log)
        db.session.commit()

        models.blastdb.makeblastdb_incr()
        return UpdateProficiencySample(updated_proficiency_sample=profsample)
