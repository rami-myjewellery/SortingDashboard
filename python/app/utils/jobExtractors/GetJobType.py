from typing import Dict

def get_job_type(comment: str) -> str:
    """
    Returns the job type category based on the comment.
    """
    # Updated mapping between comments and job categories
    COMMENT_TO_CATEGORY_MAPPING: Dict[str, str] = {
        'Truck moves': 'InboundAndBulk',
        'AMR Inbound': 'InboundAndBulk',
        'Preparation despatch packaging': 'MonoPicking',
        'Quality > Available stock': 'ErrorLanes', #VoorraadTasks - niet echt error
        'Receipt full pallets': 'InboundAndBulk',
        '601': {'category': 'Item/Quantity', 'comment': 'Receipt'}, #InboundAndBulk
        'Receipt': 'InboundAndBulk',
        'B2B try‑out and BTQ picking tasks': 'MonoPicking',
        'Multi‑SKU & marketplace try‑out tasks': 'MonoPicking',
        'B2B manual & label tasks': 'MonoPicking', # packing
        'Replenishment tasks (Geek+, AMR REA/EPT) and mono collection': 'MonoPicking', #Replenishment
        '700': {'category': 'Real-time', 'comment': 'Inventory > C zone'},#VoorraadTasks
        '701': {'category': 'Real-time', 'comment': 'Inventory > Bulk'},#VoorraadTasks
        '702': {'category': 'Real-time', 'comment': 'Inventory > Audit'},#VoorraadTasks
        'Mono flow despatch': 'MonoPicking',#packing - machine - misschien Sorting?
        'Put Away Returns': 'Returns',
        'Return MOVE': 'Returns',
        'Advent Despatch Packing': 'MonoPicking',
        'GEEK → PACK (packing Geek orders)': 'MonoPicking',
        'G71': {'category': 'Real-time', 'comment': 'Inventory > A zone'},#VoorraadTask
        'Perform actions on stock': 'ErrorLanes', #VoorraadTasks - resulteerd uit error
        'New item registration': 'InboundAndBulk',
        'Replenishment tasks (e.g., Repl REA/OPT/EPT) and mono collection': 'MonoPicking', #Replenishment
        'Replenishment (decons) and deco picking tasks': 'MonoPicking', #Replenishment
        'Picking tasks: single/multi SKU, retail, B2B and BTQ': 'MonoPicking',
        'Return receipts': 'Returns'
    }

    # Categorize moves (any comment containing '>' in it)
    if '>' in comment:
        if 'Inventory > A zone' in comment or 'Inventory > B zone' in comment:
            job_type = 'FMA'  # These are likely moves within a specific zone
        elif 'Inventory > Bulk' in comment:
            job_type = 'InboundAndBulk'  # Bulk related processing
        elif 'Quality > Available stock' in comment:
            job_type = 'ErrorLanes'  # Quality-related issues
        elif 'Inventory > Audit' in comment:
            job_type = 'ErrorLanes'  # Inventory audits likely fall under errors
        elif 'Inventory > C zone' in comment:
            job_type = 'ErrorLanes'  # Errors or stock discrepancies in this zone
        else:
            job_type = 'Unknown'  # For any other '>' comment that doesn't fit the above
    else:
        # Get the category based on the comment
        job_type = COMMENT_TO_CATEGORY_MAPPING.get(comment, 'Unknown')

    return job_type
