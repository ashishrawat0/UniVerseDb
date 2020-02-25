import { Component, OnInit, Pipe, PipeTransform, ViewChild, ElementRef, Inject } from '@angular/core';
import { FormControl, FormGroup } from '@angular/forms';
import { SaveDataService } from '../service/save-data.service';
import {DOCUMENT } from '@angular/common'


@Component({
  selector: 'stepper',
  templateUrl: './stepper.component.html',
  styleUrls: ['./stepper.component.css']
})
export class StepperComponent implements OnInit {

  recordIDs: String[]

  recordData: {}

  totalPrice: number = 0.00
  unitPrice: number

  unitPrice : number = 0.00

  @ViewChild('selectValue',{ static: false}) selectValue: ElementRef;

  constructor(private saveData: SaveDataService,@Inject(DOCUMENT) document) { }

  firstFormGroup = new FormGroup({
    item: new FormControl(),
    quantity: new FormControl('')

  })

  get item() { return this.firstFormGroup.get('item') }

  get quantity() { return this.firstFormGroup.get('quantity') }

  secondFormGroup = new FormGroup({
    companyName: new FormControl(''),
    contact: new FormControl(''),
    address: new FormControl(''),
    phoneno: new FormControl('')
  })

  get companyName() { return this.secondFormGroup.get('companyName') }

  get contact() { return this.secondFormGroup.get('contact') }

  get address() { return this.secondFormGroup.get('address') }

  get phoneno() { return this.secondFormGroup.get('phoneno') }

  ngOnInit() {
    this.saveData.readItem()
      .subscribe((res: any) => {
        this.recordData = res.table
        this.recordIDs = Object.keys(res.table)
        //console.log(this.unitPrice=this.recordData[this.item.value][0])
        console.log(this.recordIDs);
        console.log(this.recordData);
        console.log(this.recordData[45623412]);

      })
  }

<<<<<<< HEAD
  submitData(firstFormGroup, secondFormGroup) {
    this.saveData.saveItemData(firstFormGroup.value, secondFormGroup.value)
      .subscribe(res => {

      })
  }
  setUnitprice() {
    this.unitPrice = this.recordData[this.item.value][1]
  }
  calculateTotalPrice(unitPrice, quantity) {
    console.log(this.item.value);
    console.log(this.recordData[this.item.value][0]);
    console.log(this.recordData[this.item.value][1]);
    this.unitPrice = this.recordData[this.item.value][1]
    this.totalPrice = this.recordData[this.item.value][1] * quantity
=======
  submitData(firstFormGroup, secondFormGroup){
    let splittedItem = firstFormGroup.value.item.split(',')
    firstFormGroup.value.item = splittedItem[0]
    firstFormGroup.value.price = splittedItem[1]
    this.saveData.saveItemData(firstFormGroup.value,secondFormGroup.value)
    .subscribe(res=>{
      
    })
  }

  calculateTotalPrice(quantity){
    this.totalPrice = this.unitPrice * quantity
  }

  onChange(){
    this.unitPrice = this.recordData[this.item.value][1]
>>>>>>> 0ee19a57bf762c5f7c58be5d05abd7c3bb9ce786
  }

}