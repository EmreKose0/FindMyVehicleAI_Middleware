import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
import io

app = FastAPI()

# Global variable to store Excel data
excel_data = None

class VehicleQuery(BaseModel):
    vehicleType: str  # 'motorcycle' or 'car'
    budget: str  # "Under 100,000 TL", "100,000 – 250,000 TL", etc.
    vehicleSubtype: str  # 'naked', 'cruiser', 'sport', etc.

class VehicleRecommendation(BaseModel):
    id: int
    brand: str
    model: str
    price: str
    engine: str
    fuelConsumption: str

@app.get("/")
def root():
    return {
        "message": "RAG Service is Running 🚀",
        "status": "Excel loaded" if excel_data else "Waiting for Excel upload"
    }

@app.post("/upload_excel")
async def upload_excel(file: UploadFile = File(...)):
    """
    Upload Excel file with motorcycle data.
    Expected structure: 6 sheets for each budget segment.
    Each sheet should have columns: Brand, Model, Type, Engine, Fuel, Price
    """
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
        
        return {
            "message": "Excel loaded successfully",
            "total_sheets": len(excel_data),
            "total_motorcycles": total_motorcycles,
            "sheets": sheet_summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error loading Excel: {str(e)}")

@app.post("/query", response_model=dict)
async def query_motorcycles(request: VehicleQuery):
    """
    Query motorcycles based on budget and vehicle subtype.
    Returns up to 3 recommendations.
    """
    global excel_data
    
    if excel_data is None:
        raise HTTPException(status_code=400, detail="Excel not loaded. Please upload Excel first using /upload_excel")
    
    sheet_name = request.budget
    
    if sheet_name not in excel_data:
        raise HTTPException(status_code=404, detail=f"Budget segment '{request.budget}' not found. Available: {list(excel_data.keys())}")
    
    df = excel_data[sheet_name]
    
    # Find the Type column
    type_column = None
    for col in df.columns:
        if 'type' in col.lower():
            type_column = col
            break
    
    if not type_column:
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
        # Get Brand and Model directly from columns
        brand = str(row.get('Brand', 'N/A')).strip()
        model = str(row.get('Model', 'N/A')).strip()
        
        # Handle NaN values
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
    """
    Get all available motorcycle types for a specific budget segment.
    """
    global excel_data
    
    if excel_data is None:
        raise HTTPException(status_code=400, detail="Excel not loaded")
    
    sheet_name = budget
    
    if sheet_name not in excel_data:
        raise HTTPException(status_code=404, detail=f"Budget segment '{budget}' not found")
    
    df = excel_data[sheet_name]
    
    # Find type column
    type_column = None
    for col in df.columns:
        if 'type' in col.lower():
            type_column = col
            break
    
    if not type_column:
        return {
            "budget": budget,
            "available_types": [],
            "message": f"Type column not found. Available columns: {df.columns.tolist()}"
        }
    
    types = df[type_column].dropna().unique().tolist()
    
    return {
        "budget": budget,
        "available_types": types,
        "total_motorcycles": len(df)
    }