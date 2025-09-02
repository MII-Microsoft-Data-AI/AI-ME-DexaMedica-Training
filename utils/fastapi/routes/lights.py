"""
Light Control API Routes
========================

FastAPI routes for smart light control operations.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

# Import light plugin
from hands_off_agent.agents.light_agent.plugins.light import LightPlugin

# Initialize router
router = APIRouter(prefix="/lights", tags=["Lights"])

# Initialize light plugin
light_plugin = LightPlugin()

# Pydantic models
class Light(BaseModel):
    """Represents a light device with its current state"""
    id: int
    name: str
    is_on: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Table Lamp", 
                "is_on": False
            }
        }

class LightStateUpdate(BaseModel):
    """Model for updating a light's on/off state"""
    is_on: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_on": True
            }
        }

class LightAvailabilityResponse(BaseModel):
    """Response model for light availability check"""
    id: Optional[int]
    available: bool
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "available": True,
                "message": "Light 'Table Lamp' is available with ID 1"
            }
        }


@router.get("", 
         response_model=list[Light],
         summary="List All Lights",
         description="""
         Get a comprehensive list of all available light devices in the system.
         
         This endpoint returns all lights with their current state, including:
         - Unique identifier for each light
         - Human-readable name/description  
         - Current on/off status
         
         **Use Cases:**
         - Dashboard display of all lights
         - Initial system state polling
         - Inventory management
         - Status monitoring applications
         """,
         responses={
             200: {
                 "description": "Successfully retrieved all lights",
                 "content": {
                     "application/json": {
                         "example": [
                             {"id": 1, "name": "Table Lamp", "is_on": False},
                             {"id": 2, "name": "Porch light", "is_on": False},
                             {"id": 3, "name": "Chandelier", "is_on": True}
                         ]
                     }
                 }
             }
         })
async def get_all_lights():
    """
    Retrieve all available lights in the system with their current state.
    
    Returns a list of Light objects containing id, name, and current on/off status.
    This is equivalent to the light_list function from the LightPlugin.
    """
    try:
        lights_data = light_plugin.light_list()
        return [Light(**light) for light in lights_data]
    except Exception as e:
        logging.error(f"Error retrieving lights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve lights: {str(e)}")


@router.get("/search/{light_name}",
         response_model=LightAvailabilityResponse,
         summary="Search for Light by Name", 
         description="""
         Search for a specific light device by its name to check availability and get its ID.
         
         **Parameters:**
         - `light_name`: The exact name of the light to search for (case-sensitive)
         
         **Returns:**
         - Light ID if found
         - Availability status (true/false)  
         - Descriptive message
         
         **Use Cases:**
         - Validate light existence before control operations
         - Get light ID for subsequent API calls
         - User-friendly light selection by name
         - Integration with voice control systems
         
         **Examples:**
         - Search for "Table Lamp" → Returns ID 1 if available
         - Search for "NonExistentLight" → Returns availability: false
         """,
         responses={
             200: {
                 "description": "Light search completed",
                 "content": {
                     "application/json": {
                         "examples": {
                             "found": {
                                 "summary": "Light Found",
                                 "value": {
                                     "id": 1,
                                     "available": True,
                                     "message": "Light 'Table Lamp' is available with ID 1"
                                 }
                             },
                             "not_found": {
                                 "summary": "Light Not Found", 
                                 "value": {
                                     "id": None,
                                     "available": False,
                                     "message": "Light 'Unknown Light' not found"
                                 }
                             }
                         }
                     }
                 }
             }
         })
async def search_light_by_name(light_name: str):
    """
    Search for a light by name and return its availability and ID.
    
    This endpoint helps determine if a specific light exists in the system
    and provides its ID for further operations.
    """
    try:
        light_id = light_plugin.light_available(light_name)
        
        if light_id is not None:
            return LightAvailabilityResponse(
                id=light_id,
                available=True,
                message=f"Light '{light_name}' is available with ID {light_id}"
            )
        else:
            return LightAvailabilityResponse(
                id=None,
                available=False,
                message=f"Light '{light_name}' not found"
            )
            
    except Exception as e:
        logging.error(f"Error searching for light '{light_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search for light: {str(e)}")


@router.get("/{light_id}",
         response_model=Light,
         summary="Get Light State by ID",
         description="""
         Retrieve detailed information about a specific light device using its unique identifier.
         
         **Parameters:**
         - `light_id`: Unique integer identifier of the light (e.g., 1, 2, 3...)
         
         **Returns:**
         Complete light information including:
         - ID: Unique identifier
         - Name: Human-readable light name
         - is_on: Current on/off state (boolean)
         
         **Use Cases:**
         - Check current state before toggling
         - Status monitoring and reporting
         - Individual light management
         - Integration with home automation systems
         
         **Error Handling:**
         - Returns 404 if light ID doesn't exist
         - Returns 422 for invalid ID format
         """,
         responses={
             200: {
                 "description": "Successfully retrieved light information",
                 "content": {
                     "application/json": {
                         "example": {"id": 1, "name": "Table Lamp", "is_on": False}
                     }
                 }
             },
             404: {
                 "description": "Light not found",
                 "content": {
                     "application/json": {
                         "example": {"detail": "Light with ID 99 not found"}
                     }
                 }
             },
             422: {
                 "description": "Invalid light ID format",
                 "content": {
                     "application/json": {
                         "example": {"detail": "Light ID must be a valid integer"}
                     }
                 }
             }
         })
