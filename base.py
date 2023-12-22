from flask import Blueprint, request, render_template, redirect, url_for
from Db import db
from Db.models import Users, Product, Order , OrderProduct
from flask_login import login_user, login_required, current_user, logout_user

base = Blueprint('base', __name__)
# Главная страница
@base.route('/')
def home():
    if current_user.is_authenticated:
        username = current_user.username
    else:
        username = "Аноним"

    return render_template('base.html', username=username)

# Логин
@base.route('/login', methods=['GET', 'POST'])
def login():
    errors = []
    if request.method == "GET":
        return render_template('login.html')

    username_form = request.form.get('username')
    password_form = request.form.get('password')

    if not username_form:
        errors.append("Пожалуйста, введите имя пользователя")
        print(errors)
    elif not password_form:
        errors.append("Пожалуйста, введите пароль")
        print(errors)
    else:
        my_user = Users.query.filter_by(username=username_form).first()

        if my_user is not None:
            if (my_user.password == password_form):
                login_user(my_user, remember=False)
                return redirect('/')
            else:
                errors.append("Неправильный пароль")
                print(errors)
        else:
            errors.append("Пользователя не существует")
            print(errors)

    if errors:
        return render_template("login.html", errors=errors)
        
    return render_template('login.html')

# Заказы
@base.route('/orders')
@login_required
def orders():
    my_orders = Order.query.filter_by(user_id=current_user.id).all()
#извлекается имя пользователя текущего аутентифицированного пользователя и сохраняется в переменной
    username = current_user.username
    return render_template('orders.html', orders=my_orders, username=username)

# Статус заказа
@base.route('/order-status/<int:order_id>', methods=['POST'])
# только для авторизованных пользователей
@login_required
def order_status(order_id):
    errors = []
#если заказ не найден, появляется ошибка 404
    order = Order.query.get_or_404(order_id)
#сопоставление id usera с текущим авторизированным user
    if order.user_id != current_user.id:
            errors.append("У вас нет доступа к этому заказу")
            print(errors)

    if errors:
        return render_template("orders.html", errors=errors)

    # Переключение статуса
    order.is_paid = not order.is_paid
    db.session.commit()
    
    status = 'оплачен' if order.is_paid else 'не оплачен'

    return redirect(url_for('base.orders', status=status))


# Список товаров
@base.route('/products', methods=['GET', 'POST'])
@login_required
def products():
    # Получаем параметр 'offset' из GET-запроса. Если параметр не указан, то значение по умолчанию равно 0
    offset = int(request.args.get('offset', 0))
    # отображается только 50 продуктов
    products_per_page = 50
#запрос к таблице Product
    all_products = Product.query.offset(offset).limit(products_per_page).all()
