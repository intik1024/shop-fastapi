from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from typing import List
from enum import Enum

class OrderStatus(str, Enum):
    CREATED = "created"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class OrderItemBase(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=1)

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemResponse(OrderItemBase):
    id: int
    product_name: str
    price_at_time: Decimal

    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    delivery_address: str = Field(..., min_length=5)

class OrderCreate(OrderBase):
    items: List[OrderItemCreate]

class OrderUpdateStatus(BaseModel):
    status: OrderStatus

class OrderResponse(OrderBase):
    id: int
    user_id: int
    total_price: Decimal
    status: OrderStatus
    created_at: datetime
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    id: int
    user_id: int
    total_price: Decimal
    status: OrderStatus
    created_at: datetime
    items_count: int

    class Config:
        from_attributes = True