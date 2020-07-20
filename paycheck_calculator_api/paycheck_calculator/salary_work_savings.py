from datetime import date
from pprint import pprint

from marshmallow import Schema, fields


class SalaryWorkSavingsInfo(Schema):
    marialStatus = fields.Integer()
    zipCode = fields.Integer()
    payFrequency = fields.Integer()
    federalAllowance: fields.Integer()
    stateAllowance: fields.Integer()
    localAllowance: fields.Integer()
    salaryType: fields.Integer()
    salaryInput: fields.Integer()
    currentSavingAmount: fields.Integer()
    apyAnnually: fields.Integer()
    paycheckPercentSaved: fields.Integer()
    yearSaved: fields.Integer()