#посчет общего количества продуктов в базе данных
    total_products_count = Product.query.count()
    

    # Получаем текущий заказ пользователя 
    current_order = Order.query.filter_by(user_id=current_user.id, is_paid=False, is_draft=True).first()
    # Если текущего заказа нет, создаем новый заказ
    if not current_order:

        current_order = Order(user_id=current_user.id, is_paid=False, is_draft=True)
        db.session.add(current_order)
        db.session.commit()

    if request.method == 'POST':
        product_id = request.form.get('product_id')
        product = Product.query.get(product_id)


        if 'quantity' in request.form:
            # Получаем количество продукта, указанное пользователем
            quantity = int(request.form.get('quantity', 0))
            order_product = OrderProduct.query.filter_by(order_id=current_order.id, product_id=product_id).first()
           
           # Если товар уже присутствует в заказе и количество продукта и указанное пользователем количество больше 0,
            # увеличиваем количество заказанного товара и уменьшаем количество продукта на складе
            if order_product and product and quantity > 0:
                if product.quantity >= quantity:
                    order_product.quantity += quantity
                    product.quantity -= quantity
                    db.session.commit()

            # Если товара нет в заказе и количество продукта и указанное пользователем количество больше 0,
            # создаем новую запись в таблице OrderProduct и уменьшаем количество продукта на складе
            elif not order_product and product and quantity > 0 and product.quantity >= quantity:
                new_order_product = OrderProduct(order_id=current_order.id, product_id=product_id, quantity=quantity)
                product.quantity -= quantity
                db.session.add(new_order_product)
                db.session.commit()

        elif 'remove_quantity' in request.form:
            # Получаем количество продукта, указанное пользователем для удаления из заказа
            remove_quantity = int(request.form.get('remove_quantity', 0))
            order_product = OrderProduct.query.filter_by(order_id=current_order.id, product_id=product_id).first()

            if order_product and product:
                # Уменьшаем количество товара в корзине только на указанное количество
                if order_product.quantity >= remove_quantity:
                    order_product.quantity -= remove_quantity
                    product.quantity += remove_quantity
                    db.session.commit()
                # Если количество товара в корзине становится равным 0, удаляем запись о товаре из корзины
                if order_product.quantity == 0:
                    db.session.delete(order_product)
                    db.session.commit()

    # Подсчитываем оплаченное количество для каждого продукта
    products_with_quantity = []
    for product in all_products:
        quantity_in_basket = 0
        if current_order:
            order_product = OrderProduct.query.filter_by(order_id=current_order.id, product_id=product.id).first()
            if order_product:
                quantity_in_basket = order_product.quantity

        # Получаем сумму оплаченных количеств для каждого продукта
        paid_quantity = sum(op.quantity for op in OrderProduct.query.join(Order).filter(Order.is_paid==True, OrderProduct.product_id==product.id))

        products_with_quantity.append((product, quantity_in_basket, paid_quantity))

    return render_template('products.html', products=products_with_quantity, current_order=current_order, total_products_count=total_products_count, products_per_page=products_per_page, offset=offset)


# Формирование накладной
@base.route('/basket', methods=['GET', 'POST'])
@login_required
def basket():
    products_in_basket = []

    if request.method == 'POST':
        product_id = request.form['product_id']
        quantity = int(request.form['quantity'])

        # Получаем текущий заказ пользователя
        current_order = Order.query.filter_by(user_id=current_user.id, is_paid=False).first()

        # Если заказа нет, создаем новый
        if current_order is None:
            current_order = Order(user_id=current_user.id)
            db.session.add(current_order)
            db.session.commit() 

        # Получаем товар из базы данных
        product = Product.query.get(product_id)

        # Если товар есть в корзине, обновляем количество, иначе добавляем новый товар
        order_product = OrderProduct.query.filter_by(order_id=current_order.id, product_id=product_id).first()
        if order_product:
            order_product.quantity = quantity
            if quantity == 0:
                db.session.delete(order_product)
        else:
            if quantity > 0: 
                order_product = OrderProduct(order_id=current_order.id, product_id=product_id, quantity=quantity)
                db.session.add(order_product)

        db.session.commit()

    # Формируем список товаров в корзине
    current_order = Order.query.filter_by(user_id=current_user.id, is_paid=False, is_draft=True).first()
    if current_order:
        order_products = db.session.query(OrderProduct, Product).join(Product).filter(OrderProduct.order_id == current_order.id).all()
        for order_product, product in order_products:
            products_in_basket.append((order_product, order_product.quantity, current_order.is_draft))

    return render_template('basket.html', products=products_in_basket, current_order=current_order)


# Разлогинивание пользователя
@base.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


# Создание заказа
@base.route('/create_order', methods=['POST'])
@login_required
def create_order():
    # Получаем текущую черновую запись заказа пользователя
    current_order = Order.query.filter_by(user_id=current_user.id, is_paid=False, is_draft=True).first()
    if current_order:
        # Меняем статус заказа с черновика на подтвержденный, но еще не оплаченный
        current_order.is_draft = False
    
    db.session.commit()

    return redirect(url_for('base.orders'))

