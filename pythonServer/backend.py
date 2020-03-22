from flask import Flask
from flask import request,jsonify
from flask import make_response
from functools import wraps
import u2py
import xmltodict
import pprint
import json
import random
import jwt
from datetime import datetime
from collections import OrderedDict
from flask_cors import CORS, cross_origin

app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisisthesercretkey'
CORS(app)

import logging

logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

file_handler = logging.FileHandler('./logs/api.log')
file_handler.setFormatter(formatter)

logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def checkuser(username,password):
	users={"jhon":"abc","stuart":"xyz","robin":"123"}
	for keys in users.keys():
		if(keys==username):
			if(users[username]==password):
				return 'True'
			else:
				return 'False'
		else:
			return 'False'
################################
## ITEMS API ###################
################################

@app.route('/api/item', methods=['GET'])
def allItems():
    itemFile=u2py.File("PO.ITEM.MST")
    fileList=u2py.List(0,itemFile)
    idData=fileList.readlist()
    totalCount=idData.dcount(u2py.FM)+1
    recordid=[]
    start=1
    for i in range(start,totalCount):
        tm=idData.extract(i)
        recordid.append(list(tm)[0][0])
    items=[]
    for ids in recordid:
        field={}
        item=list(itemFile.readv(ids,0))[0][0]
        desc=list(itemFile.readv(ids,1))[0][0]
        field['@_ID']=item
        field['@DESC']=desc
        items.append(field)

    return {"data": items}, 200

################################
## VENDORS API #################
################################

def filterVendor(vendorNo, vendorName,vendorCompany):
    vendor_No = vendor_Name = vendor_Company = ""
    if vendorNo and vendorNo != 'null':
        vendor_No = ' WITH @ID = "' + str(vendorNo) + '"'
    if vendorName and vendorName != 'null':
        vendor_Name = 'AND WITH VEND.NAME = "' + vendorName + '"'
    if vendorCompany and vendorCompany != 'null':
        vendor_Company = 'AND WITH VEND.COMPANY = "' + vendorCompany + '"'

    if not vendorNo and not vendorName and not vendorCompany:
        commandLine = 'SELECT {}'.format('PO.VENDOR.MST')
    else:
        commandLine = 'SELECT {} {} {} {}'.format('PO.VENDOR.MST', vendor_No, vendor_Name, vendor_Company)
    
    line= commandLine.find('PO.VENDOR.MST  AND')
    if (line != -1):
        commandLine = commandLine.replace('PO.VENDOR.MST  AND','PO.VENDOR.MST')
    return commandLine

@app.route('/api/vendor', methods=['GET'])
def vendorList():
    allVendors = request.args.get('allVendors')
    saveList_name = 'PAGE.LIST'
    if allVendors != 'true':
        start =1
        pageIndex = int(request.args.get('pageIndex'))
        pageSize = int(request.args.get('pageSize'))
        vendorNo = request.args.get('VendorNo')
        vendorName = request.args.get('Name')
        vendorCompany = request.args.get('Company')
        start = pageIndex * pageSize + 1
        end = (pageIndex + 1) * pageSize
        lastOrder = False
        commandLine = filterVendor(vendorNo, vendorName,vendorCompany)
    else:
        start = 1
        commandLine = 'SELECT {}'.format('PO.VENDOR.MST')

    u2py.run(commandLine, capture=True)
    u2py.run('SAVE.LIST {}'.format(saveList_name))

    dataFile = u2py.File('PO.VENDOR.MST')
    myList = u2py.List(0, saveList_name)
    t_id = myList.readlist()
    totalCount = t_id.dcount(u2py.FM)
    if allVendors == 'true':
        end = totalCount - 1
    data = {}	
    for x in range(start, end + 1):
        if x > totalCount:
            break
        ids = t_id.extract(x)
        vendorCompany = list(dataFile.readv(ids, 1))[0][0]
        vendorName = list(dataFile.readv(ids, 2))[0][0]
        vendorPhone = list(dataFile.readv(ids, 4))[0][0]
        vendorItems = list(dataFile.readv(ids, 5))
        vendorId = list(ids)[0][0]
        orderDict = mappingVendor(vendorCompany,vendorName,vendorPhone,vendorItems,vendorId)
        data[vendorId]=(orderDict)
    return {
        'status': 200,
        'data': data,
        'totalCount': totalCount
    }