async def get_light_state(light_id: int):
    """
    Get the current state and information of a specific light by its ID.
    
    This endpoint provides detailed information about a single light,
    including its current on/off state and descriptive name.
    """
    try:
        light_data = light_plugin.get_state(light_id)
        
        if light_data is None:
            raise HTTPException(status_code=404, detail=f"Light with ID {light_id} not found")
            
        return Light(**light_data)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logging.error(f"Error getting light state for ID {light_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get light state: {str(e)}")


@router.put("/{light_id}/state",
         response_model=Light,
         summary="Update Light State",
         description="""
         Control a light by changing its on/off state using its unique identifier.
         
         **Parameters:**
         - `light_id`: Unique integer identifier of the light to control
         - `is_on`: Desired state (true = turn on, false = turn off)
         
         **Request Body:**
         ```json
         {
           "is_on": true
         }
         ```
         
         **Returns:**
         Updated light information with the new state
         
         **Use Cases:**
         - Turn lights on/off programmatically
         - Home automation integration
         - Smart scheduling systems
         - Mobile app controls
         - Voice assistant integration
         
         **Features:**
         - Immediate state change
         - Idempotent operation (safe to call multiple times)
         - Returns updated state for confirmation
         
         **Error Handling:**
         - Returns 404 if light ID doesn't exist
         - Returns 422 for invalid request format
         """,
         responses={
             200: {
                 "description": "Light state successfully updated",
                 "content": {
                     "application/json": {
                         "example": {"id": 1, "name": "Table Lamp", "is_on": True}
                     }
                 }
             },
             404: {
                 "description": "Light not found",
                 "content": {
                     "application/json": {
                         "example": {"detail": "Light with ID 99 not found"}
                     }
                 }
             },
             422: {
                 "description": "Invalid request format",
                 "content": {
                     "application/json": {
                         "example": {"detail": "Request validation error"}
                     }
                 }
             }
         })
async def update_light_state(light_id: int, state_update: LightStateUpdate):
    """
    Update the on/off state of a specific light.
    
    This endpoint allows you to turn a light on or off by providing
    the light ID and the desired state.
    """
    try:
        # First check if light exists
        current_light = light_plugin.get_state(light_id)
        if current_light is None:
            raise HTTPException(status_code=404, detail=f"Light with ID {light_id} not found")
        
        # Update the light state
        updated_light = light_plugin.change_state(light_id, state_update.is_on)
        
        if updated_light is None:
            raise HTTPException(status_code=404, detail=f"Failed to update light with ID {light_id}")
            
        return Light(**updated_light)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logging.error(f"Error updating light state for ID {light_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update light state: {str(e)}")


@router.post("/{light_id}/toggle",
          response_model=Light,
          summary="Toggle Light State",
          description="""
          Toggle a light's current state - if it's on, turn it off; if it's off, turn it on.
          
          **Parameters:**
          - `light_id`: Unique integer identifier of the light to toggle
          
          **Returns:**
          Updated light information with the new toggled state
          
          **Use Cases:**
          - Quick on/off switching without knowing current state
          - Smart switch implementations
          - Convenient toggle functionality for UIs
          - Voice commands like "toggle living room light"
          
          **Behavior:**
          - Current state ON → Changes to OFF
          - Current state OFF → Changes to ON
          - Atomic operation ensuring state consistency
          
          **Error Handling:**
          - Returns 404 if light ID doesn't exist
          - Returns 500 for system errors
          """,
          responses={
              200: {
                  "description": "Light state successfully toggled",
                  "content": {
                      "application/json": {
                          "example": {"id": 1, "name": "Table Lamp", "is_on": True}
                      }
                  }
              },
              404: {
                  "description": "Light not found",
                  "content": {
                      "application/json": {
                          "example": {"detail": "Light with ID 99 not found"}
                      }
                  }
              }
          })
async def toggle_light(light_id: int):
    """
    Toggle the current state of a light (on→off, off→on).
    
    This is a convenience endpoint that automatically switches the light
    to the opposite of its current state.
    """
    try:
        # Get current state
        current_light = light_plugin.get_state(light_id)
        if current_light is None:
            raise HTTPException(status_code=404, detail=f"Light with ID {light_id} not found")
        
        # Toggle the state
        new_state = not current_light["is_on"]
        updated_light = light_plugin.change_state(light_id, new_state)
        
        if updated_light is None:
            raise HTTPException(status_code=404, detail=f"Failed to toggle light with ID {light_id}")
            
        return Light(**updated_light)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logging.error(f"Error toggling light state for ID {light_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to toggle light state: {str(e)}")


