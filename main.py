from fastapi import FastAPI, Depends, HTTPException, Form, Query, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
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

from fastapi import FastAPI, Depends, HTTPException, Form, Query, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from starlette.templating import _TemplateResponse

# ... остальные импорты

app = FastAPI()

# Настройка шаблонов
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    # Возвращаем HTML напрямую, без Jinja2
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Магазин - Корзина товаров</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: white; border-radius: 15px; padding: 20px; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
            .header h1 { color: #333; margin-bottom: 15px; }
            .auth-section { display: flex; gap: 15px; flex-wrap: wrap; align-items: center; }
            .auth-section input { padding: 10px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; }
            .btn { padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; transition: all 0.3s; }
            .btn-primary { background: #667eea; color: white; }
            .btn-primary:hover { background: #5a67d8; transform: translateY(-2px); }
            .btn-success { background: #48bb78; color: white; }
            .btn-success:hover { background: #38a169; }
            .btn-danger { background: #f56565; color: white; }
            .btn-danger:hover { background: #e53e3e; }
            .user-info { background: #e2e8f0; padding: 10px 15px; border-radius: 10px; display: inline-block; }
            .products-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; margin-bottom: 30px; }
            .product-card { background: white; border-radius: 15px; padding: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); transition: transform 0.3s; }
            .product-card:hover { transform: translateY(-5px); }
            .product-card h3 { color: #333; margin-bottom: 10px; }
            .product-card .price { font-size: 24px; color: #667eea; font-weight: bold; margin: 10px 0; }
            .product-card .stock { color: #48bb78; margin-bottom: 15px; }
            .product-card input { width: 60px; padding: 5px; margin-right: 10px; border: 1px solid #ddd; border-radius: 5px; }
            .cart-section { background: white; border-radius: 15px; padding: 20px; margin-top: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
            .cart-item { display: flex; justify-content: space-between; align-items: center; padding: 15px; border-bottom: 1px solid #eee; }
            .cart-item:last-child { border-bottom: none; }
            .cart-total { text-align: right; padding-top: 15px; font-size: 20px; font-weight: bold; color: #333; }
            .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
            .tab { padding: 10px 20px; background: #e2e8f0; border: none; border-radius: 10px; cursor: pointer; transition: all 0.3s; }
            .tab.active { background: #667eea; color: white; }
            .tab-content { display: none; }
            .tab-content.active { display: block; }
            .order-card { background: #f7fafc; border-radius: 10px; padding: 15px; margin-bottom: 15px; }
            .order-header { display: flex; justify-content: space-between; margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid #ddd; }
            .order-status { padding: 5px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }
            .status-created { background: #fef3c7; color: #d97706; }
            .status-paid { background: #d1fae5; color: #059669; }
            .status-shipped { background: #dbeafe; color: #2563eb; }
            .status-delivered { background: #d1fae5; color: #059669; }
            .status-cancelled { background: #fee2e2; color: #dc2626; }
            .loading { text-align: center; padding: 40px; color: white; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🛍️ Интернет-магазин</h1>
                <div id="authPanel" class="auth-section">
                    <input type="text" id="loginUsername" placeholder="Имя пользователя">
                    <input type="password" id="loginPassword" placeholder="Пароль">
                    <button class="btn btn-primary" onclick="login()">Войти</button>
                    <button class="btn btn-success" onclick="showRegister()">Регистрация</button>
                </div>
                <div id="userPanel" style="display: none;">
                    <span class="user-info" id="userInfo"></span>
                    <button class="btn btn-danger" onclick="logout()">Выйти</button>
                </div>
            </div>
            <div class="tabs">
                <button class="tab active" onclick="showTab('products', event)">📦 Товары</button>
                <button class="tab" onclick="showTab('cart', event)">🛒 Корзина</button>
                <button class="tab" onclick="showTab('orders', event)">📋 Заказы</button>
            </div>
            <div id="productsTab" class="tab-content active"><div id="productsGrid" class="products-grid"><div class="loading">Загрузка товаров...</div></div></div>
            <div id="cartTab" class="tab-content">
                <div class="cart-section">
                    <h2>🛒 Моя корзина</h2>
                    <div id="cartItems"></div>
                    <div id="cartEmpty" style="text-align: center; padding: 40px; color: #999;">Корзина пуста</div>
                    <div id="cartCheckout" style="display: none;">
                        <div class="cart-total" id="cartTotal"></div>
                        <div style="margin-top: 20px;">
                            <input type="text" id="deliveryAddress" placeholder="Адрес доставки" style="width: 70%; padding: 10px; margin-right: 10px;">
                            <button class="btn btn-success" onclick="createOrder()">Оформить заказ</button>
                        </div>
                    </div>
                </div>
            </div>
            <div id="ordersTab" class="tab-content"><div class="cart-section"><h2>📋 Мои заказы</h2><div id="ordersList"></div></div></div>
        </div>
        <script>
            let API_URL = 'http://127.0.0.1:8000';
            let token = localStorage.getItem('token');
            let currentUser = null;
            if (token) checkAuth();
            async function checkAuth() {
                try {
                    const response = await fetch(API_URL + '/users/me', { headers: { 'Authorization': 'Bearer ' + token } });
                    if (response.ok) {
                        const user = await response.json();
                        currentUser = user;
                        document.getElementById('authPanel').style.display = 'none';
                        document.getElementById('userPanel').style.display = 'block';
                        document.getElementById('userInfo').innerHTML = '👤 ' + user.username;
                        loadProducts(); loadCart(); loadOrders();
                    } else logout();
                } catch(e) { logout(); }
            }
            async function login() {
                const username = document.getElementById('loginUsername').value;
                const password = document.getElementById('loginPassword').value;
                if (!username || !password) { alert('Введите username и password'); return; }
                const formData = new URLSearchParams();
                formData.append('username', username);
                formData.append('password', password);
                try {
                    const response = await fetch(API_URL + '/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                        body: formData
                    });
                    if (response.ok) {
                        const data = await response.json();
                        token = data.access_token;
                        localStorage.setItem('token', token);
                        currentUser = { username: data.username, id: data.user_id };
                        document.getElementById('authPanel').style.display = 'none';
                        document.getElementById('userPanel').style.display = 'block';
                        document.getElementById('userInfo').innerHTML = '👤 ' + data.username;
                        loadProducts(); loadCart(); loadOrders();
                    } else alert('Неверный username или пароль');
                } catch(e) { alert('Ошибка подключения'); }
            }
            function showRegister() {
                const username = prompt('Введите username:'); if (!username) return;
                const email = prompt('Введите email:'); if (!email) return;
                const password = prompt('Введите пароль:'); if (!password) return;
                fetch(API_URL + '/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: username, email: email, password: password })
                }).then(async response => {
                    if (response.ok) alert('Регистрация успешна! Теперь войдите.');
                    else { const error = await response.json(); alert('Ошибка: ' + error.detail); }
                });
            }
            function logout() {
                localStorage.removeItem('token');
                token = null; currentUser = null;
                document.getElementById('authPanel').style.display = 'flex';
                document.getElementById('userPanel').style.display = 'none';
                document.getElementById('productsGrid').innerHTML = '<div class="loading">Авторизуйтесь для просмотра товаров</div>';
                document.getElementById('cartItems').innerHTML = '';
                document.getElementById('ordersList').innerHTML = '';
                document.getElementById('cartEmpty').style.display = 'block';
                document.getElementById('cartCheckout').style.display = 'none';
            }
            async function loadProducts() {
                if (!token) return;
                try {
                    const response = await fetch(API_URL + '/products', { headers: { 'Authorization': 'Bearer ' + token } });
                    const products = await response.json();
                    const grid = document.getElementById('productsGrid');
                    if (products.length === 0) { grid.innerHTML = '<div style="text-align:center; color:white;">Нет товаров</div>'; return; }
                    grid.innerHTML = products.map(p => '<div class="product-card"><h3>' + p.name + '</h3><div class="price">' + Number(p.price).toLocaleString() + ' ₽</div><div class="stock">В наличии: ' + p.stock + '</div><input type="number" id="qty_' + p.id + '" value="1" min="1" max="' + p.stock + '"><button class="btn btn-primary" onclick="addToCart(' + p.id + ')">В корзину</button></div>').join('');
                } catch(e) { console.error(e); }
            }
            async function addToCart(productId) {
                const quantity = document.getElementById('qty_' + productId).value;
                try {
                    const response = await fetch(API_URL + '/cart/add/' + productId + '?quantity=' + quantity, {
                        method: 'POST',
                        headers: { 'Authorization': 'Bearer ' + token }
                    });
                    if (response.ok) { alert('Товар добавлен'); loadCart(); }
                    else { const error = await response.json(); alert('Ошибка: ' + error.detail); }
                } catch(e) { alert('Ошибка'); }
            }
            async function loadCart() {
                if (!token || !currentUser) return;
                try {
                    const response = await fetch(API_URL + '/cart/' + currentUser.username, { headers: { 'Authorization': 'Bearer ' + token } });
                    const cart = await response.json();
                    const container = document.getElementById('cartItems');
                    const empty = document.getElementById('cartEmpty');
                    const checkout = document.getElementById('cartCheckout');
                    if (!cart.items || cart.items.length === 0) { empty.style.display = 'block'; container.innerHTML = ''; checkout.style.display = 'none'; return; }
                    empty.style.display = 'none'; checkout.style.display = 'block';
                    container.innerHTML = cart.items.map(item => '<div class="cart-item"><div><strong>' + item.product_name + '</strong><div>' + Number(item.product_price).toLocaleString() + ' ₽ × ' + item.quantity + '</div></div><div><strong>' + Number(item.product_price * item.quantity).toLocaleString() + ' ₽</strong><button class="btn btn-danger" style="margin-left: 10px;" onclick="removeFromCart(' + item.id + ')">Удалить</button></div></div>').join('');
                    document.getElementById('cartTotal').innerHTML = 'Итого: ' + Number(cart.total_price).toLocaleString() + ' ₽';
                } catch(e) { console.error(e); }
            }
            async function removeFromCart(itemId) {
                try { await fetch(API_URL + '/cart/remove/' + itemId, { method: 'DELETE', headers: { 'Authorization': 'Bearer ' + token } }); loadCart(); }
                catch(e) { alert('Ошибка'); }
            }
            async function createOrder() {
                const address = document.getElementById('deliveryAddress').value;
                if (!address) { alert('Введите адрес доставки'); return; }
                try {
                    const cartResponse = await fetch(API_URL + '/cart/' + currentUser.username, { headers: { 'Authorization': 'Bearer ' + token } });
                    const cart = await cartResponse.json();
                    if (!cart.items || cart.items.length === 0) { alert('Корзина пуста'); return; }
                    const items = cart.items.map(item => ({ product_id: item.product_id, quantity: item.quantity }));
                    const response = await fetch(API_URL + '/orders', {
                        method: 'POST',
                        headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
                        body: JSON.stringify({ delivery_address: address, items: items })
                    });
                    if (response.ok) { alert('Заказ оформлен!'); loadCart(); loadOrders(); document.getElementById('deliveryAddress').value = ''; }
                    else { const error = await response.json(); alert('Ошибка: ' + error.detail); }
                } catch(e) { alert('Ошибка'); }
            }
            async function loadOrders() {
                if (!token || !currentUser) return;
                try {
                    const response = await fetch(API_URL + '/orders/user/' + currentUser.username, { headers: { 'Authorization': 'Bearer ' + token } });
                    const orders = await response.json();
                    const container = document.getElementById('ordersList');
                    if (!orders || orders.length === 0) { container.innerHTML = '<div style="text-align:center; padding:40px; color:#999;">У вас пока нет заказов</div>'; return; }
                    container.innerHTML = orders.map(order => '<div class="order-card"><div class="order-header"><strong>Заказ #' + order.id + '</strong><span class="order-status status-' + order.status + '">' + getStatusText(order.status) + '</span></div><div>Сумма: ' + Number(order.total_price).toLocaleString() + ' ₽</div><div>Товаров: ' + order.items_count + '</div><div>Дата: ' + new Date(order.created_at).toLocaleString() + '</div>' + (order.status === 'created' ? '<button class="btn btn-primary" style="margin-top:10px;" onclick="payOrder(' + order.id + ')">Оплатить</button>' : '') + '</div>').join('');
                } catch(e) { console.error(e); }
            }
            async function payOrder(orderId) {
                try {
                    const response = await fetch(API_URL + '/orders/id/' + orderId + '/pay', { method: 'POST', headers: { 'Authorization': 'Bearer ' + token } });
                    if (response.ok) { alert('Заказ оплачен!'); loadOrders(); }
                    else { const error = await response.json(); alert('Ошибка: ' + error.detail); }
                } catch(e) { alert('Ошибка'); }
            }
            function getStatusText(status) {
                const statuses = { 'created': 'Создан', 'paid': 'Оплачен', 'shipped': 'Отправлен', 'delivered': 'Доставлен', 'cancelled': 'Отменен' };
                return statuses[status] || status;
            }
            function showTab(tabName, event) {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
                if (event && event.target) event.target.classList.add('active');
                document.getElementById(tabName + 'Tab').classList.add('active');
                if (tabName === 'cart' && token) loadCart();
                if (tabName === 'orders' && token) loadOrders();
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

models.Base.metadata.create_all(bind=engine)

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