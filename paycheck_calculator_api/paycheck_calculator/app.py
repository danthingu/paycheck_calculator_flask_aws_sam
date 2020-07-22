import json
import sys
from types import TracebackType
from typing import Type, Union
from flask_cors import CORS

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from flask_lambda import FlaskLambda
from flask import request
import csv
import datetime


app = FlaskLambda(__name__)
CORS(app)
ddb = boto3.resource('dynamodb')
state_tax_table = ddb.Table('state_tax')
federal_tax_table = ddb.Table('federal_tax')


@app.route('/')
def index():
    return json_response({"message": "1234Hello, world!"})

def compound_interest_calculator(original_principal, annual_interest, compound, total_years, monthly_contribution):
    # original_principal = int(input('Enter the starting principal: '))
    # 
    # # Input the annual interest rate.
    # 
    # annual_interest = float(input('Enter the annual interest rate (%): '))
    annual_interest = float(float(annual_interest) / 100.00)
    # 
    # # Input times per year the interest is compounded.
    # 
    # compound = int(input('How many times per year is the interest compounded? '))
    # 
    # # Input number of years account will earn interest.
    # 
    # total_years = int(input('For how many years will the account earn interest? '))

    # Calculate ending principle amount after earning annual
    # interest for a specified amount of years.

    # compound_interest_principal = float(original_principal) + (float(original_principal) * (float((1 + float(annual_interest) / float(compound))) ** (float(total_years) * float(compound)) - 1))
    compound_interest_principal = (float(original_principal) *
                                   (
                                           float((1 + float(annual_interest) / float(compound))) **
                                           (float(total_years) * float(compound))
                                   )
                                   )
    future_value_of_series = float(monthly_contribution) * ((float((1 + float(annual_interest) / float(compound))) ** (float(total_years) * float(compound))) - 1) / (float(annual_interest) / float(compound))
    # Display the ending principle amount.
    total = compound_interest_principal + future_value_of_series
    print('At the end of ', total_years, 'years you will have $',
          format(compound_interest_principal, '.2f'))
    print('At the end of ', total_years, 'years you will have $',
          format(future_value_of_series, '.2f'))
    print('At the end of ', total_years, 'years you will have $',
          format(total, '.2f'))
    return '{:,.2f}'.format(total)

def calculate_monthly_contribution_percent_saved(data, stateTaxTotal, federalTaxTotal, stateTaxPercent, federalTaxPercent, socialSecurityTaxAmount, socialSecurityTaxPercent, mySalary):
    data['salaryWorkSavingInfo']['stateTaxTotal'] = round(stateTaxTotal, 2)
    data['salaryWorkSavingInfo']['federalTaxTotal'] = round(federalTaxTotal, 2)
    data['salaryWorkSavingInfo']['stateTaxPercent'] = round(stateTaxPercent, 2)
    data['salaryWorkSavingInfo']['federalTaxPercent'] = round(federalTaxPercent, 2)

    data['salaryWorkSavingInfo']['socialSecurityTaxAmount'] = round(socialSecurityTaxAmount, 2)
    data['salaryWorkSavingInfo']['socialSecurityTaxPercent'] = round(socialSecurityTaxPercent, 2)

    socialSecurityTaxPercent = 1.45
    socialSecurityTaxAmount = float(mySalary) * 1.45 / 100
    data['salaryWorkSavingInfo']['medicareTaxPercent'] = round(socialSecurityTaxPercent, 2)
    data['salaryWorkSavingInfo']['medicareTaxAmount'] = round(socialSecurityTaxAmount, 2)

    netIncome = float(mySalary) \
                - data['salaryWorkSavingInfo']['stateTaxTotal'] \
                - data['salaryWorkSavingInfo']['federalTaxTotal'] \
                - data['salaryWorkSavingInfo']['socialSecurityTaxAmount'] \
                - data['salaryWorkSavingInfo']['medicareTaxAmount']
    monthlyPutAsideFromPaycheck = '{:,.2f}'.format(float(((
                float(netIncome) * float(
            data['salaryWorkSavingInfo']['paycheckPercentSaved']) / 100.00)) / 12.00))
    return monthlyPutAsideFromPaycheck


