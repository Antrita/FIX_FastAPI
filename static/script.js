document.addEventListener('DOMContentLoaded', () => {
    const socket = new WebSocket('ws://localhost:8000/ws');
    const connectionStatus = document.getElementById('connection-status');
    const subscribeBtn = document.getElementById('subscribe-btn');
    const unsubscribeBtn = document.getElementById('unsubscribe-btn');
    const orderForm = document.getElementById('order-form');
    const orderMessage = document.getElementById('order-message');
    const statusForm = document.getElementById('status-form');
    const priceInput = document.getElementById('price-input');

    let isSubscribed = false;

    socket.onopen = () => {
        connectionStatus.textContent = 'Connection Status: Connected';
        connectionStatus.className = 'connected';
    };

    socket.onclose = () => {
        connectionStatus.textContent = 'Connection Status: Disconnected';
        connectionStatus.className = 'disconnected';
    };

    subscribeBtn.addEventListener('click', () => {
        isSubscribed = true;
        priceInput.disabled = false;
        priceInput.placeholder = '';
        window.location.href = 'MarketData.html';
    });

    unsubscribeBtn.addEventListener('click', () => {
        isSubscribed = false;
        priceInput.disabled = true;
        priceInput.value = '';
        priceInput.placeholder = 'Please subscribe to Market Data first!';
    });

    priceInput.addEventListener('focus', () => {
        if (!isSubscribed) {
            priceInput.blur();
            priceInput.value = '';
            priceInput.placeholder = 'Please subscribe to Market Data first!';
        }
    });

    orderForm.addEventListener('submit', (e) => {
        e.preventDefault();
        if (!isSubscribed) {
            alert('Please subscribe to Market Data before placing an order.');
            return;
        }
        const formData = new FormData(orderForm);
        const order = {
            action: formData.get('action'),
            symbol: formData.get('symbol'),
            quantity: formData.get('quantity'),
            price: formData.get('price')
        };

        console.log('Order placed:', order);

        orderMessage.textContent = 'Order placed successfully!';
        orderMessage.className = '';
        setTimeout(() => {
            orderMessage.className = 'hidden';
        }, 3000);
    });

    statusForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const formData = new FormData(statusForm);
        const clOrdID = formData.get('clordid');

        // check the order status with backend
        console.log('Checking status for order:', clOrdID);
    });
      // Initialize price input state
    priceInput.disabled = true;
    priceInput.placeholder = 'Please subscribe to Market Data first!';
});