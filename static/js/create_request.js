async function loadModules() {
  const resp = await fetch('/modules');
  const modules = await resp.json();
  const list = document.getElementById('module-list');
  modules.forEach(m => {
    const label = document.createElement('label');
    label.className = 'block';
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.value = m;
    checkbox.className = 'mr-2';
    label.appendChild(checkbox);
    label.appendChild(document.createTextNode(m));
    list.appendChild(label);
  });
}

async function createRequest(event) {
  event.preventDefault();
  const nickname = document.getElementById('nickname').value;
  const expires = parseInt(document.getElementById('expires').value, 10);

  const res = await fetch('/requests', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ nickname, expires_days: expires })
  });
  const request = await res.json();

  const selected = Array.from(document.querySelectorAll('#module-list input:checked')).map(cb => cb.value);
  for (const mod of selected) {
    await fetch(`/requests/${request.id}/modules`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ kind: mod })
    });
  }

  // Show success modal with copy-able URL
  showSuccessModal(request.token);
}

function showSuccessModal(token) {
  const baseUrl = window.location.origin;
  const customerUrl = `${baseUrl}/customer?token=${token}`;
  
  // Create modal overlay
  const modal = document.createElement('div');
  modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
  modal.innerHTML = `
    <div class="bg-white rounded-lg p-6 max-w-lg w-full mx-4">
      <h2 class="text-xl font-bold mb-4 text-green-600">✓ Request Created Successfully!</h2>
      
      <div class="mb-4">
        <p class="text-sm text-gray-600 mb-2">Customer URL:</p>
        <div class="flex gap-2">
          <input type="text" 
                 value="${customerUrl}" 
                 id="customer-url-input"
                 class="flex-1 px-3 py-2 border rounded bg-gray-50 text-sm" 
                 readonly>
          <button onclick="copyToClipboard()" 
                  class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
            Copy
          </button>
        </div>
        <p class="text-xs text-gray-500 mt-2">Share this link with your customer to collect their documents.</p>
      </div>
      
      <div class="mt-6 flex justify-end gap-2">
        <button onclick="window.open('${customerUrl}', '_blank')" 
                class="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50">
          Preview
        </button>
        <button onclick="closeModal()" 
                class="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700">
          Done
        </button>
      </div>
    </div>
  `;
  
  document.body.appendChild(modal);
  
  // Auto-select the URL for easy copying
  setTimeout(() => {
    document.getElementById('customer-url-input').select();
  }, 100);
}

function copyToClipboard() {
  const input = document.getElementById('customer-url-input');
  input.select();
  document.execCommand('copy');
  
  // Show feedback
  const button = event.target;
  const originalText = button.textContent;
  button.textContent = '✓ Copied!';
  button.classList.add('bg-green-600');
  
  setTimeout(() => {
    button.textContent = originalText;
    button.classList.remove('bg-green-600');
  }, 2000);
}

function closeModal() {
  const modal = document.querySelector('.fixed.inset-0');
  if (modal) {
    modal.remove();
    // Reset form for next request
    document.getElementById('request-form').reset();
    // Reload modules to reset checkboxes
    document.getElementById('module-list').innerHTML = '';
    loadModules();
  }
}

document.getElementById('request-form').addEventListener('submit', createRequest);
loadModules();