@app.route('/calculate_paycheck', methods=['POST'])
def calculate():
    try:
        data = request.get_json()
        stateTaxTable = state_tax_table.scan()['Items']
        federalTaxTable = federal_tax_table.scan()['Items']
        mySalary = data['salaryWorkSavingInfo']['salaryInput']
        if data['salaryWorkSavingInfo']['marialStatus'] == '0':
            # tempDict = next((item for item in stateTaxTable if float(item["single_bracket"]) <= float(mySalary)), None)whatever
            tempStateTaxTableDict = sorted(
                list(filter(lambda item: item['single_bracket'] <= float(mySalary), stateTaxTable)),
                key=lambda item: item['single_bracket'])
            tempFederalTaxTableDict = sorted(
                list(filter(lambda item: item['single'] <= float(mySalary), federalTaxTable)),
                key=lambda item: item['single'])
            stateTaxTotal = 0.0
            federalTaxTotal = 0.0
            for index, row in enumerate(tempStateTaxTableDict[1:], start=1):  # 5
                stateTaxTotal = stateTaxTotal + (
                        (float(row['single_bracket']) - (float(tempStateTaxTableDict[index - 1]['single_bracket']) + 1)) * (
                            float(
                                tempStateTaxTableDict[index - 1]['single_rate']) / 100))
                # print(stateTaxTotal)
            stateTaxTotal = stateTaxTotal + ((float(mySalary) - float(tempStateTaxTableDict[-1]['single_bracket'] + 1)) * (
                float(tempStateTaxTableDict[-1]['single_rate'])) / 100)
            print(stateTaxTotal)

            for index, row in enumerate(tempFederalTaxTableDict[1:], start=1):  # 5
                federalTaxTotal = federalTaxTotal + (
                        (float(row['single']) - (float(tempFederalTaxTableDict[index - 1]['single']) + 1)) * (
                        float(
                            tempFederalTaxTableDict[index - 1]['tax_rate']) / 100))
                # print(federalTaxTotal)
            federalTaxTotal = federalTaxTotal + ((float(mySalary) - float(tempFederalTaxTableDict[-1]['single'] + 1)) * (
                float(tempFederalTaxTableDict[-1]['tax_rate'])) / 100)
            print(federalTaxTotal)
        else:
            # tempDict = next((item for item in stateTaxTable if float(item["single_bracket"]) <= float(mySalary)), None)whatever
            tempStateTaxTableDict = sorted(
                list(filter(lambda item: item['married_bracket'] <= float(mySalary), stateTaxTable)),
                key=lambda item: item['married_bracket'])
            tempFederalTaxTableDict = sorted(
                list(filter(lambda item: item['married_filing_jointly'] <= float(mySalary), federalTaxTable)),
                key=lambda item: item['married_filing_jointly'])
            stateTaxTotal = 0.0
            federalTaxTotal = 0.0
            for index, row in enumerate(tempStateTaxTableDict[1:], start=1):  # 5
                stateTaxTotal = stateTaxTotal + (
                        (float(row['married_bracket']) - (
                                    float(tempStateTaxTableDict[index - 1]['married_bracket']) + 1)) * (
                                float(
                                    tempStateTaxTableDict[index - 1]['married_rate']) / 100))
                # print(stateTaxTotal)
            stateTaxTotal = stateTaxTotal + (
                        (float(mySalary) - float(tempStateTaxTableDict[-1]['married_bracket'] + 1)) * (
                    float(tempStateTaxTableDict[-1]['single_rate'])) / 100)
            print(stateTaxTotal)

            for index, row in enumerate(tempFederalTaxTableDict[1:], start=1):  # 5
                federalTaxTotal = federalTaxTotal + (
                        (float(row['married_filing_jointly']) - (float(tempFederalTaxTableDict[index - 1]['married_filing_jointly']) + 1)) * (
                        float(
                            tempFederalTaxTableDict[index - 1]['tax_rate']) / 100))
                # print(federalTaxTotal)
            federalTaxTotal = federalTaxTotal + (
                        (float(mySalary) - float(tempFederalTaxTableDict[-1]['married_filing_jointly'] + 1)) * (
                    float(tempFederalTaxTableDict[-1]['tax_rate'])) / 100)
            print(federalTaxTotal)

        stateTaxPercent = float(round(stateTaxTotal, 2)) * 100 / float(mySalary)
        federalTaxPercent = float(round(federalTaxTotal, 2)) * 100 / float(mySalary)

        # FICA section
        socialSecurityTaxAmount = 0.0
        socialSecurityTaxPercent = 0.0
        if float(mySalary) >= 137000:
            socialSecurityTaxAmount = 8537.40
            socialSecurityTaxPercent = round(8537.40 * 100 / float(mySalary), 2)
        else:
            socialSecurityTaxAmount = round(float(mySalary) * 6.2 / 100, 2)
            socialSecurityTaxPercent = 6.2

        data['salaryWorkSavingInfo']['monthlyPutAsideFromPaycheck'] = calculate_monthly_contribution_percent_saved(data, stateTaxTotal, federalTaxTotal, stateTaxPercent, federalTaxPercent, socialSecurityTaxAmount, socialSecurityTaxPercent, mySalary)

        if data['salaryWorkSavingInfo']['payFrequency'] == 365:
            data['salaryWorkSavingInfo']['stateTaxTotal'] = round(stateTaxTotal, 2)
            data['salaryWorkSavingInfo']['federalTaxTotal'] = round(federalTaxTotal, 2)
            data['salaryWorkSavingInfo']['stateTaxPercent'] = round(stateTaxPercent, 2)
            data['salaryWorkSavingInfo']['federalTaxPercent'] = round(federalTaxPercent, 2)


            data['salaryWorkSavingInfo']['socialSecurityTaxAmount'] = round(socialSecurityTaxAmount, 2)
            data['salaryWorkSavingInfo']['socialSecurityTaxPercent'] = round(socialSecurityTaxPercent, 2)

            socialSecurityTaxPercent = 1.45
            socialSecurityTaxAmount = float(mySalary) * 1.45/100
            data['salaryWorkSavingInfo']['medicareTaxPercent'] = round(socialSecurityTaxPercent, 2)
            data['salaryWorkSavingInfo']['medicareTaxAmount'] = round(socialSecurityTaxAmount, 2)

            netIncome = float(mySalary) \
                        - data['salaryWorkSavingInfo']['stateTaxTotal'] \
                        - data['salaryWorkSavingInfo']['federalTaxTotal'] \
                        - data['salaryWorkSavingInfo']['socialSecurityTaxAmount'] \
                        - data['salaryWorkSavingInfo']['medicareTaxAmount']
            data['salaryWorkSavingInfo']['netIncome'] = '{:,.2f}'.format(netIncome)
            data['salaryWorkSavingInfo']['totalTaxAmount'] = '{:,.2f}'.format(data['salaryWorkSavingInfo']['federalTaxTotal'] + data['salaryWorkSavingInfo']['stateTaxTotal'])
            data['salaryWorkSavingInfo']['totalFicaAmount'] = '{:,.2f}'.format(data['salaryWorkSavingInfo']['socialSecurityTaxAmount'] + data['salaryWorkSavingInfo']['medicareTaxAmount'])

            data['salaryWorkSavingInfo']['totalTaxPercent'] = '{:,.2f}'.format(
                data['salaryWorkSavingInfo']['federalTaxPercent'] + data['salaryWorkSavingInfo']['stateTaxPercent'])
            data['salaryWorkSavingInfo']['totalFicaPercent'] = '{:,.2f}'.format(
                data['salaryWorkSavingInfo']['socialSecurityTaxPercent'] + data['salaryWorkSavingInfo']['medicareTaxPercent'])

            data['salaryWorkSavingInfo']['takeHomeSalaryTaxPercent'] = '{:,.2f}'.format(float(100.00) \
                                                                                        - float(data['salaryWorkSavingInfo']['totalTaxPercent'])
                                                                                        - float(data['salaryWorkSavingInfo']['totalFicaPercent']))
            data['salaryWorkSavingInfo']['grossPaycheck'] = '{:,.2f}'.format(float(mySalary))

        elif data['salaryWorkSavingInfo']['payFrequency'] == 15:
            data['salaryWorkSavingInfo']['stateTaxTotal'] = round(stateTaxTotal/24, 2)
            data['salaryWorkSavingInfo']['federalTaxTotal'] = round(federalTaxTotal/24, 2)
            data['salaryWorkSavingInfo']['stateTaxPercent'] = round(stateTaxPercent/24, 2)
            data['salaryWorkSavingInfo']['federalTaxPercent'] = round(federalTaxPercent/24, 2)

            mySalary = float(mySalary) / 24.00
            data['salaryWorkSavingInfo']['socialSecurityTaxAmount'] = round(socialSecurityTaxAmount/24, 2)
            data['salaryWorkSavingInfo']['socialSecurityTaxPercent'] = round(socialSecurityTaxPercent/24, 2)
            socialSecurityTaxPercent = 1.45
            socialSecurityTaxAmount = float(mySalary) * 1.45/100
            data['salaryWorkSavingInfo']['medicareTaxPercent'] = round(socialSecurityTaxPercent/24, 2)
            data['salaryWorkSavingInfo']['medicareTaxAmount'] = round(socialSecurityTaxAmount/24, 2)

            netIncome = float(mySalary) \
                        - data['salaryWorkSavingInfo']['stateTaxTotal'] \
                        - data['salaryWorkSavingInfo']['federalTaxTotal'] \
                        - data['salaryWorkSavingInfo']['socialSecurityTaxAmount'] \
                        - data['salaryWorkSavingInfo']['medicareTaxAmount']
            data['salaryWorkSavingInfo']['netIncome'] = '{:,.2f}'.format(netIncome)
            data['salaryWorkSavingInfo']['totalTaxAmount'] = '{:,.2f}'.format(data['salaryWorkSavingInfo']['federalTaxTotal'] + data['salaryWorkSavingInfo']['stateTaxTotal'])
            data['salaryWorkSavingInfo']['totalFicaAmount'] = '{:,.2f}'.format(data['salaryWorkSavingInfo']['socialSecurityTaxAmount'] + data['salaryWorkSavingInfo']['medicareTaxAmount'])

            data['salaryWorkSavingInfo']['totalTaxPercent'] = '{:,.2f}'.format(
                data['salaryWorkSavingInfo']['federalTaxPercent'] + data['salaryWorkSavingInfo']['stateTaxPercent'])
            data['salaryWorkSavingInfo']['totalFicaPercent'] = '{:,.2f}'.format(
                data['salaryWorkSavingInfo']['socialSecurityTaxPercent'] + data['salaryWorkSavingInfo']['medicareTaxPercent'])

            data['salaryWorkSavingInfo']['takeHomeSalaryTaxPercent'] = '{:,.2f}'.format(float(100.00) \
                                                                                        - float(data['salaryWorkSavingInfo']['totalTaxPercent'])
                                                                                        - float(data['salaryWorkSavingInfo']['totalFicaPercent']))
            data['salaryWorkSavingInfo']['grossPaycheck'] = '{:,.2f}'.format(float(mySalary))
        elif data['salaryWorkSavingInfo']['payFrequency'] == 14:
            data['salaryWorkSavingInfo']['stateTaxTotal'] = round(stateTaxTotal/26, 2)
            data['salaryWorkSavingInfo']['federalTaxTotal'] = round(federalTaxTotal/26, 2)
            data['salaryWorkSavingInfo']['stateTaxPercent'] = round(stateTaxPercent/26, 2)
            data['salaryWorkSavingInfo']['federalTaxPercent'] = round(federalTaxPercent/26, 2)

            mySalary = float(mySalary) / 26.00
            data['salaryWorkSavingInfo']['socialSecurityTaxAmount'] = round(socialSecurityTaxAmount/26, 2)
            data['salaryWorkSavingInfo']['socialSecurityTaxPercent'] = round(socialSecurityTaxPercent/26, 2)
            socialSecurityTaxPercent = 1.45
            socialSecurityTaxAmount = float(mySalary) * 1.45/100
            data['salaryWorkSavingInfo']['medicareTaxPercent'] = round(socialSecurityTaxPercent/26, 2)
            data['salaryWorkSavingInfo']['medicareTaxAmount'] = round(socialSecurityTaxAmount/26, 2)

            netIncome = float(mySalary) \
                        - data['salaryWorkSavingInfo']['stateTaxTotal'] \
                        - data['salaryWorkSavingInfo']['federalTaxTotal'] \
                        - data['salaryWorkSavingInfo']['socialSecurityTaxAmount'] \
                        - data['salaryWorkSavingInfo']['medicareTaxAmount']
            data['salaryWorkSavingInfo']['netIncome'] = '{:,.2f}'.format(netIncome)
            data['salaryWorkSavingInfo']['totalTaxAmount'] = '{:,.2f}'.format(data['salaryWorkSavingInfo']['federalTaxTotal'] + data['salaryWorkSavingInfo']['stateTaxTotal'])
            data['salaryWorkSavingInfo']['totalFicaAmount'] = '{:,.2f}'.format(data['salaryWorkSavingInfo']['socialSecurityTaxAmount'] + data['salaryWorkSavingInfo']['medicareTaxAmount'])

            data['salaryWorkSavingInfo']['totalTaxPercent'] = '{:,.2f}'.format(
                data['salaryWorkSavingInfo']['federalTaxPercent'] + data['salaryWorkSavingInfo']['stateTaxPercent'])
            data['salaryWorkSavingInfo']['totalFicaPercent'] = '{:,.2f}'.format(
                data['salaryWorkSavingInfo']['socialSecurityTaxPercent'] + data['salaryWorkSavingInfo']['medicareTaxPercent'])

            data['salaryWorkSavingInfo']['takeHomeSalaryTaxPercent'] = '{:,.2f}'.format(float(100.00) \
                                                                                        - float(data['salaryWorkSavingInfo']['totalTaxPercent'])
                                                                                        - float(data['salaryWorkSavingInfo']['totalFicaPercent']))
            data['salaryWorkSavingInfo']['grossPaycheck'] = '{:,.2f}'.format(float(mySalary))
        # data['salaryWorkSavingInfo']['monthlyPutAsideFromPaycheck'] = '{:,.2f}'.format(float(((float(data['salaryWorkSavingInfo']['netIncome'].replace(',', '')) * float(data['salaryWorkSavingInfo']['paycheckPercentSaved']) / 100.00))/12.00))

        data['salaryWorkSavingInfo']['futureCompoundInterest'] = compound_interest_calculator(data['salaryWorkSavingInfo']['currentSavingAmount'], data['salaryWorkSavingInfo']['apyAnnually'], 12, data['salaryWorkSavingInfo']['yearSaved'],
                                                                                              data['salaryWorkSavingInfo']['monthlyPutAsideFromPaycheck'].replace(',',''))
        data['salaryWorkSavingInfo']['yearFuture'] = datetime.datetime.now().year + int(data['salaryWorkSavingInfo']['yearSaved'])

    except ClientError as e:
        print(e.response['Error']['Message'])
    return json_response(data)