def mappingVendor(vendorCompany,vendorName,vendorPhone,vendorItems,vendorId):
        vendorItems = [items[0] for items in vendorItems]
        details = {}
        details['vendorCompany'] = vendorCompany
        details['vendorName'] = vendorName
        details['phoneNo'] = vendorPhone
        details['itemId'] = vendorItems
        return details
		
@app.route('/api/vendor', methods=['POST'])
def vendorCreate():
    vendorData = request.get_json()
    vendorId = random.randrange(12, 10 ** 6)
    itemIds = vendorData['itemIds']
    vendorDetails = vendorData['vendorDetail']

    upsertVendor(vendorDetails, itemIds, vendorId)
    return {
        'status': 200,
        'msg': "vendor " + str(vendorId) + " created",
    }


@app.route('/api/vendor/<vendorId>', methods=['PUT'])
def vendorUpdate(vendorId):
    vendorData = request.get_json()
    itemIds = vendorData['itemIds']
    vendorDetails = vendorData['vendorDetail']
    upsertVendor(vendorDetails, itemIds, vendorId)
    return {
        'status': 200,
        'msg': "vendor updated",
        'data': vendorData
    }

@app.route('/api/vendor/<vendorId>', methods=['GET'])
def vendorGet(vendorId):
    status = checkExistingRecord("PO.VENDOR.MST", vendorId)
    if (status):
        orderFile = u2py.File("PO.VENDOR.MST")
        vendorData={}
        vendorDict={}
        vendorDict['Company']=list(orderFile.readv(vendorId,1))[0][0]
        vendorDict['Contact']=list(orderFile.readv(vendorId,2))[0][0]
        vendorDict['Street']=list(orderFile.readv(vendorId,3))[0][0]
        vendorDict['City']=list(orderFile.readv(vendorId,3))[1][0]
        vendorDict['State']=list(orderFile.readv(vendorId,3))[2][0]
        vendorDict['Zip']=list(orderFile.readv(vendorId,3))[3][0]
        vendorDict['Phone']=list(orderFile.readv(vendorId,4))[0][0]
        itemid=list(orderFile.readv(vendorId,5))
        items=[]
   
        for i in itemid:
                itemsa={}
                itemsa["itemId"]=i[0]
                items.append(itemsa)
        vendorData["particularVendorData"]=vendorDict
        vendorData["itemIds"]=items
        return {
            'status': 200,
            'vendorData': vendorData
        }
    else:
        return {
            'status': 404,
            'msg': 'Vendor not found'
        }

################################
## PURCHASE ORDERS API #########
################################

@app.route('/api/order', methods=['GET'])
def purchaseOrderList():
    allOrders = request.args.get('allOrders')
    lastOrder = False
    if allOrders is None:
        saveList_name = 'PAGE.LIST'
        pageIndex = int(request.args.get('pageIndex'))
        pageSize = int(request.args.get('pageSize'))
        orderNo = request.args.get('OrderNo')

        vendorName = request.args.get('VendorName')
        fromDate = request.args.get('FromDate')
        toDate = request.args.get('ToDate')

        start = pageIndex * pageSize + 1
        end = (pageIndex + 1) * pageSize
        lastOrder = False
        commandLine = filterPurchaseOrder(orderNo, vendorName, fromDate, toDate)
    else:
        start = 1
        saveList_name = 'TEMP.LIST'
        commandLine = 'SELECT {}'.format('PO.ORDER.MST')

    u2py.run(commandLine, capture=True)
    u2py.run('SAVE.LIST {}'.format(saveList_name))

    dataFile = u2py.File('PO.ORDER.MST')
    myList = u2py.List(0, saveList_name)
    t_id = myList.readlist()
    totalCount = t_id.dcount(u2py.FM)
    if allOrders is not None:
        end = totalCount - 1
    data = []
    for x in range(start, end + 1):
        if x > totalCount:
            lastOrder = True
            break
        id = t_id.extract(x)

        date = list(dataFile.readv(id, 1))[0][0]
        vendorName = list(dataFile.readv(id, 14))[0][0]
        id = list(id)[0][0]
        orderDict = mappingOrder(date, vendorName, id)
        data.append(orderDict)
    return {
        'status': 200,
        'data': data,
        'lastOrder': lastOrder,
        'totalCount': totalCount
    }

