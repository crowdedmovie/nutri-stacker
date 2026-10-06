export default function(component) {
  const {parentElement, data, setStateValue} = component;
  const root = parentElement.querySelector('.ui-live-root');
  let style = parentElement.querySelector('[data-live-tokens]');
  if (!style) {
    style = document.createElement('style');
    style.dataset.liveTokens = '';
    parentElement.append(style);
  }
  style.textContent = data.tokens;
  // DOM nodes survive data updates; preserve focus, selection and uncommitted text.
  if (!root.querySelector('input')) {
    root.innerHTML = '<label for="search"></label><div class="control"><svg aria-hidden="true" viewBox="0 0 24 24"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4 4"/></svg><input id="search" type="search" autocomplete="off"/><button type="button" class="clear">×</button></div><div id="guidance" class="guidance"></div>';
  }
  const input = root.querySelector('input');
  const clear = root.querySelector('button');
  const guidance = root.querySelector('.guidance');
  root.querySelector('label').textContent = data.label;
  input.placeholder = data.placeholder;
  input.disabled = Boolean(data.disabled);
  clear.disabled = Boolean(data.disabled);
  clear.setAttribute('aria-label', data.clearLabel);
  clear.title = data.clearLabel;
  input.setAttribute('aria-describedby', 'guidance');
  input.setAttribute('aria-invalid', data.error ? 'true' : 'false');
  guidance.textContent = data.error || data.helper || '';
  guidance.setAttribute('role', data.error ? 'alert' : 'status');
  root.classList.toggle('error', Boolean(data.error));
  root.classList.toggle('disabled', Boolean(data.disabled));
  const active = parentElement.activeElement === input;
  if (!active) input.value = data.value || '';
  let timer;
  let composing = false;
  let lastSent = data.value || '';
  const updateClear = () => { clear.hidden = !input.value; };
  const commit = () => {
    clearTimeout(timer);
    if (composing || input.disabled || input.value === lastSent) return;
    lastSent = input.value;
    setStateValue('value', input.value);
  };
  const changed = () => {
    updateClear();
    clearTimeout(timer);
    if (!composing) timer = setTimeout(commit, data.debounce);
  };
  const keydown = (event) => {
    if (event.key === 'Enter' && !event.isComposing) { event.preventDefault(); commit(); }
    if (event.key === 'Escape' && !event.isComposing) { input.value = ''; updateClear(); commit(); }
  };
  const start = () => { composing = true; clearTimeout(timer); };
  const end = () => { composing = false; changed(); };
  const cleared = () => { input.value = ''; updateClear(); input.focus(); commit(); };
  const listeners = [[input, 'input', changed], [input, 'blur', commit], [input, 'keydown', keydown],
    [input, 'compositionstart', start], [input, 'compositionend', end], [clear, 'click', cleared]];
  listeners.forEach(([element, event, handler]) => element.addEventListener(event, handler));
  updateClear();
  return () => {
    clearTimeout(timer);
    listeners.forEach(([element, event, handler]) => element.removeEventListener(event, handler));
  };
}
