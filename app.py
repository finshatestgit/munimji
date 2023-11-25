from flask import Flask, request, jsonify
from pymongo import MongoClient
import re

app = Flask(__name__)

# MongoDB Configuration
# MONGO_URI = "mongodb://localhost:27017/finsha"
# client = MongoClient(MONGO_URI)
# db = client["munimji2"]
MONGO_URI = "mongodb://munimdb2:XMQ4d6T7pFzA07eVJqFQ4mumNQ76YOX6wKdcsfVn8zPimd63eCB0IYIM9G5KF7DgRn19kZo4eoGuACDbU8VM9Q==@munimdb2.mongo.cosmos.azure.com:10255/munimji3?ssl=true&retrywrites=false"
client = MongoClient(MONGO_URI)
db = client["munimji3"]

INTENT_TO_MONGODB_COLUMN = {
    "financialndicator - Beta": ("Beta", "Beta value", None),

    "financialndicator - Alpha": ("Alpha", "Alpha value", None),
    "financialndicator - facevalue": ("NSE_Face_Value_INR", "Face Value", "RS"),
    "financialndicator - MarketCapitalisation": ("Market_Capitalisation_CR", "market capitalisation", "CR"),
    "financialndicator - closingPrice": ("NSE_Closing_Price_INR", "NSE Closing price", "RS"),
    "financialndicator - nsePE": ("NSE_PE_", "NSE price to equity ratio", "RS"),
    "financialndicator - SharesOutstanding": ("NSE_Shares_Outstanding_", "NSE shares outstanding", "RS"),
    "financialndicator - EPS": ("NSE_EPS_INR", "NSE earning per share", "RS"),


    "AnnualReport - consolidated - Sales": ("AFC_Sales", "consolidated sales data", "Crores"),
    "AnnualReport - consolidated - TotalCapital": ("AFC_Total_capital", "consolidated total capital", "Crores"),
    "AnnualReport - consolidated - ProfitAfterTax": ("AFC_Profit_after_tax", "consolidated profit after tax", "Crores"),
    "AnnualReport - consolidated - DividentIncome": ("AFC_Dividend_income", "consolidated divident income", "Crores"),
    "AnnualReport - consolidated - TotalExpenses": ("AFC_Total_expenses", "consolidated total expenses", "Crores"),
    "AnnualReport - consolidated - BankBalance": ("AFC_Bank_balance_short_term", "consolidated bank balance(short term)", "Crores"),
    "AnnualReport - consolidated - NetfixedAssets": ("AFC_Net_fixed_assets", "consolidated net fixed assets", "Crores"),
    "AnnualReport - consolidated - TotalLiabilities": ("AFC_Total_liabilities", "consolidated total liabilities", "Crores"),



    "QuarterlyReport - netSales": ("QIS_Net__sales_{quarter}", "net sales for {quarter}", "Crores"),
    "QuarterlyReport - netProfit": ("QIS_{quarter}_Net_ProfitLossafter_tax", "net profit for {quarter}", "Crores"),


}




def fetch_data_from_db(company):
    collection = db["samplechat"]


    pattern = re.compile(re.escape(company).replace("ltd.", "ltd\\.?").replace("ltd", "ltd\\.?"), re.I)

    search_fields = ["Company_Name", "NSE_symbol", "BSE_scrip_id"]

    for field in search_fields:
        data = collection.find_one({field: pattern})
        if data:
            return data
    return None

def fetch_data_for_company(company, column, description, unit):
    data = fetch_data_from_db(company)

    if not column:
        return "Column information is missing."

    if data and column in data:
        value = data[column]
        if value:
            response = f"The {description} for {company} is {value}"
            if unit:
                response += f" {unit}"
            return response
        else:
            return "Data not available at present."
    else:
        return "Data not available."


def fetch_company_info(company):
    data = fetch_data_from_db(company)

    if not data:
        return f"'5Paisa Capital Ltd. company info', please say like that"

    age_group = data.get("Age_group", None)
    first_trade_date = data.get("First_trading_date_on_BSE", None)
    BSE_scrip_id = data.get("BSE_scrip_id", None)
    responses = []
    if age_group:
        responses.append(f"Age group for {company} is {age_group}")
    if first_trade_date:
        responses.append(f"it is first traded on BSE on {first_trade_date}")
    if BSE_scrip_id:
        responses.append(f"its symbol is {BSE_scrip_id}")


    if responses:
        return " and ".join(responses) + "."
    else:
        return f"Sorry, I couldn't find the information for {company}"


# def manual_test():
#     print("Manual test mode.")
#     intent_name = input("Enter intent name: ")
#     company_name = input("Enter company name: ")
#
#     if intent_name == "companyInfo":
#         response = fetch_company_info(company_name)
#     elif intent_name in INTENT_TO_MONGODB_COLUMN:
#         column, description, unit = INTENT_TO_MONGODB_COLUMN[intent_name]
#         response = fetch_data_for_company(company_name, column, description, unit)
#     else:
#         response = "Invalid intent or not implemented."
#
#     print("Response:", response)


@app.route('/dialogflow-webhook', methods=['POST'])
def dialogflow_webhook():
    data = request.get_json()
    intent_name = data['queryResult']['intent']['displayName']
    company_name = data['queryResult']['parameters'].get('company_name')
    quarter = data['queryResult']['parameters'].get('quarter')

    column, description, unit = None, None, None

    if not company_name:
        return jsonify({"fulfillmentText": "Company name is missing."})

    if intent_name == "companyInfo":
        return jsonify({"fulfillmentText": fetch_company_info(company_name)})

    if intent_name in INTENT_TO_MONGODB_COLUMN:
        column, description, unit = INTENT_TO_MONGODB_COLUMN[intent_name]

        # Handling the QuarterlyReport dynamic logic
        if "QuarterlyReport" in intent_name and quarter:
            column = column.format(quarter=quarter)
            description = description.format(quarter=quarter)
    else:
        return jsonify({"fulfillmentText": "Sorry, I couldn't fetch that data."})

    result = fetch_data_for_company(company_name, column, description, unit)
    return jsonify({"fulfillmentText": result})

if __name__ == "__main__":
    # mode = input("Enter mode (test/server): ")
    # if mode == "test":
    #     manual_test()
    # else:
    app.run(debug=True)