@app.route('/api/order', methods=['POST'])
def purchaseOrderCreate():
    data = request.get_json()
    newOrderId = random.randrange(12, 10 ** 6)
    upsertPurchaseOrder(data['details'], data['itemDetails'], newOrderId, data['status'])
    return {
        'status': 200,
        'msg': 'OrderId ' + str(newOrderId) + ' created'
    }

@app.route('/api/order/<orderId>', methods=['PUT'])
def purchaseOrderUpdate(orderId):
    data = request.get_json()
    upsertPurchaseOrder(data['details'], data['itemDetails'], orderId, data['status'])
    return {
        'status': 200,
        'msg': 'OrderId ' + str(orderId) + ' updated'
    }

@app.route('/api/order/<orderID>', methods=['GET'])
def purchaseOrderGet(orderID):
    status = checkExistingRecord('PO.ORDER.MST', orderID)
    if status:
        commandLine = 'SELECT {}'.format('PO.ORDER.MST')
        saveList_name = 'PAGE.LIST'
        u2py.run(commandLine, capture=True)
        u2py.run('SAVE.LIST {}'.format(saveList_name))

        dataFile = u2py.File('PO.ORDER.MST')
        orderDetail = mapPurchaseOrder(dataFile, orderID)
        itemList = mapOrderItems(dataFile, orderID)
        submitStatus = list(dataFile.readv(orderID, 2))[0][0]

        return {
            'status': 200,
            'data': {
                'orderData' : orderDetail,
                'itemList':itemList,
                'submitStatus': submitStatus
            }
        }
    else:
        return {
            'status': 404,
            'msg': 'Order no not found'
        }


################################
## INVOICE API #################
################################

@app.route('/api/invoices', methods=['GET'])
def invoiceList():
    invoiceNo = request.args.get('invoiceNo')
    invoiceFromDate = request.args.get('invoiceFromDate')
    invoiceToDate = request.args.get('invoiceToDate')
    orderNo = request.args.get('orderNo')
    pageIndex = int(request.args.get('pageIndex'))
    pageSize = int(request.args.get('pageSize'))
    saveList_name = 'INVOICE.LIST'

    start = pageIndex * pageSize + 1
    end = (pageIndex + 1) * pageSize
    allInvoices = request.args.get('allVendors')

    if allInvoices  is not 'true':
        start = pageIndex * pageSize + 1
        end = (pageIndex + 1) * pageSize
        commandLine = filterInvoice(invoiceToDate,invoiceNo,invoiceFromDate,orderNo)
    else:
        commandLine = 'SELECT {}'.format('PO.INVOICE.MST')

    u2py.run(commandLine, capture=True)
    u2py.run('SAVE.LIST {}'.format(saveList_name))

    dataFile = u2py.File('PO.INVOICE.MST')
    myList = u2py.List(0, saveList_name)
    t_id = myList.readlist()
    totalCount = t_id.dcount(u2py.FM)

    data = []
    for x in range(start, end+1):
        if x > totalCount:
            break
        id = t_id.extract(x)
        invoiceDate = list(dataFile.readv(id, 1))[0][0]
        orderNo = list(dataFile.readv(id, 6))[0][0]
        invoiceAmt = list(dataFile.readv(id, 8))[0][0]
        id = list(id)[0][0]

        vendorDict = mappingInvoices(invoiceDate,orderNo,invoiceAmt,id)
        data.append(vendorDict)
    return {
        'status': 200,
        'data': data,
        'totalInvoices': totalCount
    }

