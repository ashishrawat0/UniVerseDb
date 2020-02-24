from flask import Flask
from flask import request
import u2py
import xmltodict
import pprint
import json
from collections import OrderedDict
from flask_cors import CORS,cross_origin
app = Flask(__name__)
CORS(app)

def vendorDetailU2(vendorDetails,itemsId,recordID):
	vendorArray=u2py.DynArray()
	item=bytes("","utf-8")
	vendorFile=u2py.File('PO.VENDOR.MST');
	vendorArray.insert(1,0,0,vendorDetails['Company'])
	vendorArray.insert(2,0,0,vendorDetails['Contact'])
	vendorArray.insert(3,0,0,bytes(vendorDetails['Street'],"utf-8")+u2py.VM+bytes(vendorDetails['City'],"utf-8")+u2py.VM+bytes(vendorDetails['State'],"utf-8")+u2py.VM+bytes(vendorDetails['Zip'],"utf-8"))
	vendorArray.insert(4,0,0,vendorDetails['Phone'])
	for items in itemsId:
		item=item+bytes(items['items'],"utf-8")+u2py.VM
	vendorArray.insert(5,0,0,item[:-1])
	vendorFile.write(recordID,vendorArray)
@app.route('/api/itemData',methods=['GET'])
def readFromU2():
	cmd=u2py.run("LIST DATA PO.ITEM.MST DESC TOXML",capture=True)
	my_xml = cmd.strip()	
	ids={}
	cost=[]
	itemData=[]
	dictItems={}
	dataLength=len(xmltodict.parse(my_xml)['ROOT']['PO.ITEM.MST'])
	for i in range(dataLength):
		data = xmltodict.parse(my_xml)['ROOT']['PO.ITEM.MST'][i]
		ids=(data['@_ID'])
		itemData.append(data['@DESC'])
		dictItems[ids]=itemData
		itemData=[]
	return{"table": dictItems },200

@app.route('/api/vendorDetail',methods=['POST'])
def vendorDetails():
	print("yes")
	vendorData =request.get_json()
	itemsId=vendorData['itemId']['items'];
	vendorDetails=vendorData['vendorDetail'];
	vendorDetailU2(vendorDetails,itemsId,vendorData['recordID'])
	return{	'status':200,
		'message':"data saved",
		'data':vendorData
		}
@app.route('/api/vendorDetail',methods=['GET'])
def allVendors():
	ids={}
	cost=[]
	itemData=[]
	vendorDetail=[]
	dictItems={}
	itemId=[]
	cmd=u2py.run("LIST DATA PO.VENDOR.MST VEND.COMPANY VEND.NAME VEND.ADDRESS VEND.PHONE ITEM.IDS TOXML	",capture=True)
	my_xml=cmd.strip()
	data = xmltodict.parse(my_xml)['ROOT']['PO.VENDOR.MST']
	for i in range(len(data)):
		data = xmltodict.parse(my_xml)['ROOT']['PO.VENDOR.MST'][i]
		for j in data['ITEM.IDS_MV']:
			itemId.append(j['@ITEM.IDS'])	
			ids=data['@_ID']
		vendorDetail.append(data['@VEND.COMPANY'])
		vendorDetail.append(data['@VEND.NAME'])
		vendorDetail.append(data['@VEND.PHONE'])
		itemData.append(vendorDetail)
		itemData.append(itemId)
		dictItems[ids]=itemData
		itemData=[]
		itemId=[]
		vendorDetail=[]
	return{'status':200,
		'data':dictItems	
		}
if __name__ == '__main__':
	app.run()