@app.route('/duplicate_table', methods=['GET'])
def duplicate():
    dynamoclient = boto3.resource('dynamodb')
    table = dynamoclient.Table('state_tax_back_up')
    rowList = csv.DictReader(open('state_tax.csv'))
    rows = []
    for row in rowList:
        rows.append(row)
    with table.batch_writer() as batch:
        for row in rows:
            batch.put_item(Item=row)
    return True


# @app.route('/seed_federal_tax', methods=['GET'])
# def seed_federal_tax(dynamodb=None):
#     try:
#         federal_tax_dict_list = [
#             {
#                 'id': 0,
#                 'tax_rate': 10,
#                 'single': 0,
#                 'married_filing_jointly': 0,
#                 'married_filing_separately': 0,
#                 'head_of_household': 0,
#             },
#             {
#                 'id': 1,
#                 'tax_rate': 12,
#                 'single': 9875,
#                 'married_filing_jointly': 19750,
#                 'married_filing_separately': 9875,
#                 'head_of_household': 14100,
#             },
#             {
#                 'id': 2,
#                 'tax_rate': 22,
#                 'single': 40125,
#                 'married_filing_jointly': 80250,
#                 'married_filing_separately': 40125,
#                 'head_of_household': 53700,
#             },
#             {
#                 'id': 3,
#                 'tax_rate': 24,
#                 'single': 85525,
#                 'married_filing_jointly': 171050,
#                 'married_filing_separately': 85525,
#                 'head_of_household': 85500,
#             },
#         ]
#
#         if not dynamodb:
#             dynamodb = boto3.resource('dynamodb')
#
#         table = dynamodb.create_table(
#             TableName='federal_tax',
#             KeySchema=[
#                 {
#                     'AttributeName': 'id',
#                     'KeyType': 'HASH'  # Partition key
#                 },
#                 {
#                     'AttributeName': 'tax_rate',
#                     'KeyType': 'N'
#                 },
#                 {
#                     'AttributeName': 'single',
#                     'KeyType': 'N'
#                 },
#                 {
#                     'AttributeName': 'married_filing_jointly',
#                     'KeyType': 'N'
#                 },
#                 {
#                     'AttributeName': 'married_filing_separately',
#                     'KeyType': 'N'
#                 },
#                 {
#                     'AttributeName': 'head_of_household',
#                     'KeyType': 'N'
#                 },
#
#             ],
#             AttributeDefinitions=[
#                 {
#                     'AttributeName': 'id',
#                     'AttributeType': 'N'
#                 },
#                 {
#                     'AttributeName': 'tax_rate',
#                     'AttributeType': 'N'
#                 },
#                 {
#                     'AttributeName': 'single',
#                     'AttributeType': 'N'
#                 },
#                 {
#                     'AttributeName': 'married_filing_jointly',
#                     'AttributeType': 'N'
#                 },
#                 {
#                     'AttributeName': 'married_filing_separately',
#                     'AttributeType': 'N'
#                 },
#                 {
#                     'AttributeName': 'head_of_household',
#                     'AttributeType': 'N'
#                 },
#             ],
#             ProvisionedThroughput={
#                 'ReadCapacityUnits': 10,
#                 'WriteCapacityUnits': 10
#             }
#         )
#         # table = dynamodb.create_table(
#         #     TableName='Movies',
#         #     KeySchema=[
#         #         {
#         #             'AttributeName': 'year',
#         #             'KeyType': 'HASH'  # Partition key
#         #         },
#         #         {
#         #             'AttributeName': 'title',
#         #             'KeyType': 'RANGE'  # Sort key
#         #         }
#         #     ],
#         #     AttributeDefinitions=[
#         #         {
#         #             'AttributeName': 'year',
#         #             'AttributeType': 'N'
#         #         },
#         #         {
#         #             'AttributeName': 'title',
#         #             'AttributeType': 'S'
#         #         },
#         #
#         #     ],
#         #     ProvisionedThroughput={
#         #         'ReadCapacityUnits': 10,
#         #         'WriteCapacityUnits': 10
#         #     }
#         # )
#         for federal_tax_dict in federal_tax_dict_list:
#             table.put_item(Item=federal_tax_dict)
#
#         # table.put_item(Item={'year': 2002, 'title': 'hello'})
#     except ClientError as e:
#         print(e.response['Error']['Message'])
#     return json_response({"message": "1234Hello, world!"})

def json_response(data, response_code=200):
    return json.dumps(data), response_code, {'Content-Type': 'application/json'}


if __name__ == "__main__":
    app.run(port=5000, debug=True)
