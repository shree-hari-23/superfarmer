from mcp.server.fastmcp import FastMCP
from config import execute_fluxbase_sql
import json

# Create the FastMCP server
mcp = FastMCP("FarmerProfile")

@mcp.tool()
def get_farmer_profile(farmer_id: int) -> str:
    """Fetch the farmer's full profile (name, land_size, location, water_availability, farming_goals) from the database."""
    try:
        p_res = execute_fluxbase_sql(f"SELECT * FROM farmer_profile WHERE farmer_id={farmer_id}")
        if p_res.get('rows'):
            return json.dumps(p_res['rows'][0])
        else:
            return json.dumps({
                "water_availability": "High",
                "farming_goals": "Standard yield",
                "error": "Farmer not found, using defaults"
            })
    except Exception as e:
        return json.dumps({
            "water_availability": "High",
            "farming_goals": "Standard yield",
            "error": str(e)
        })

if __name__ == "__main__":
    mcp.run(transport='stdio')
