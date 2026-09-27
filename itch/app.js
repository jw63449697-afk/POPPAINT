const canvas = document.getElementById('paintCanvas');
const ctx = canvas.getContext('2d');
const colorButtons = document.querySelectorAll('.color-button');
const eraserButton = document.getElementById('eraserButton');
const clearButton = document.getElementById('clearButton');
const currentTool = document.getElementById('currentTool');
const saveButton = document.getElementById('saveButton');
const titleInput = document.getElementById('drawingTitle');
const descriptionInput = document.getElementById('drawingDescription');

let drawing = false;
let currentColor = '#000000';
let isEraser = false;
let brushSize = 5;

ctx.fillStyle = '#ffffff';
ctx.fillRect(0, 0, canvas.width, canvas.height);
ctx.lineCap = 'round';
ctx.lineJoin = 'round';

function updateToolText() {
  if (isEraser) {
    currentTool.textContent = '현재 도구: 지우개';
  } else {
    currentTool.textContent = `현재 도구: ${currentColor} 펜`;
  }
}

function getMousePosition(event) {
  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;

  return {
    x: (event.clientX - rect.left) * scaleX,
    y: (event.clientY - rect.top) * scaleY,
  };
}

function startDrawing(event) {
  drawing = true;
  const position = getMousePosition(event);
  ctx.beginPath();
  ctx.moveTo(position.x, position.y);
}

function draw(event) {
  if (!drawing) return;

  const position = getMousePosition(event);
  ctx.lineWidth = brushSize;
  ctx.strokeStyle = isEraser ? '#ffffff' : currentColor;
  ctx.lineTo(position.x, position.y);
  ctx.stroke();
}

function stopDrawing() {
  drawing = false;
  ctx.beginPath();
}

canvas.addEventListener('mousedown', startDrawing);
canvas.addEventListener('mousemove', draw);
canvas.addEventListener('mouseup', stopDrawing);
canvas.addEventListener('mouseleave', stopDrawing);

colorButtons.forEach((button) => {
  button.addEventListener('click', () => {
    colorButtons.forEach((b) => b.classList.remove('active'));
    button.classList.add('active');
    currentColor = button.dataset.color;
    isEraser = false;
    eraserButton.classList.remove('active');
    updateToolText();
  });
});

eraserButton.addEventListener('click', () => {
  isEraser = !isEraser;
  eraserButton.classList.toggle('active', isEraser);
  updateToolText();
});

clearButton.addEventListener('click', () => {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
});

saveButton.addEventListener('click', () => {
  const title = (titleInput.value || 'POP_PAINT').trim();
  const description = (descriptionInput.value || '').trim();
  const link = document.createElement('a');

  const dataUrl = canvas.toDataURL('image/png');
  const safeTitle = title.replace(/[^a-zA-Z0-9가-힣_\- ]/g, '').slice(0, 80) || 'POP_PAINT';
  link.href = dataUrl;
  link.download = `${safeTitle}.png`;
  link.click();

  if (description) {
    console.log('작품 설명:', description);
  }
});

updateToolText();