def mappingInvoices(invoiceDate,orderNo,invoiceAmount,id):
    details = {}
    details['id'] = id
    details['orderNumber'] = orderNo
    details['amount'] = invoiceAmount
    details['date'] = convertDateFormat(invoiceDate,'external')
    return details

@app.route('/api/invoice', methods=['POST'])
def invoiceCreate():
    data = request.get_json()
    date = data['invoiceDetails']['invoiceDate']
    invoiceDate = datetime.strptime(date, "%Y-%m-%d").strftime("%m-%d-%Y")
    convertedDate = convertDateFormat(invoiceDate,'internal')
    upsertInvoice(data['invoiceDetails']['orderNo'], data['invoiceDetails']['invoiceDetails'],
                data['invoiceDetails']['invoiceNo'], convertedDate ,
                data['invoiceDetails']['invoiceAmount'], data['submitStatus'])
    return {
        'status': 200,

        'msg': 'Invoice {} generated'.format(data['invoiceDetails']['invoiceNo'])
    }


@app.route('/api/invoice/<invoiceId>', methods=['GET'])
def invoiceGet(invoiceId):
    status = checkExistingRecord('PO.INVOICE.MST', invoiceId)
    if (status):
        invoiceFile = u2py.File("PO.INVOICE.MST")
        invoiceNo = []
        invoiceDate = []
        orderNo = []
        invoiceAmount = []
        ids = []
        quantity = []
        invoiceStatus = []
        quantityReceived = []
        invoiceNo.append(invoiceId)
        invoiceDate.append(convertDateFormat(list(invoiceFile.readv(invoiceId,1))[0][0],'external'))
        orderNo.append(list(invoiceFile.readv(invoiceId,6))[0][0])
        invoiceStatus.append(list(invoiceFile.readv(invoiceId,7))[0][0])
        invoiceAmount.append(list(invoiceFile.readv(invoiceId,8))[0][0])
        itemsId=list(invoiceFile.readv(invoiceId,2))
        orderFile=u2py.File("PO.ORDER.MST")
        for i in range(len(itemsId)):
            ids.append(list(invoiceFile.readv(invoiceId,2))[i][0])
            quantity.append(list(invoiceFile.readv(invoiceId,3))[i][0])
            quantityReceived.append(list(orderFile.readv(orderNo[0],15))[i][0])
        return {
            "status": 200,
            "invoiceNo": invoiceNo,
            "invoiceDate": invoiceDate,
            "orderNo": orderNo,
            "ids": ids,
            "quantity": quantity,
            "invoiceStatus": invoiceStatus,
            "invoiceAmount": invoiceAmount,
            "quantityReceived": quantityReceived
        }
    else:
        return {
            'status': 404,
            'message': 'Invoice not found'
        }

@app.route('/api/invoice/order/<orderId>', methods=['GET'])
def invoicePurchaseOrderItemsGet(orderId):
    status = checkExistingRecord('PO.ORDER.MST', orderId)
    if (status):
        orderFile = u2py.File("PO.ORDER.MST")
        itemCost = []
        itemQuantity = []
        itemIds = []
        items=list(orderFile.readv(orderId,11))
        for i in range(len(items)):
                itemIds.append(list(orderFile.readv(orderId,11))[i][0])
                itemCost.append(list(orderFile.readv(orderId,13))[i][0])
                itemQuantity.append(list(orderFile.readv(orderId,12))[i][0])
        return {
            'status': 200,
            'cost': itemCost,
            'quantity': itemQuantity,
            "ids": itemIds,
        }
    else:
        return {
            'status': 404,
            'message': 'OrderNo not found'
        }

################################
## LOGIN API ###################
################################