@router.post("/all/on",
          response_model=list[Light],
          summary="Turn On All Lights",
          description="""
          Turn on all lights in the system simultaneously.
          
          **Returns:**
          List of all lights with their updated states (all should be on)
          
          **Use Cases:**
          - Emergency lighting activation
          - "All lights on" scenes
          - Security system integration
          - Bulk operations for convenience
          
          **Features:**
          - Batch operation for efficiency
          - Returns complete system state after operation
          - Idempotent (lights already on remain on)
          """,
          responses={
              200: {
                  "description": "All lights successfully turned on",
                  "content": {
                      "application/json": {
                          "example": [
                              {"id": 1, "name": "Table Lamp", "is_on": True},
                              {"id": 2, "name": "Porch light", "is_on": True},
                              {"id": 3, "name": "Chandelier", "is_on": True}
                          ]
                      }
                  }
              }
          })
async def turn_on_all_lights():
    """
    Turn on all lights in the system.
    
    This is a bulk operation that ensures all lights are turned on
    and returns the updated state of all lights.
    """
    try:
        lights = light_plugin.light_list()
        updated_lights = []
        
        for light in lights:
            updated_light = light_plugin.change_state(light["id"], True)
            if updated_light:
                updated_lights.append(Light(**updated_light))
        
        return updated_lights
        
    except Exception as e:
        logging.error(f"Error turning on all lights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to turn on all lights: {str(e)}")


@router.post("/all/off",
          response_model=list[Light],
          summary="Turn Off All Lights", 
          description="""
          Turn off all lights in the system simultaneously.
          
          **Returns:**
          List of all lights with their updated states (all should be off)
          
          **Use Cases:**
          - Energy saving "all off" command
          - End-of-day shutdown routines
          - Security system integration
          - Emergency power conservation
          - Vacation/away mode activation
          
          **Features:**
          - Batch operation for efficiency
          - Returns complete system state after operation
          - Idempotent (lights already off remain off)
          """,
          responses={
              200: {
                  "description": "All lights successfully turned off",
                  "content": {
                      "application/json": {
                          "example": [
                              {"id": 1, "name": "Table Lamp", "is_on": False},
                              {"id": 2, "name": "Porch light", "is_on": False},
                              {"id": 3, "name": "Chandelier", "is_on": False}
                          ]
                      }
                  }
              }
          })
async def turn_off_all_lights():
    """
    Turn off all lights in the system.
    
    This is a bulk operation that ensures all lights are turned off
    and returns the updated state of all lights.
    """
    try:
        lights = light_plugin.light_list()
        updated_lights = []
        
        for light in lights:
            updated_light = light_plugin.change_state(light["id"], False)
            if updated_light:
                updated_lights.append(Light(**updated_light))
        
        return updated_lights
        
    except Exception as e:
        logging.error(f"Error turning off all lights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to turn off all lights: {str(e)}")


@router.get("/stats",
         summary="Get Light Statistics",
         description="""
         Get statistical information about all lights in the system.
         
         **Returns:**
         Comprehensive statistics including:
         - Total number of lights
         - Number of lights currently on
         - Number of lights currently off  
         - Percentage of lights that are on
         - List of lights that are currently on
         - List of lights that are currently off
         
         **Use Cases:**
         - Dashboard summary displays
         - Energy usage monitoring
         - System status overview
         - Analytics and reporting
         - Smart home optimization
         """,
         responses={
             200: {
                 "description": "Light statistics successfully retrieved",
                 "content": {
                     "application/json": {
                         "example": {
                             "total_lights": 5,
                             "lights_on": 2,
                             "lights_off": 3,
                             "percentage_on": 40.0,
                             "on_lights": ["Chandelier", "Desk Lamp"],
                             "off_lights": ["Table Lamp", "Porch light", "Floor Lamp"]
                         }
                     }
                 }
             }
         })
async def get_light_statistics():
    """
    Get comprehensive statistics about the lighting system.
    
    Provides an overview of the current state of all lights,
    including counts, percentages, and categorized lists.
    """
    try:
        lights = light_plugin.light_list()
        
        total_lights = len(lights)
        lights_on = sum(1 for light in lights if light["is_on"])
        lights_off = total_lights - lights_on
        percentage_on = (lights_on / total_lights * 100) if total_lights > 0 else 0
        
        on_lights = [light["name"] for light in lights if light["is_on"]]
        off_lights = [light["name"] for light in lights if not light["is_on"]]
        
        return {
            "total_lights": total_lights,
            "lights_on": lights_on,
            "lights_off": lights_off,
            "percentage_on": round(percentage_on, 1),
            "on_lights": on_lights,
            "off_lights": off_lights
        }
        
    except Exception as e:
        logging.error(f"Error getting light statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get light statistics: {str(e)}")
