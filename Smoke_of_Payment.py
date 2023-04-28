import json
from json.decoder import JSONDecodeError
import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import hashlib

# use python -m pytest -x -rA Smoke_of_Payment.py to run
class TestAPI:
    TransId = 0
    paymentUrl = ""
    SecretKey = "a0d50f34-c0a0-4353-9561-195ddaf50be9"
    url = "http://109.202.9.135:7706"
    price_count = 40000

    def test_pay(self, ApiUrl=url):
        mthd = "/pay"
        ts = int(time.time())
        randOrderID = ((int(time.time() * 1000)) % 100000000) + 100000000
        ForHash = str(ts) + str(randOrderID) + TestAPI.SecretKey
        CurrSIGN = str(hashlib.sha256(ForHash.encode()).hexdigest())
        data = {
            "supplierId": 1,
            "acquirerId": 2,
            "orderId": str(randOrderID),
            "userId": "1",
            "staff": [
                {
                    "description": "TESTENG",
                    "price": TestAPI.price_count,
                    "qty": 1000,
                    "PayAttribute": 1,
                    "lineAttribute": 1,
                    "taxId": 1,
                    "agentMode": 1,
                    "providerData": {
                        "Phone": "80008890000",
                        "Name": "NameName",
                        "INN": "123456789012"
                    }
                }
            ],
            "TotalPrice": TestAPI.price_count,
            "backRef": "http://megadyyken.com/thankyou",
            "userPhoneOrEmail": "s.rozhkov@integrasources.com",
            "timestamp": ts,
            "sign": CurrSIGN
        }
        try:
            response = requests.post(ApiUrl + mthd, json=data)  # запрос /pay
        except requests.exceptions.ConnectionError:
            assert False, "Ошибка соединения с сервером"
        else:
            print(f"\n {mthd}'s response: {response.text}\n")
            assert response.status_code == 200, "Status code isn't equal 200"
            TestAPI.TransId = response.json()["transactionId"]
            assert TestAPI.TransId > 100100, "Transaction ID is less than 100100"

    def test_getUrl_of_pay(self, ApiUrl=url):
        mthd = "/getPaymentUrl"
        data = {"transactionId": TestAPI.TransId}
        headers = {"Accept": "application/json"}
        for i in range(15):
            response = requests.get(ApiUrl + mthd, params=data, headers=headers)  # запрос /get
            assert response.status_code == 200, "Status code isn't equal 200"
            statusCode = response.json()["statusCode"]
            if statusCode == "1":
                break
            time.sleep(3)
        print(f"\n {mthd}'s response: {response.json()}\n")
        assert statusCode == "1", "Status code is not 1"
        TestAPI.paymentUrl = response.json()["paymentUrl"]
        assert TestAPI.paymentUrl != "", "paymentUrl does not exist"

    def test_frontbutton(self):
        browser = webdriver.Chrome()
        browser.get(TestAPI.paymentUrl)
        time.sleep(1)
        button = browser.find_element(By.ID, "payment_btn")
        button.click()
        time.sleep(1)
        restext_elem = browser.find_element(By.ID, "result_text")
        restext = restext_elem.text
        print(f"\n Front's response: {restext}\n")
        assert restext == "Платёж прошёл успешно", "Payment failed after button 'Pay!'"

    def test_transaction_of_pay(self):
        mthd = "/transaction"
        data = {"transactionId": TestAPI.TransId, "userId": "1", "sign": "123123123"}
        headers = {"Accept": "application/json"}
        for i in range(10):
            response = requests.get(TestAPI.url + mthd, params=data, headers=headers)  # запрос /transaction
            if "ofdChequeFormatter" in response.json():
                break
            time.sleep(2)
        print(f"\n {mthd}'s response: {response.json()}\n")
        assert "status" in response.json(), "There is no the 'status' field in the response"
        assert response.json()["status"] == "SUCCESS", "Status of the payment is not SUCCESS"
        assert "transType" in response.json(), "There is no the 'transType' field in the response"
        assert response.json()["transType"] == "TRANSFER", "Type of the transaction is not TRANSFER"
        # assert "ofdChequeFormatter" in response.json(), "There is no the Cheque in the response"
        assert response.json()["ofdChequeFormatter"] != "", "Cheque is not exist"
        assert response.status_code == 200, "Status code isn't equal 200"

    def test_CancelPayment(self, ApiUrl=url):
        ts = int(time.time())
        ForHash = str(ts) + str(TestAPI.TransId) + TestAPI.SecretKey
        CurrSIGN = str(hashlib.sha256(ForHash.encode()).hexdigest())
        mthd = "/cancelPayment"
        data = {
            "refundTransactionId": TestAPI.TransId,
            "refundAmount": 0,
            "staff": [
                {
                    "description": "TESTENG",
                    "price": TestAPI.price_count,
                    "qty": 1000,
                    "PayAttribute": 1,
                    "lineAttribute": 1,
                    "taxId": 1,
                    "agentMode": 1,
                    "providerData": {
                        "Phone": "80008890000",
                        "Name": "NameName",
                        "INN": "123456789012"
                    }
                }
            ],
            "timestamp": ts,
            "sign": CurrSIGN
        }
        response = requests.post(ApiUrl + mthd, json=data)  # запрос /cancelPay
        print(f"\n {mthd}'s response: {response.text}\n")
        assert response.status_code == 200, "Status code isn't equal 200"
        TestAPI.TransId = response.json()["transactionId"]
        assert TestAPI.TransId > 100100, "Transaction ID is less than 100100"

    def test_getTransStatus_of_cancel(self, ApiUrl=url):
        mthd = "/getTransactionStatus"
        data = {"transactionId": TestAPI.TransId}
        headers = {"Accept": "application/json"}
        time.sleep(2)
        for i in range(10):
            response = requests.get(ApiUrl + mthd, params=data, headers=headers)  # запрос /getTransactionStatus
            assert "statusCode" in response.json(), "There is no the 'statusCode' field in the response"
            statusCode = response.json()["statusCode"]
            if statusCode == "1":
                break
            time.sleep(2)
        print(f"\n {mthd}'s response: {response.text} \n")
        assert response.status_code == 200, "Status code isn't equal 200"
        statusCode = response.json()["statusCode"]
        assert statusCode == "0", "Status code is not 0"

    def test_transaction_of_cancel(self):
        mthd = "/transaction"
        data = {"transactionId": TestAPI.TransId, "userId": "1", "sign": "123123123"}
        headers = {"Accept": "application/json"}
        time.sleep(3)  # вынужденная задержка, чек приходит не сразу в BackOffice
        response = requests.get(TestAPI.url + mthd, params=data, headers=headers)  # запрос /transaction
        print(f"\n {mthd}'s response: {response.json()}\n")
        assert "status" in response.json(), "There is no the 'status' field in the response"
        assert response.json()["status"] == "SUCCESS", "Status of the payment is not SUCCESS"
        assert "transType" in response.json(), "There is no the 'transType' field in the response"
        assert response.json()["transType"] == "REFUND_TRANSFER", "Type of the transaction is not REFUND_TRANSFER"
        assert "ofdChequeFormatter" in response.json(), "There is no the Cheque in the response"
        assert response.json()["ofdChequeFormatter"] != "", "Cheque is not exist"
        assert response.status_code == 200, "Status code isn't equal 200"

# Самый мощный сценарий, это когда мы:
# 1) Отправляем транзакцию.
# 2) Оплачиваем.
# 3) Убеждаемся что она упала в Бэк офис
# 4) Убеждаемся что чек пробился
# 5) Отменяем транзакцию - готово
# 6) Убеждаемся что отмена упала в Бэк офис
# 7) Убеждаемся что чек на отмену пробился

# Тест проверки присутствия ключа

# try:
#     parsed_answer = response.json()  # попытка распарсить json
#     print(parsed_answer)  # вывод результата парса
# except JSONDecodeError:
#     print("There is no JSON in the response")  # Если строка в блоке try привела к исключению, программа вывалится сюда
#
# obj = json.loads(some_jsonlike_text)
# keyToTest = "error"
# if keyToTest in response_in_text:
#     print(response_in_text[keyToTest])
# else:
#     print(f"The {keyToTest} key is not found")

# Это не работает, если искомый ключ действительно есть в теле запроса. Есть мысли, что таким образом не будет нужды проверять тело ответов.
# Тест проверки присутствия ключа