@app.route('/login', methods=['POST'])
def login():
    auth = request.get_json()
    username = auth['loginDetails']['username']
    password = auth['loginDetails']['password']
    if (checkuser(username, password)):
        token = jwt.encode({'username': username, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)},
                           app.config['SECRET_KEY'])
        return {
            'status': 200,
            'token': token.decode('UTF-8')
        }
    return make_response('Could not verify!', 401)


################################
## HELPER METHODS ##############
################################

def checkExistingRecord(filename, recordID):
    fileObject = u2py.File(filename)
    try:
        recordObject = fileObject.read(recordID)
        return True
    except u2py.U2Error as e:
        return False

def upsertVendor(details, itemIds, recordID):
    address = [details['Street'], details['City'], details['State'], details['Zip']]
    data = [details['Company'], details['Contact'], address, details['Phone'], itemIds]
    vendorFile = u2py.File('PO.VENDOR.MST')
    vendorFile.write(recordID, u2py.DynArray(data))


def upsertPurchaseOrder(details, itemDetails, recordID, status):
    orderDate = datetime.strptime(details['OrderDate'], "%Y-%m-%d").strftime("%m-%d-%Y")
    formattedDate = convertDateFormat(orderDate,'internal')
    address = [details['Street'], details['City'], details['State'], details['ZipCode']]
    itemIds = []
    quantities = []
    costs = []
    for itemDetail in itemDetails:
        itemIds.append(itemDetail['ItemID'])
        quantities.append(itemDetail['Quantity'])
        costs.append(itemDetail['UnitCost'])
    data = [formattedDate, status, "", "", "", "", details['CompanyName'], details['ContactName'], address, details['PhoneNumber'], itemIds, quantities, costs, details['VendorName']]
    orderFile = u2py.File("PO.ORDER.MST")
    orderFile.write(recordID, u2py.DynArray(data))

def upsertInvoice(orderNo, invoiceDetails, invoiceNo, invoiceDate, invoiceAmount, status):
    invoiceData = u2py.DynArray()
    invoiceFile = u2py.File("PO.INVOICE.MST")
    itemNo = bytes("", "utf-8")
    description = bytes("", "utf-8")
    quantityOrdered = bytes("", "utf-8")
    quantityPending = bytes("", "utf-8")
    quantityReceived = bytes("", "utf-8")
    for i in range(len(invoiceDetails)):
        itemNo = itemNo + bytes(invoiceDetails[i]['itemNo'], "utf-8") + u2py.VM
        quantityOrdered = quantityOrdered + bytes(invoiceDetails[i]['quantityOrdered'], "utf-8") + u2py.VM
        quantityPending = quantityPending + bytes(str(invoiceDetails[i]['quantityPending']), "utf-8") + u2py.VM
        quantityReceived = quantityReceived + bytes(invoiceDetails[i]['quantityReceived'], "utf-8") + u2py.VM
    invoiceData.insert(1, 0, 0, invoiceDate)
    invoiceData.insert(2, 0, 0, itemNo[:-1])
    invoiceData.insert(3, 0, 0, quantityOrdered[:-1])
    invoiceData.insert(4, 0, 0, quantityPending[:-1])
    invoiceData.insert(5, 0, 0, quantityReceived[:-1])
    invoiceData.insert(6, 0, 0, orderNo)
    invoiceData.insert(7, 0, 0, status)
    invoiceData.insert(8, 0, 0, invoiceAmount)
    invoiceFile.write(invoiceNo, invoiceData)

def checkuser(username, password):
    users = {"user1": "abc", "user2": "xyz", "user3": "123"}
    for keys in users.keys():
        if (keys == username):
            if (users[username] == password):
                return 'True'
            else:
                return 'False'
        else:
            return 'False'

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return {"msg": "Token is missing"
                    }, 403
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            return data
        except:
            return {'msg': 'Token is invalid'}, 403

    return decorated

