from typing import List
from pydantic import BaseModel
import re

class VehicleRecommendation(BaseModel):
	id: int
	brand: str
	model: str
	price: str
	engine: str
	fuelConsumption: str

def parse_brand_model(brand_model_str: str):
	"""
	Parse 'Arora CR250' into brand='Arora' and model='CR250'
	"""
	if not brand_model_str:
		return "", ""
	
	parts = brand_model_str.strip().split(None, 1)  # Split on first whitespace
	if len(parts) == 2:
		return parts[0], parts[1]
	elif len(parts) == 1:
		return parts[0], ""
	return "", ""

def normalize_type(type_str: str) -> str:
	"""
	Normalize motorcycle type for comparison.
	"""
	if not type_str:
		return ""
	return type_str.lower().strip()

def process_motorcycle_query(budget: str, vehicle_subtype: str, tables_data: dict) -> List[dict]:
	"""
	Filter motorcycles based on budget and subtype.
	Return up to 3 recommendations.
	
	Args:
		budget: Budget segment like "100,000 – 250,000 TL"
		vehicle_subtype: Type like 'naked', 'cruiser', 'sport', etc.
		tables_data: Structured data from PDF tables
	
	Returns:
		List of up to 3 motorcycle recommendations
	"""
	
	# Step 1: Filter by budget segment
	if budget not in tables_data:
		return []
	
	motorcycles_in_budget = tables_data[budget]
	
	if not motorcycles_in_budget:
		return []
	
	# Step 2: Filter by vehicle subtype
	normalized_subtype = normalize_type(vehicle_subtype)
	filtered_motorcycles = []
	
	for motorcycle in motorcycles_in_budget:
		motorcycle_type = normalize_type(motorcycle.get("type", ""))
		
		# Check if the motorcycle type matches the requested subtype
		if normalized_subtype in motorcycle_type or motorcycle_type in normalized_subtype:
			filtered_motorcycles.append(motorcycle)
	
	# If no exact matches, return empty (as per requirements - don't look at other types)
	if not filtered_motorcycles:
		return []
	
	# Step 3: Prepare recommendations (max 3)
	recommendations = []
	
	for idx, motorcycle in enumerate(filtered_motorcycles[:3], start=1):
		brand, model = parse_brand_model(motorcycle.get("brand_model", ""))
		
		recommendation = {
			"id": idx,
			"brand": brand,
			"model": model,
			"price": motorcycle.get("price", "N/A"),
			"engine": motorcycle.get("engine", "N/A"),
			"fuelConsumption": motorcycle.get("fuel", "N/A")
		}
		
		recommendations.append(recommendation)
	
	return recommendations