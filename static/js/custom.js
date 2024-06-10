// custom.js

function showConfirmation() {
  const shippingAddress = document.getElementById('shipping_address').value.trim();
  if (!shippingAddress) {
      alert('Please enter a valid shipping address.');
      return;
  }
  document.getElementById('confirm_shipping_address').innerText = shippingAddress;
  document.getElementById('confirm_total_price').innerText = '{{ total_price }}';
  document.getElementById('confirmation_section').style.display = 'block';
}

function submitOrder() {
  document.getElementById('checkout_form').submit();
}