def filterPurchaseOrder(orderNo, vendorName, fromDate, toDate):
    order_No = vendor_Name = from_Date = to_Date = ""
    if orderNo and orderNo != 'null':
        order_No = ' WITH @ID = "' + str(orderNo) + '"'
    if vendorName and vendorName != 'null':
        vendor_Name = ' AND WITH VEND.NAME = "' + vendorName + '"'
    if fromDate and fromDate != 'null':
        from_Date = ' AND WITH ORDER.DATE GE "' + str(fromDate) + '"'
    if toDate and toDate != 'null':
        to_Date = ' AND WITH ORDER.DATE LE "' + str(toDate) + '"'

    if not orderNo and not vendorName and not fromDate and not toDate:
        commandLine = 'SELECT {}'.format('PO.ORDER.MST')
    else:
        commandLine = 'SELECT {} {} {} {} {}'.format('PO.ORDER.MST', order_No, vendor_Name, from_Date, to_Date)

    return commandLine

def filterInvoice(invoiceToDate,invoiceNo,invoiceFromDate,orderNo):
    invoice_No = order_No = date_from = date_to = ""
    if invoiceNo and invoiceNo != 'null':
        invoice_No = ' WITH @ID = "' + str(invoiceNo) + '"'
    if orderNo and orderNo != 'null':
        order_No = ' AND WITH ORDER.NO = "' + str(orderNo) + '"'
    if invoiceFromDate and invoiceFromDate != 'null':
        date_from = ' AND WITH INV.DATE GE "' + str(invoiceFromDate) + '"'
    if invoiceToDate and invoiceToDate != 'null':
        date_to = ' AND WITH INV.DATE LE "' + str(invoiceToDate) + '"'
    command = "SELECT {}{}{}{}{}".format('PO.INVOICE.MST',invoice_No, order_No, date_from, date_to)
    return command


def mappingOrder(date, vendorName, id):
    orderDict = {}
    orderDict['date'] = convertDateFormat(date,'external')
    orderDict['vendorName'] = vendorName
    orderDict['id'] = id
    return orderDict

def convertDateFormat(orderDate,format):
    date = u2py.DynArray()
    date.insert(1, 0, 0, orderDate)
    if format == 'internal':
        formattedDate = date.extract(1).iconv('D-')
    else:
        formattedDate = str(date.extract(1).oconv('D-'))
    return formattedDate

def mapPurchaseOrder(dataFile,orderID):
    orderDetailsDict = {}
    date = list(dataFile.readv(orderID, 1))[0][0]
    orderDetailsDict['OrderDate'] = convertDateFormat(date,'external')
    orderDetailsDict['CompanyName'] = list(dataFile.readv(orderID, 7))[0][0]
    orderDetailsDict['ContactName'] = list(dataFile.readv(orderID, 8))[0][0]
    orderDetailsDict['PhoneNumber'] = list(dataFile.readv(orderID, 10))[0][0]
    orderDetailsDict['VendorName'] = list(dataFile.readv(orderID, 14))[0][0]
    orderDetailsDict['Street'] = list(dataFile.readv(orderID, 9))[0][0]
    orderDetailsDict['City'] = list(dataFile.readv(orderID, 9))[1][0]
    orderDetailsDict['State'] = list(dataFile.readv(orderID, 9))[2][0]
    orderDetailsDict['ZipCode'] = list(dataFile.readv(orderID, 9))[3][0]
    return orderDetailsDict

def mapOrderItems(dataFile,orderID):
    itemId = [items[0] for items in list(dataFile.readv(orderID, 11))]
    cost = [items[0] for items in list(dataFile.readv(orderID, 12))]
    quantity= [items[0] for items in list(dataFile.readv(orderID, 13))]
    itemList = []
    for i in range(len(itemId)):
        itemDict = {}
        itemDict['ItemID'] = itemId[i]
        itemDict['Cost'] = cost[i]
        itemDict['Quantity'] = quantity[i]
        itemList.append(itemDict)
    return itemList


if __name__ == '__main__':
    app.run()

