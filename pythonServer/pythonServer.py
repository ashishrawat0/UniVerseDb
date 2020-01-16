from flask import Flask, request,jsonify, render_template
from flask_cors import CORS, cross_origin
import pandas as pd
import u2py
import os

app = Flask(__name__)
CORS(app)


@app.route('/api/U2data',methods=['POST'])
def savedata():
	theArray = u2py.DynArray()
	excel_file = request.files['file']
	filePath = os.path.join(os.path.dirname(os.path.abspath(__file__)),excel_file.filename)
	recordname = request.form['recordname']
	filename = request.form['filename']
	f = u2py.File(filename)
	val = 0
	data = pd.read_excel(open(filePath,'rb'),sheet_name='Sheet1')
	for i,j in data.iterrows():
		theArray.insert(val,0,0,j['empname'])
		val+=1
	f.write(recordname,theArray)
	f.close()
	return {'id':1}


@app.route('/api/U2data',methods=['GET'])
def readFromU2():
	data=[]
	filename = request.args.get('filename')
	record=request.args.get('recordname')
	try:
		f=u2py.File(filename)
	except u2py.U2Error as e:
		return {'status':404,'msg':"File Not Found"}
	theArray=u2py.DynArray()
	try:
		data=f.read(record)
	except u2py.U2Error as e:
		return {'status':404,'msg':"Record Not Found"}
	data=tuple(data)
	print(theArray)
	return{"data":data},201
if __name__ == '__main__':
	app.run()


