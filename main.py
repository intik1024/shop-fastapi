from fastapi import FastAPI, Depends, HTTPException, Form, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from models.database import SessionLocal, engine
from models import models
from models.models import Product, Cart, CartItem,User
from auth import get_current_user, hash_password, verify_password, create_access_token, SECRET_KEY, ALGORITHM
from schemas.User import UserCreate, UserResponse
from schemas.Product import ProductCreate, ProductUpdate, ProductResponse
from schemas.Order import OrderCreate, OrderResponse, OrderListResponse, OrderUpdateStatus
from typing import List
from decimal import Decimal
from datetime import datetime


models.Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_by_username(db: Session, username: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(404, f"User '{username}' not found")
    return user


def get_user_cart(db: Session, username: str):
    user = get_user_by_username(db, username)

    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if not cart:
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart

@app.post('/register', response_model=UserResponse)
def register_user(
        user: UserCreate,
        db: Session = Depends(get_db)
):
    existing = db.query(models.User).filter(
        or_(
            models.User.username == user.username,
            models.User.email == user.email
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="User with this username or email already exists"
        )

    hashed_password = hash_password(user.password)

    db_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        is_admin=False
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

@app.post('/login')
def login_user(
        username: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):

    user = db.query(models.User).filter(models.User.username == username).first()

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    access_token = create_access_token(data={'sub': user.username})

    return {
        'access_token': access_token,
        'token_type': 'bearer',
        'user_id': user.id,
        'username': user.username,
        'is_admin': user.is_admin
    }



@app.get('/users/me', response_model=UserResponse)
def get_current_user_info(
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):

    return current_user

@app.post('/products', response_model=ProductResponse)
def create_product(
        product: ProductCreate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):

    existing = db.query(Product).filter(Product.name == product.name).first()
    if existing:
        raise HTTPException(status_code=400, detail='Product with this name already exists')


    db_product = Product(
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock,
        user_id=current_user.id
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@app.get('/products', response_model=List[ProductResponse])
def get_products(
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        db: Session = Depends(get_db)
):
    products = db.query(Product).order_by(Product.created_at.desc()).offset(skip).limit(limit).all()


    for p in products:
        owner = db.query(models.User).filter(models.User.id == p.user_id).first()
        p.owner_username = owner.username if owner else None

    return products


@app.get('/products/{product_id}', response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')

    owner = db.query(models.User).filter(models.User.id == product.user_id).first()
    product.owner_username = owner.username if owner else None

    return product


@app.patch('/products/{product_id}', response_model=ProductResponse)
def update_product(
        product_id: int,
        product_update: ProductUpdate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail='Product not found')

    if db_product.user_id != current_user.id:
        raise HTTPException(status_code=403, detail='Not enough permission. Only the creator can edit this product')


    if product_update.name is not None:
        db_product.name = product_update.name
    if product_update.description is not None:
        db_product.description = product_update.description
    if product_update.price is not None:
        db_product.price = product_update.price
    if product_update.stock is not None:
        db_product.stock = product_update.stock

    db.commit()
    db.refresh(db_product)

    owner = db.query(models.User).filter(models.User.id == db_product.user_id).first()
    db_product.owner_username = owner.username if owner else None

    return db_product


@app.delete('/products/{product_id}')
def delete_product(
        product_id: int,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail='Product not found')

    if db_product.user_id != current_user.id:
        raise HTTPException(status_code=403, detail='Not enough permission. Only the creator can delete this product')

    db.delete(db_product)
    db.commit()
    return {'message': 'Product deleted successfully'}


@app.get("/cart/{username}")
def get_my_cart(
        username: str,
        db: Session = Depends(get_db)
):
    cart = get_user_cart(db, username)
    user = get_user_by_username(db, username)

    items_list = []
    total_price = Decimal('0')

    for item in cart.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            total_price += product.price * item.quantity
            items_list.append({
                "id": item.id,
                "product_id": item.product_id,
                "product_name": product.name,
                "product_price": product.price,
                "quantity": item.quantity,
                "added_at": item.added_at
            })

    return {
        "username": user.username,
        "items": items_list,
        "total_price": total_price,
        "total_items": len(items_list)
    }

@app.post("/cart/add/{product_id}")
def add_to_my_cart(
        product_id: int,
        quantity: int = 1,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "Product not found")

    if product.stock < quantity:
        raise HTTPException(400, f"Not enough stock. Available: {product.stock}")

    cart = get_user_cart(db, current_user.username)

    cart_item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_id == product_id
    ).first()

    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(
            cart_id=cart.id,
            product_id=product_id,
            quantity=quantity
        )
        db.add(cart_item)

    db.commit()

    return {
        "message": f"Added {quantity} x '{product.name}' to your cart",
        "product": product.name,
        "quantity": cart_item.quantity
    }

@app.delete("/cart/remove/{item_id}")
def remove_from_my_cart(
        item_id: int,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    cart = get_user_cart(db, current_user.username)

    cart_item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.cart_id == cart.id
    ).first()

    if not cart_item:
        raise HTTPException(404, "Item not found in your cart")

    db.delete(cart_item)
    db.commit()

    return {"message": "Item removed from your cart"}

@app.delete("/cart/clear")
def clear_my_cart(
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    cart = get_user_cart(db, current_user.username)

    deleted = db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()

    return {"message": f"Your cart cleared. Removed {deleted} items"}

@app.post('/orders', response_model=OrderResponse)
def create_order(
        order_data: OrderCreate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    if not order_data.items:
        raise HTTPException(status_code=400, detail='No items in order')

    total_price = Decimal('0')
    order_items = []

    for item_data in order_data.items:
        product = db.query(Product).filter(Product.id == item_data.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f'Product {item_data.product_id} not found')

        if product.stock < item_data.quantity:
            raise HTTPException(
                status_code=400,
                detail=f'Not enough stock for product: {product.name}. Available: {product.stock}'
            )

        product.stock -= item_data.quantity
        total_price += product.price * item_data.quantity

        order_items.append({
            "product_id": product.id,
            "quantity": item_data.quantity,
            "price_at_time": product.price,
            "product_name": product.name
        })

    order = models.Order(
        user_id=current_user.id,
        total_price=total_price,
        delivery_address=order_data.delivery_address,
        status=models.OrderStatus.CREATED
    )
    db.add(order)
    db.flush()

    for item in order_items:
        order_item = models.OrderItem(
            order_id=order.id,
            product_id=item["product_id"],
            quantity=item["quantity"],
            price_at_time=item["price_at_time"],
            product_name=item["product_name"]
        )
        db.add(order_item)

    db.commit()
    db.refresh(order)

    return order

@app.get('/orders/user/{username}', response_model=List[OrderListResponse])
def get_orders_by_username(
        username: str,
        db: Session = Depends(get_db),
        skip: int = 0,
        limit: int = 20
):
    user = get_user_by_username(db, username)

    orders = db.query(models.Order).filter(
        models.Order.user_id == user.id
    ).order_by(models.Order.created_at.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": o.id,
            "user_id": o.user_id,
            "total_price": o.total_price,
            "status": o.status,
            "created_at": o.created_at,
            "items_count": len(o.items)
        }
        for o in orders
    ]


@app.get('/orders/id/{order_id}', response_model=OrderResponse)
def get_order_details(
        order_id: int,
        db: Session = Depends(get_db)
):

    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')
    return order


@app.patch('/orders/id/{order_id}/status')
def update_order_status(
        order_id: int,
        status_update: OrderUpdateStatus,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):

    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')

    order.status = status_update.status
    db.commit()

    return {'message': f'Order status updated to {status_update.status}'}


@app.post('/orders/id/{order_id}/pay')
def mock_payment(
        order_id: int,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')

    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail='Not enough permission')

    if order.status != models.OrderStatus.CREATED:
        raise HTTPException(status_code=400, detail='Order already paid or cancelled')

    order.status = models.OrderStatus.PAID

    payment = models.Payment(
        order_id=order.id,
        amount=order.total_price,
        status=models.PaymentStatus.COMPLETED,
        stripe_payment_intent_id=f"mock_{order_id}_{int(datetime.now().timestamp())}"
    )
    db.add(payment)
    db.commit()

    return {
        'message': 'Payment successful',
        'order_id': order.id,
        'status': order.status,
        'payment_id': payment.id
    }