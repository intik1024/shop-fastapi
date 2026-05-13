from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

class CartItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_price: Decimal
    quantity: int
    added_at: datetime

class CartResponse(BaseModel):
    id: int
    user_id: int
    items: List[CartItemResponse] = []
    total_price: Decimal
    total_items: int
    created_at: datetime
    updated_at: Optional[datetime] = None