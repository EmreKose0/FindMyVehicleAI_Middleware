import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
import io

app = FastAPI()

# Global variable to store Excel data
excel_data = None

class VehicleQuery(BaseModel):
    vehicleType: str
    budget: str
    vehicleSubtype: str

class VehicleRecommendation(BaseModel):
    id: int
    brand: str
    model: str
    price: str
    engine: str
    fuelConsumption: str

@app.get("/")
def root():
    print("📍 GET / - Root endpoint called")
    return {
        "message": "RAG Service is Running 🚀",
        "status": "Excel loaded" if excel_data else "Waiting for Excel upload"
    }

@app.post("/upload_excel")
async def upload_excel(file: UploadFile = File(...)):
    print(f"\n📤 POST /upload_excel - File: {file.filename}")
    global excel_data
    
    try:
        contents = await file.read()
        excel_data = pd.read_excel(io.BytesIO(contents), sheet_name=None, engine='openpyxl')
        
        total_motorcycles = 0
        sheet_summary = {}
        
        for sheet_name, df in excel_data.items():
            df.columns = df.columns.str.strip()
            excel_data[sheet_name] = df
            count = len(df)
            total_motorcycles += count
            sheet_summary[sheet_name] = count
        
        print(f"✅ Excel loaded: {total_motorcycles} motorcycles in {len(excel_data)} sheets")
        
        return {
            "message": "Excel loaded successfully",
            "total_sheets": len(excel_data),
            "total_motorcycles": total_motorcycles,
            "sheets": sheet_summary
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error loading Excel: {str(e)}")

@app.post("/query", response_model=dict)
async def query_motorcycles(request: VehicleQuery):
    print(f"\n🔍 POST /query")
    print(f"   Vehicle Type: {request.vehicleType}")
    print(f"   Budget: {request.budget}")
    print(f"   Subtype: {request.vehicleSubtype}")
    
    global excel_data
    
    if excel_data is None:
        print("❌ Excel not loaded")
        raise HTTPException(status_code=400, detail="Excel not loaded. Please upload Excel first using /upload_excel")
    
        # Flexible budget matching
    sheet_name = None
    requested_budget_normalized = request.budget.replace(" ", "").replace("–", "-").replace("—", "-").lower()
    
    for available_sheet in excel_data.keys():
        available_normalized = available_sheet.replace(" ", "").replace("–", "-").replace("—", "-").lower()
        if requested_budget_normalized == available_normalized:
            sheet_name = available_sheet
            break
    
    # If still not found, try fuzzy matching
    if not sheet_name:
        for available_sheet in excel_data.keys():
            # Check if the main numbers match
            if any(num in available_sheet for num in request.budget.replace(",", "").split()):
                sheet_name = available_sheet
                break
    
    if not sheet_name:
        print(f"❌ Budget segment not found: '{request.budget}'")
        print(f"   Available sheets: {list(excel_data.keys())}")
        raise HTTPException(
            status_code=404, 
            detail=f"Budget segment '{request.budget}' not found. Available: {list(excel_data.keys())}"
        )
    
    print(f"✅ Matched to sheet: '{sheet_name}'")
    
    df = excel_data[sheet_name]
    
    # Find the Type column
    type_column = None
    for col in df.columns:
        if 'type' in col.lower():
            type_column = col
            break
    
    if not type_column:
        print(f"❌ Type column not found")
        return {
            "query": {
                "vehicleType": request.vehicleType,
                "budget": request.budget,
                "vehicleSubtype": request.vehicleSubtype
            },
            "recommendations": [],
            "message": f"Type column not found. Available columns: {df.columns.tolist()}"
        }
    
    # Normalize type column for comparison
    df['Type_Lower'] = df[type_column].astype(str).str.lower().str.strip()
    requested_type = request.vehicleSubtype.lower().strip()
    
    # Filter motorcycles matching the type
    filtered_df = df[df['Type_Lower'] == requested_type]
    
    # If no exact match, try partial matching
    if filtered_df.empty:
        filtered_df = df[df['Type_Lower'].str.contains(requested_type, na=False)]
    
    # Get up to 3 results
    results = filtered_df.head(3)
    
    if results.empty:
        print(f"❌ No motorcycles found for type '{request.vehicleSubtype}'")
        return {
            "query": {
                "vehicleType": request.vehicleType,
                "budget": request.budget,
                "vehicleSubtype": request.vehicleSubtype
            },
            "recommendations": [],
            "message": f"No motorcycles found for type '{request.vehicleSubtype}' in budget '{request.budget}'"
        }
    
    # Format response
    recommendations = []
    
    for idx, row in results.iterrows():
        brand = str(row.get('Brand', 'N/A')).strip()
        model = str(row.get('Model', 'N/A')).strip()
        
        if brand == 'nan':
            brand = 'N/A'
        if model == 'nan':
            model = 'N/A'
        
        recommendation = {
            "id": len(recommendations) + 1,
            "brand": brand,
            "model": model,
            "price": str(row.get('Price', 'N/A')).strip(),
            "engine": str(row.get('Engine', 'N/A')).strip(),
            "fuelConsumption": str(row.get('Fuel', 'N/A')).strip()
        }
        
        recommendations.append(recommendation)
    
    print(f"✅ Found {len(recommendations)} recommendations")
    for rec in recommendations:
        print(f"   - {rec['brand']} {rec['model']}")
    
    return {
        "query": {
            "vehicleType": request.vehicleType,
            "budget": request.budget,
            "vehicleSubtype": request.vehicleSubtype
        },
        "recommendations": recommendations,
        "total_found": len(filtered_df)
    }

@app.get("/available_types/{budget}")
async def get_available_types(budget: str):
    print(f"\n📋 GET /available_types/{budget}")
    global excel_data
    
    if excel_data is None:
        print("❌ Excel not loaded")
        raise HTTPException(status_code=400, detail="Excel not loaded")
    
    sheet_name = budget
    
    if sheet_name not in excel_data:
        print(f"❌ Budget segment not found: {budget}")
        raise HTTPException(status_code=404, detail=f"Budget segment '{budget}' not found")
    
    df = excel_data[sheet_name]
    
    # Find type column
    type_column = None
    for col in df.columns:
        if 'type' in col.lower():
            type_column = col
            break
    
    if not type_column:
        print(f"❌ Type column not found")
        return {
            "budget": budget,
            "available_types": [],
            "message": f"Type column not found. Available columns: {df.columns.tolist()}"
        }
    
    types = df[type_column].dropna().unique().tolist()
    print(f"✅ Found {len(types)} types: {types}")
    
    return {
        "budget": budget,
        "available_types": types,
        "total_motorcycles": len(df)
    }