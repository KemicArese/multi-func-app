const form = document.getElementById('assistant-form');
const modeSelect = document.getElementById('mode');
const promptInput = document.getElementById('prompt');
const responseSection = document.getElementById('response');
const jsonOutput = document.getElementById('json-output');
const imageOutput = document.getElementById('image-output');

form.addEventListener('submit', async (event) => {
  event.preventDefault();

  const mode = modeSelect.value;
  const prompt = promptInput.value.trim();
  if (!prompt) {
    alert('Please enter a prompt.');
    return;
  }

  const endpoint = mode === 'image' ? '/api/image' : '/api/chat';

  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode, prompt }),
    });

    const data = await res.json();

    responseSection.classList.remove('hidden');
    jsonOutput.textContent = JSON.stringify(data, null, 2);

    if (mode === 'image' && data.image_url) {
      imageOutput.src = data.image_url;
      imageOutput.classList.remove('hidden');
    } else {
      imageOutput.classList.add('hidden');
      imageOutput.removeAttribute('src');
    }
  } catch (error) {
    responseSection.classList.remove('hidden');
    imageOutput.classList.add('hidden');
    jsonOutput.textContent = JSON.stringify(
      {
        error: 'Request failed',
        details: String(error),
      },
      null,
      2
    );
  }
});
