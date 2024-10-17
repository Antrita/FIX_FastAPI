document.addEventListener('DOMContentLoaded', () => {
    generateDynamicForm(document.getElementById('order-type').value);

    document.getElementById('order-type').addEventListener('change', function() {
        generateDynamicForm(this.value);
    });

    const socket = new WebSocket(`ws://${window.location.host}/ws`);
    const connectionStatus = document.getElementById('connection-status');
    const subscribeBtn = document.getElementById('subscribe-btn');
    const unsubscribeBtn = document.getElementById('unsubscribe-btn');
    const orderForm = document.getElementById('order-form');
    const orderMessage = document.getElementById('order-message');
    const statusForm = document.getElementById('status-form');
    const priceInput = document.getElementById('price-input');
    const orderTypeSelect = document.getElementById('order-type');
    const limitFields = document.getElementById('limit-fields');
    const stopFields = document.getElementById('stop-fields');
    const stopLimitFields = document.getElementById('stop-limit-fields');
    let isSubscribed = false;
    let marketDataWindow = null;
  function generateDynamicForm(orderType) {
    const priceField = document.getElementById('price-field');
    const marketFields = document.getElementById('Market');
    const limitFields = document.getElementById('limit-fields');
    const stopFields = document.getElementById('stop-fields');
    const stopLimitFields = document.getElementById('stop-limit-fields');

    // Hide all fields initially
    priceField.style.display = 'none';
    marketFields.style.display = 'none';
    limitFields.style.display = 'none';
    stopFields.style.display = 'none';
    stopLimitFields.style.display = 'none';
    const usdToBrlRate = 5.25;

    switch (orderType) {
        case 'Market':
            marketFields.style.display = 'block';
            break;
        case 'Limit':
            limitFields.style.display = 'block';
            const samplePrice = 65;
            const limit = samplePrice * 1.1;
            document.getElementById('limit-price').placeholder = `Enter limit price (Warning: Don't exceed ${limit.toFixed(2)})`;

        limitPriceInput.addEventListener('input', function() {
                const warningElement = this.nextElementSibling || document.createElement('p');
                warningElement.style.color = 'red';
                if (parseFloat(this.value) > limit) {
                    warningElement.textContent = `Warning: Price exceeds ${limit.toFixed(2)}`;
                    if (!this.nextElementSibling) {
                        this.parentNode.insertBefore(warningElement, this.nextSibling);
                    }
                } else {
                    warningElement.textContent = '';
                }
            });
            break;
        case 'Stop':
            stopFields.style.display = 'block';
            const stopPrice = 60;
            const stopPriceBrl = stopPrice * usdToBrlRate;
             const stopPriceInput = document.getElementById('stop-price');
             stopPriceInput.placeholder = `Enter stop price (Calculated BRL price: ${stopPriceBrl.toFixed(2)})`;
            // Add warning display for Stop order
            stopPriceInput.addEventListener('input', function() {
                const warningElement = this.nextElementSibling || document.createElement('p');
                warningElement.style.color = 'red';
                if (parseFloat(this.value) > stopPriceBrl) {
                    warningElement.textContent = `Warning: Price exceeds ${stopPriceBrl.toFixed(2)} BRL`;
                    if (!this.nextElementSibling) {
                        this.parentNode.insertBefore(warningElement, this.nextSibling);
                    }
                } else {
                    warningElement.textContent = '';
                }
            });
            break;
         case 'StopLimit':
            stopLimitFields.style.display = 'block';
            const stopLimitStopPrice = document.getElementById('stop-limit-stop-price');
            const stopLimitLimitPrice = document.getElementById('stop-limit-limit-price');

            stopLimitStopPrice.placeholder = 'Enter stop price';
            stopLimitLimitPrice.placeholder = 'Enter limit price';

            stopLimitStopPrice.addEventListener('input', function() {
                const stopValue = parseFloat(this.value);
                if (!isNaN(stopValue)) {
                }
            });

            stopLimitLimitPrice.addEventListener('input', function() {
                const limitValue = parseFloat(this.value);
                const stopValue = parseFloat(stopLimitStopPrice.value);
            });

            const actionSelect = document.getElementById('action');
            const validateStopLimitPrices = function() {
                const action = actionSelect.value;
                const stopValue = parseFloat(stopLimitStopPrice.value);
                const limitValue = parseFloat(stopLimitLimitPrice.value);
                let warningMessage = '';

                if (!isNaN(stopValue) && !isNaN(limitValue)) {
                    if (action === 'Buy' && stopValue > limitValue) {
                        warningMessage = 'For buy orders, stop price should not be higher than limit price.';
                    } else if (action === 'Sell' && stopValue < limitValue) {
                        warningMessage = 'For sell orders, stop price should not be lower than limit price.';
                    }
                }

                const warningElement = stopLimitFields.querySelector('.warning') || document.createElement('p');
                warningElement.textContent = warningMessage;
                warningElement.style.color = 'red';
                warningElement.className = 'warning';
                if (warningMessage && !stopLimitFields.querySelector('.warning')) {
                    stopLimitFields.appendChild(warningElement);
                } else if (!warningMessage) {
                    warningElement.remove();
                }
            };

            stopLimitStopPrice.addEventListener('input', validateStopLimitPrices);
            stopLimitLimitPrice.addEventListener('input', validateStopLimitPrices);
            actionSelect.addEventListener('change', validateStopLimitPrices);

            break;
    }
}

    // Function for validation logic
    function validateStopLimitInput() {
        const enteredPrice = parseFloat(this.value);
        const minStopPrice = 61;
        const maxStopLimitPrice = 64;
        if (enteredPrice < minStopPrice || enteredPrice > maxStopLimitPrice) {
            alert(`Warning: The stop limit price must be between ${minStopPrice} and ${maxStopLimitPrice}.`);
        }
    }

    if (socket) {
        socket.onopen = () => {
            if (connectionStatus) {
                connectionStatus.textContent = 'Connection Status: Connected';
                connectionStatus.className = 'connected';
            }
        };

        socket.onclose = () => {
            if (connectionStatus) {
                connectionStatus.textContent = 'Connection Status: Disconnected';
                connectionStatus.className = 'disconnected';
            }
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'market_data') {
                console.log('Received market data:', data.data);
                updateMarketData(data.data);
            }
        };
    }

    function updateMarketData(data) {
    const marketDataContent = document.getElementById('market-data-content');
    if (marketDataContent) {
        marketDataContent.innerHTML = JSON.stringify(data, null, 2);
    }

    // Update the price input field if it exists and is not focused
    const priceInput = document.getElementById('price-input');
    if (priceInput && !priceInput.matches(':focus')) {
        if (data.USD_BRL && data.USD_BRL.bid) {
            priceInput.value = data.USD_BRL.bid;
        }
    }

    // Update other relevant fields if necessary
    // For example, updating the market price field for Market orders
    const marketPriceField = document.getElementById('market-price');
    if (marketPriceField && data.USD_BRL && data.USD_BRL.bid) {
        marketPriceField.value = data.USD_BRL.bid;
    }
}



    if (subscribeBtn) {
        subscribeBtn.addEventListener('click', () => {
            isSubscribed = true;
            marketDataWindow = window.open('http://127.0.0.1:8000/MarketData.html', 'MarketData', 'width=600,height=400');
        });
    }

    if (unsubscribeBtn) {
        unsubscribeBtn.addEventListener('click', () => {
            isSubscribed = false;
            if (marketDataWindow) {
                marketDataWindow.close();
                marketDataWindow = null;
            }
        });
    }

    if (priceInput) {
        priceInput.disabled = false;
        priceInput.placeholder = 'Enter price';
    }

    orderTypeSelect.addEventListener('change', () => {
        limitFields.style.display = 'none';
        stopFields.style.display = 'none';
        stopLimitFields.style.display = 'none';

        switch (orderTypeSelect.value) {
            case 'Limit':
                limitFields.style.display = 'block';
                break;
            case 'Stop':
                stopFields.style.display = 'block';
                break;
            case 'StopLimit':
                stopLimitFields.style.display = 'block';
                break;
        }
    });

    if (orderForm) {
        orderForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const formData = new FormData(orderForm);
            const order = {
                action: formData.get('action'),
                symbol: formData.get('symbol'),
                quantity: formData.get('quantity'),
                orderType: formData.get('order-type'),
              //  price: formData.get('price')
            };

            // Generate dynamic form based on order type
            generateDynamicForm(order.orderType);

           switch (order.orderType) {
                case 'Limit':
                    order.limitPrice = formData.get('limit-price');
                    break;
                case 'Stop':
                    order.stopPrice = formData.get('stop-price');
                    break;
                case 'StopLimit':
                    order.stopPrice = formData.get('stop-limit-stop-price');
                    order.limitPrice = formData.get('stop-limit-limit-price');
                    break;
                }
            const lastGeneratedClOrdID = generateClOrdID();
            console.log('Order placed:', order, 'ClOrdID:', lastGeneratedClOrdID);

            if (orderMessage) {
                orderMessage.textContent = `Order placed successfully! ClOrdID: ${lastGeneratedClOrdID}`;
                orderMessage.className = '';
                setTimeout(() => {
                    orderMessage.className = 'hidden';
                }, 5000);
            }
        });
    }

    if (statusForm) {
        statusForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const formData = new FormData(statusForm);
            const clOrdID = formData.get('clordid');

            console.log('Checking status for order:', clOrdID);

            const statusResponse = document.getElementById('status-response');
            if (clOrdID === '12345') {
                const action = document.getElementById('action').value;
                const symbol = document.getElementById('symbol').value;
                const quantity = document.getElementById('quantity').value;
                const orderType = document.getElementById('order-type').value;
                const price = document.getElementById('price-input').value;

                let additionalInfo = '';
                switch (orderType) {
                    case 'Limit':
                        additionalInfo = `<p>Limit Price: ${document.getElementById('limit-price').value}</p>`;
                        break;
                    case 'Stop':
                        additionalInfo = `<p>Stop Price: ${document.getElementById('stop-price').value}</p>`;
                        break;
                    case 'StopLimit':
                        additionalInfo = `
                            <p>Stop Price: ${document.getElementById('stop-limit-stop-price').value}</p>
                            <p>Limit Price: ${document.getElementById('stop-limit-limit-price').value}</p>
                        `;
                        break;
                }

                statusResponse.innerHTML = `
                    <h3>Order Status:</h3>
                    <p>ClOrdID: ${clOrdID}</p>
                    <p>Status: Order Placed</p>
                    <p>Action: ${action}</p>
                    <p>Symbol: ${symbol}</p>
                    <p>Quantity: ${quantity}</p>
                    <p>Order Type: ${orderType}</p>
                    ${additionalInfo}

                `;
                statusResponse.className = '';
            } else {
                statusResponse.textContent = 'Order not found.';
                statusResponse.className = '';
            }
        });
    }

    function generateClOrdID() {
        return 'ORD' + Math.random().toString(36).substr(2, 9);
    }
});