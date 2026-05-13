from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from typing import Optional
from enum import Enum

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class PaymentBase(BaseModel):
    order_id: int
    amount: Decimal

class PaymentCreate(PaymentBase):
    payment_method_id: str  # от Stripe

class PaymentResponse(PaymentBase):
    id: int
    status: PaymentStatus
    stripe_payment_intent_id: Optional[str] = None
    client_secret: Optional[str] = None  # для Stripe
    created_at: datetime

    class Config:
        from_attributes = True