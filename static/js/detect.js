(function() {
	const fileInput = document.getElementById('file');
	const dropzone = document.getElementById('dropzone');
	const form = document.getElementById('uploadForm');
	const detectBtn = document.getElementById('detectBtn');
	const clearBtn = document.getElementById('clearBtn');
	const previewBox = document.getElementById('previewBox');
	const resultContent = document.getElementById('resultContent');
	const confidenceViz = document.getElementById('confidenceViz');
	const gaugePath = document.getElementById('gauge');

	function reset() {
		fileInput.value = '';
		if (previousBlobUrl) {
			URL.revokeObjectURL(previousBlobUrl);
			previousBlobUrl = null;
		}
		dropzone.dataset.droppedFile = '';
		dropzone._droppedFile = null;
		previewBox.innerHTML = '<span class="text-white/50">Preview will appear here</span>';
		resultContent.textContent = 'No prediction yet.';
		detectBtn.disabled = false;
		if (confidenceViz) confidenceViz.classList.add('hidden');
	}

	function humanConfidence(value) {
		const pct = (value * 100).toFixed(1);
		return `${pct}%`;
	}

	// Store previous blob URLs to clean up
	let previousBlobUrl = null;

	function showPreview(file) {
		// Clean up previous blob URL to prevent memory leaks
		if (previousBlobUrl) {
			URL.revokeObjectURL(previousBlobUrl);
			previousBlobUrl = null;
		}

		const name = file.name || 'file';
		if (file.type.startsWith('image/') || name.toLowerCase().match(/\.(jpg|jpeg|png)$/i)) {
			const url = URL.createObjectURL(file);
			previousBlobUrl = url;
			previewBox.innerHTML = `<div class="w-full h-full flex items-center justify-center"><img src="${url}" alt="preview" class="rounded-xl object-contain max-w-full max-h-[200px]" onerror="this.parentElement.innerHTML='<span class=\\'text-red-300 text-sm\\'>Failed to load image preview</span>'" onload="console.log('Image loaded successfully')" /></div>`;
		} else if (name.toLowerCase().endsWith('.dcm')) {
			previewBox.innerHTML = '<div class="text-white/70">DICOM file selected</div>';
		} else {
			previewBox.innerHTML = '<div class="text-white/70">Unsupported preview</div>';
		}
	}

	// Handle click on dropzone - trigger file input
	dropzone.addEventListener('click', (e) => {
		e.stopPropagation();
		e.preventDefault();
		fileInput.click();
	});
	
	dropzone.addEventListener('dragover', (e) => { 
		e.preventDefault(); 
		e.stopPropagation();
		dropzone.classList.add('border-white/40'); 
	});
	dropzone.addEventListener('dragleave', (e) => {
		e.preventDefault();
		e.stopPropagation();
		dropzone.classList.remove('border-white/40'); 
	});
	dropzone.addEventListener('drop', (e) => {
		e.preventDefault();
		e.stopPropagation();
		dropzone.classList.remove('border-white/40');
		const file = e.dataTransfer.files?.[0];
		if (file) {
			showPreview(file);
			// Try to set the file input if possible (modern browsers)
			try {
				if (window.DataTransfer) {
					const dt = new DataTransfer();
					dt.items.add(file);
					fileInput.files = dt.files;
				} else {
					// Store file reference for fallback
					dropzone.dataset.droppedFile = file.name;
					dropzone._droppedFile = file;
				}
			} catch (err) {
				// Fallback: store file reference
				dropzone.dataset.droppedFile = file.name;
				dropzone._droppedFile = file;
			}
			detectBtn.disabled = false;
		}
	});

	fileInput.addEventListener('change', (e) => {
		const file = fileInput.files?.[0];
		if (file) {
			console.log('File selected:', file.name, file.type, file.size);
			showPreview(file);
			// Enable detect button immediately
			detectBtn.disabled = false;
		} else {
			console.log('No file selected');
		}
	});

	function setGauge(conf) {
		if (!gaugePath || !confidenceViz) return;
		// stroke-dasharray percentage of full circumference (approx)
		const pct = Math.max(0, Math.min(1, conf));
		const dash = (pct * 100).toFixed(2);
		gaugePath.setAttribute('stroke-dasharray', `${dash},100`);
		confidenceViz.classList.remove('hidden');
	}

	form.addEventListener('submit', async (e) => {
		e.preventDefault();
		let file = fileInput.files?.[0];
		
		// Fallback: check if we have a dropped file stored (for older browsers)
		if (!file && dropzone._droppedFile) {
			file = dropzone._droppedFile;
		}
		
		if (!file) {
			resultContent.textContent = 'Please choose a file first.';
			return;
		}
		detectBtn.disabled = true;
		resultContent.innerHTML = '<span class="text-white/70">Analyzing…</span>';
		if (confidenceViz) confidenceViz.classList.add('hidden');
		try {
			const formData = new FormData();
			formData.append('file', file);
			const res = await fetch('/api/predict', { method: 'POST', body: formData });
			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				throw new Error(err.detail || `Request failed (${res.status})`);
			}
			const data = await res.json();
			const color = data.label === 'Tuberculosis' ? 'text-red-300' : 'text-emerald-300';
			resultContent.innerHTML = `
				<div class="text-sm text-white/60">Prediction</div>
				<div class="mt-1 text-2xl font-extrabold ${color}">${data.label}</div>
				<div class="mt-2 text-white/70">Confidence: <span class="font-semibold">${humanConfidence(data.confidence)}</span></div>
			`;
			setGauge(Number(data.confidence || 0));
		} catch (err) {
			resultContent.innerHTML = `<span class="text-red-300">${err.message || err}</span>`;
		} finally {
			detectBtn.disabled = false;
		}
	});

	clearBtn.addEventListener('click', reset);
})();
