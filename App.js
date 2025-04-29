import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);
  const [customerName, setCustomerName] = useState('');
  const [customerEmail, setCustomerEmail] = useState('');
  const [orderStatus, setOrderStatus] = useState(null);
  const [orderId, setOrderId] = useState('');
  const [lookupOrderId, setLookupOrderId] = useState('');
  const [view, setView] = useState('products'); // products, cart, confirmation, lookup

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

  useEffect(() => {
    // Fetch products from the API
    fetch(`${API_URL}/api/products`)
      .then(response => response.json())
      .then(data => setProducts(data))
      .catch(error => console.error('Error fetching products:', error));
  }, [API_URL]);

  const addToCart = (product) => {
    const existingItem = cart.find(item => item.id === product.id);
    
    if (existingItem) {
      const updatedCart = cart.map(item => 
        item.id === product.id 
          ? { ...item, quantity: item.quantity + 1 } 
          : item
      );
      setCart(updatedCart);
    } else {
      setCart([...cart, { ...product, quantity: 1 }]);
    }
  };

  const removeFromCart = (productId) => {
    const updatedCart = cart.filter(item => item.id !== productId);
    setCart(updatedCart);
  };

  const updateQuantity = (productId, newQuantity) => {
    if (newQuantity < 1) return;
    
    const updatedCart = cart.map(item => 
      item.id === productId 
        ? { ...item, quantity: newQuantity } 
        : item
    );
    setCart(updatedCart);
  };

  const placeOrder = () => {
    if (!customerName || !customerEmail || cart.length === 0) {
      alert('Please fill in all fields and add items to your cart');
      return;
    }

    const orderData = {
      customer_name: customerName,
      customer_email: customerEmail,
      items: cart.map(item => ({
        product_id: item.id,
        quantity: item.quantity,
        price: item.price
      }))
    };

    fetch(`${API_URL}/api/orders`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(orderData)
    })
      .then(response => response.json())
      .then(data => {
        setOrderId(data.order_id);
        setView('confirmation');
        setCart([]);
      })
      .catch(error => console.error('Error placing order:', error));
  };

  const lookupOrder = () => {
    if (!lookupOrderId) return;

    fetch(`${API_URL}/api/orders/${lookupOrderId}`)
      .then(response => {
        if (!response.ok) {
          throw new Error('Order not found');
        }
        return response.json();
      })
      .then(data => {
        setOrderStatus(data);
        setView('orderStatus');
      })
      .catch(error => {
        console.error('Error fetching order:', error);
        alert('Order not found or error occurred');
      });
  };

  const calculateTotal = () => {
    return cart.reduce((total, item) => total + (item.price * item.quantity), 0).toFixed(2);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Vedanti's Bakery</h1>
        <nav>
          <button onClick={() => setView('products')}>Products</button>
          <button onClick={() => setView('cart')}>
            Cart ({cart.reduce((total, item) => total + item.quantity, 0)})
          </button>
          <button onClick={() => setView('lookup')}>Check Order Status</button>
        </nav>
      </header>

      <div className="container">
        {view === 'products' && (
          <div className="products-container">
            <h2>Our Products</h2>
            <div className="products-grid">
              {products.map(product => (
                <div key={product.id} className="product-card">
                  <div className="product-image">
                    {product.image_url && (
                      <img src={product.image_url} alt={product.name} />
                    )}
                  </div>
                  <h3>{product.name}</h3>
                  <p>{product.description}</p>
                  <p className="price">${product.price.toFixed(2)}</p>
                  <button onClick={() => addToCart(product)}>Add to Cart</button>
                </div>
              ))}
            </div>
          </div>
        )}

        {view === 'cart' && (
          <div className="cart-container">
            <h2>Your Cart</h2>
            {cart.length === 0 ? (
              <p>Your cart is empty</p>
            ) : (
              <>
                <table className="cart-table">
                  <thead>
                    <tr>
                      <th>Product</th>
                      <th>Price</th>
                      <th>Quantity</th>
                      <th>Total</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cart.map(item => (
                      <tr key={item.id}>
                        <td>{item.name}</td>
                        <td>${item.price.toFixed(2)}</td>
                        <td>
                          <button onClick={() => updateQuantity(item.id, item.quantity - 1)}>-</button>
                          {item.quantity}
                          <button onClick={() => updateQuantity(item.id, item.quantity + 1)}>+</button>
                        </td>
                        <td>${(item.price * item.quantity).toFixed(2)}</td>
                        <td>
                          <button onClick={() => removeFromCart(item.id)}>Remove</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr>
                      <td colSpan="3" className="text-right"><strong>Total:</strong></td>
                      <td><strong>${calculateTotal()}</strong></td>
                      <td></td>
                    </tr>
                  </tfoot>
                </table>

                <div className="checkout-form">
                  <h3>Customer Information</h3>
                  <div className="form-group">
                    <label>Name:</label>
                    <input 
                      type="text" 
                      value={customerName} 
                      onChange={(e) => setCustomerName(e.target.value)} 
                      required 
                    />
                  </div>
                  <div className="form-group">
                    <label>Email:</label>
                    <input 
                      type="email" 
                      value={customerEmail} 
                      onChange={(e) => setCustomerEmail(e.target.value)} 
                      required 
                    />
                  </div>
                  <button className="checkout-button" onClick={placeOrder}>Place Order</button>
                </div>
              </>
            )}
          </div>
        )}

        {view === 'confirmation' && (
          <div className="confirmation-container">
            <h2>Order Confirmation</h2>
            <p>Thank you for your order!</p>
            <p>Your order ID is: <strong>{orderId}</strong></p>
            <p>You can check your order status anytime using this ID.</p>
            <button onClick={() => setView('products')}>Continue Shopping</button>
          </div>
        )}

        {view === 'lookup' && (
          <div className="lookup-container">
            <h2>Check Order Status</h2>
            <div className="form-group">
              <label>Order ID:</label>
              <input 
                type="text" 
                value={lookupOrderId} 
                onChange={(e) => setLookupOrderId(e.target.value)} 
                required 
              />
            </div>
            <button onClick={lookupOrder}>Check Status</button>
          </div>
        )}

        {view === 'orderStatus' && orderStatus && (
          <div className="order-status-container">
            <h2>Order #{orderStatus.order_id}</h2>
            <p><strong>Customer:</strong> {orderStatus.customer_name}</p>
            <p><strong>Date:</strong> {orderStatus.created_at}</p>
            <p><strong>Status:</strong> {orderStatus.status}</p>
            
            <h3>Order Items</h3>
            <table className="order-items-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Quantity</th>
                  <th>Price</th>
                  <th>Total</th>
                </tr>
              </thead>
              <tbody>
                {orderStatus.items.map((item, index) => (
                  <tr key={index}>
                    <td>{item.product_name}</td>
                    <td>{item.quantity}</td>
                    <td>${item.unit_price.toFixed(2)}</td>
                    <td>${item.total.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr>
                  <td colSpan="3" className="text-right"><strong>Total:</strong></td>
                  <td>
                    <strong>
                      ${orderStatus.items.reduce((sum, item) => sum + item.total, 0).toFixed(2)}
                    </strong>
                  </td>
                </tr>
              </tfoot>
            </table>
            
            <button onClick={() => setView('lookup')}>Back to Order Lookup</button>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;