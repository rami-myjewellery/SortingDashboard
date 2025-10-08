from typing import Dict, Any

async def extract_fma_metrics(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts metrics specific to the FMA job type."""
    return {
        "comment": job_data.get("comment", ""),  # Extract the comment
        "category": job_data.get("category", ""),  # Extract the category
        "employee_code": job_data.get("EMPLOYEE_CODE", ""),  # Extract employee code
        "total_cartons": job_data.get("LINE_COUNT", 0),  # Total cartons processed
        "total_handling_units": job_data.get("HANDLING_UNIT_COUNT", 0),  # Number of handling units
        "net_weight": job_data.get("NET_WEIGHT_DURATION", 0),  # Total net weight
        "gross_weight": job_data.get("GROSS_WEIGHT_DURATION", 0),  # Total gross weight
        "volume": job_data.get("VOLUME_DURATION", 0),  # Volume of stored items
        "duration_seconds": job_data.get("DURATION_SECONDS", 0),  # Total duration of job
    }


async def extract_monopicking_metrics(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts metrics specific to the MonoPicking job type."""

    # Ensure that 'DURATION_SECONDS' and 'LINE_COUNT' are valid numbers, otherwise set them to default values.
    duration_seconds = job_data.get("DURATION_SECONDS", 0)
    line_count = job_data.get("LINE_COUNT", 1)  # Default to 1 to avoid division by zero.

    # If either value is None or not a valid number, handle accordingly
    if duration_seconds is None or not isinstance(duration_seconds, (int, float)):
        duration_seconds = 0  # Default to 0 if invalid

    if line_count is None or not isinstance(line_count, (int, float)):
        line_count = 1  # Default to 1 if invalid

    # Calculate picking speed, avoid division by zero
    picking_speed = duration_seconds / line_count if line_count != 0 else 0

    return {
        "comment": job_data.get("comment", ""),  # Extract the comment
        "category": job_data.get("category", ""),  # Extract the category
        "employee_code": job_data.get("EMPLOYEE_CODE", ""),  # Extract employee code
        "total_items_processed": job_data.get("LINE_COUNT", 0),  # Number of items processed
        "pick_duration": duration_seconds,  # Time spent picking items
        "picking_speed": picking_speed,  # Time per item picked
        "total_cartons_picked": job_data.get("CARTON_COUNT", 0),  # Cartons picked
        "total_handling_units": job_data.get("HANDLING_UNIT_COUNT", 0),  # Handling units involved
    }


async def extract_inbound_and_bulk_metrics(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts metrics specific to the InboundAndBulk job type."""
    return {
        "comment": job_data.get("comment", ""),  # Extract the comment
        "category": job_data.get("category", ""),  # Extract the category
        "employee_code": job_data.get("EMPLOYEE_CODE", ""),  # Extract employee code
        "total_units_processed": job_data.get("LINE_COUNT", 0),  # Units processed
        "inbound_duration": job_data.get("DURATION_SECONDS", 0),  # Time spent in inbound processing
        "bulk_processing_time": job_data.get("QTY_LEVEL_1_DURATION", 0),  # Time for bulk processing
        "volume": job_data.get("VOLUME_DURATION", 0),  # Volume of processed items
        "weight": job_data.get("NET_WEIGHT_DURATION", 0),  # Weight of processed items
    }

async def extract_returns_metrics(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts metrics specific to the Returns job type."""
    return {
        "comment": job_data.get("comment", ""),  # Extract the comment
        "category": job_data.get("category", ""),  # Extract the category
        "employee_code": job_data.get("EMPLOYEE_CODE", ""),  # Extract employee code
        "total_returns": job_data.get("LINE_COUNT", 0),  # Number of items returned
        "return_duration": job_data.get("DURATION_SECONDS", 0),  # Time spent processing returns
        "return_weight": job_data.get("NET_WEIGHT_DURATION", 0),  # Weight of returned items
        "return_volume": job_data.get("VOLUME_DURATION", 0),  # Volume of returned items
        "return_receipts": job_data.get("comment", "").lower() == "return receipts",  # Check for return receipts
    }

async def extract_errorlanes_metrics(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts metrics specific to the ErrorLanes job type."""
    return {
        "comment": job_data.get("comment", ""),  # Extract the comment
        "category": job_data.get("category", ""),  # Extract the category
        "employee_code": job_data.get("EMPLOYEE_CODE", ""),  # Extract employee code
        "error_actions": job_data.get("LINE_COUNT", 0),  # Number of error actions processed
        "error_duration": job_data.get("DURATION_SECONDS", 0),  # Time spent on error lanes
        "error_weight": job_data.get("NET_WEIGHT_DURATION", 0),  # Weight related to error lanes
        "error_volume": job_data.get("VOLUME_DURATION", 0),  # Volume related to error lanes
        "error_handling_units": job_data.get("HANDLING_UNIT_COUNT", 0),  # Handling units in error lanes
    }
