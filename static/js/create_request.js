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

  alert('Request created with token: ' + request.token);
}

document.getElementById('request-form').addEventListener('submit', createRequest);
loadModules();
