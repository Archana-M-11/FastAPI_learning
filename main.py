from fastapi import FastAPI,Path,HTTPException,Query
import json
from fastapi.responses import JSONResponse
from typing import Annotated,Literal,Optional
from pydantic import BaseModel,Field,computed_field

app=FastAPI()

class Patient(BaseModel):
    id:Annotated[str,Field(...,description='ID od patient',examples=['P001'])]
    name:Annotated[str,Field(...,description='name of the patient')]
    city:Annotated[str,Field(...,description='city of the patient')]
    age:Annotated[int,Field(...,gt=0,le=120,description='age of the patient')]
    gender:Annotated[Literal['male','female','others'],Field(...,description='gender of the patient')]
    height:Annotated[float,Field(...,gt=0,description='height of the patient')]
    weight:Annotated[float,Field(...,gt=0,description='weight of the patient')]

    @computed_field
    @property
    def bmi(self)->float:
        bmi = round(self.weight / (self.height ** 2), 2)
        return bmi
    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return 'Underweight'
        elif self.bmi < 25:
            return 'Normal'
        elif self.bmi < 30:
            return 'Overweight'
        else:
            return 'Obese'
        
class PatientUpdate(BaseModel):
    name: Optional[str] = Field(default=None, description='Name of the patient')
    city: Optional[str] = Field(default=None, description='City of the patient')
    age: Optional[int] = Field(default=None, gt=0, le=120, description='Age of the patient')
    gender: Optional[Literal['male', 'female', 'others']] = Field(default=None, description='Gender of the patient')
    height: Optional[float] = Field(default=None, gt=0, description='Height in metres')
    weight: Optional[float] = Field(default=None, gt=0, description='Weight in kg')

# helper functions
def load_data():
    with open('patients.json','r') as f:
        data=json.load(f)
    return data
def save_data(data):
    with open('patients.json','w') as f:
        json.dump(data,f)

# endpoints
@app.get('/')
def home():
    return{
        'message':'A full function API for patient data'
    }

@app.get('/view')
def view():
    data=load_data()
    return data

# path parameter
@app.get('/patients/{patient_id}')
def get_patient(patient_id :str = Path(...,description='id of the patient in db',examples='P001')):
    data=load_data()
    if patient_id in data:
        return data[patient_id]
    raise HTTPException(status_code=404,detail='Patient not found')

# query parameter
@app.get('/sort')
def sort_patient(sort_by:str=Query(...,description='sort on the basis od the height, weight, bmi'),order:str=Query('asc',description='sort in asc or desc order')):
    valid_fields=['height','weight','bmi']
    if sort_by not in valid_fields:
        raise HTTPException(status_code=400,detail=f'invalid field select from {valid_fields}')
    if order not in ['asc','desc']:
        raise HTTPException(status_code=400 ,detail='choose asc or desc')
    data=load_data()
    sort_order=True if order=='desc' else False
    sorted_data=sorted(data.values(),key=lambda x: x.get(sort_by,0),reverse=sort_order)
    return sorted_data

@app.post('/create')
def creat_patient(patient:Patient):
    # load data
    data=load_data()
    if patient.id in data:
        raise HTTPException(status_code=400,detail='patient already exist')
    # new data
    data[patient.id]=patient.model_dump(exclude=['id'])
    # save data
    save_data(data)
    return JSONResponse(status_code=201,content={'message':'patient created'})

@app.put('/update/{patient_id}')
def update_patient(patient_id: str, patient_update: PatientUpdate):
    data = load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404, detail='Patient not found')
    existing_patient_info = data[patient_id]
    updated_patient_info = patient_update.model_dump(exclude_unset=True)
    existing_patient_info.update(updated_patient_info)
    existing_patient_info['id'] = patient_id
    patient_obj = Patient(**existing_patient_info)
    data[patient_id] = patient_obj.model_dump(exclude={'id'})
    save_data(data)
    return {"message": "Patient data updated successfully"}

@app.delete('/delete/{patient_id}')
def patient_delete(patient_id:str= Path(...,description='id of the patient in db',example='P001')):
    data=load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404,detail='patient not found')
    del data[patient_id]
    save_data(data)
    return JSONResponse(
        status_code=200,
        content={'message':'patient deleted'}
    )