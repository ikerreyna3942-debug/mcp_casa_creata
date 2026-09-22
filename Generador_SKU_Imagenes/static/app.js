let productosCatalogo = [];
let productosSeleccionados = [];
let archivosAdjuntos = [];
let imagenGeneradaBase64 = null;
let imagenGeneradaMime = 'image/jpeg';

document.addEventListener('DOMContentLoaded', async () => {
    const searchInput = document.getElementById('searchInput');
    const searchResults = document.getElementById('searchResults');
    const selectedList = document.getElementById('selectedList');
    const selectedCount = document.getElementById('selectedCount');
    const summaryCount = document.getElementById('summaryCount');

    const multiFileInput = document.getElementById('multiFileInput');
    const filesContainer = document.getElementById('filesContainer');
    const filesCount = document.getElementById('filesCount');
    const summaryFilesCount = document.getElementById('summaryFilesCount');

    const approvalNotes = document.getElementById('approvalNotes');
    const btnConfirm = document.getElementById('btnConfirm');
    const confirmationNotice = document.getElementById('confirmationNotice');

    const resultThumbWrapper = document.getElementById('resultThumbWrapper');
    const resultThumbImg = document.getElementById('resultThumbImg');
    const btnMostrarFoto = document.getElementById('btnMostrarFoto');
    const imageLightboxModal = document.getElementById('imageLightboxModal');
    const lightboxImg = document.getElementById('lightboxImg');
    const btnCloseLightbox = document.getElementById('btnCloseLightbox');

    try {
        const res = await fetch('/api/productos');
        const data = await res.json();
        if (data.success && data.productos) {
            productosCatalogo = data.productos;
        }
    } catch (e) {
        console.error("Error al cargar productos:", e);
    }

    function renderDropdown(items) {
        if (!items || items.length === 0) {
            searchResults.innerHTML = '<div style="padding:10px;font-size:12px;color:#64748b;">No se encontraron productos con foto</div>';
            searchResults.style.display = 'block';
            return;
        }

        searchResults.innerHTML = items.slice(0, 30).map(p => `
            <div class="search-item" data-id="${p.id}">
                <img src="${p.foto_url}" class="search-item-thumb" onerror="this.src='/static/placeholder_furniture.png'">
                <div class="search-item-info">
                    <span class="search-item-title">${p.nombre}</span>
                    <span class="search-item-sku">${p.sku}</span>
                </div>
            </div>
        `).join('');
        searchResults.style.display = 'block';

        searchResults.querySelectorAll('.search-item').forEach(el => {
            el.addEventListener('click', () => {
                const prodId = el.getAttribute('data-id');
                const prod = productosCatalogo.find(p => p.id === prodId);
                if (prod && !productosSeleccionados.some(s => s.id === prod.id)) {
                    productosSeleccionados.push({
                        ...prod,
                        cantidad: 1
                    });
                    actualizarSeleccionados();
                }
                searchInput.value = '';
                searchResults.style.display = 'none';
            });
        });
    }

    searchInput.addEventListener('focus', () => {
        const q = searchInput.value.toLowerCase().trim();
        const filtrados = q ? productosCatalogo.filter(p => p.nombre.toLowerCase().includes(q) || p.sku.toLowerCase().includes(q)) : productosCatalogo;
        renderDropdown(filtrados);
    });

    searchInput.addEventListener('input', (e) => {
        const q = e.target.value.toLowerCase().trim();
        const filtrados = q ? productosCatalogo.filter(p => p.nombre.toLowerCase().includes(q) || p.sku.toLowerCase().includes(q)) : productosCatalogo;
        renderDropdown(filtrados);
    });

    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-container')) {
            searchResults.style.display = 'none';
        }
    });

    function actualizarSeleccionados() {
        selectedCount.textContent = productosSeleccionados.length;
        summaryCount.textContent = productosSeleccionados.length;

        if (productosSeleccionados.length === 0) {
            selectedList.innerHTML = '<p class="empty-tip">Sin productos seleccionados</p>';
            btnConfirm.disabled = (archivosAdjuntos.length === 0);
            return;
        }

        selectedList.innerHTML = productosSeleccionados.map((p, idx) => `
            <div class="selected-card">
                <div class="selected-card-left">
                    <img src="${p.foto_url}" class="selected-thumb" onerror="this.src='/static/placeholder_furniture.png'">
                    <div class="selected-info">
                        <span class="selected-name" title="${p.nombre}">${p.nombre}</span>
                    </div>
                </div>
                <div class="selected-card-right">
                    <input type="number" class="input-qty" min="1" max="999" value="${p.cantidad || 1}" data-idx="${idx}" title="Cantidad">
                    <button class="btn-remove" data-idx="${idx}" title="Quitar">✕</button>
                </div>
            </div>
        `).join('');

        selectedList.querySelectorAll('.input-qty').forEach(inp => {
            inp.addEventListener('change', (e) => {
                const idx = parseInt(e.target.getAttribute('data-idx'));
                const val = Math.max(parseInt(e.target.value) || 1, 1);
                productosSeleccionados[idx].cantidad = val;
            });
        });

        selectedList.querySelectorAll('.btn-remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const idx = parseInt(e.target.getAttribute('data-idx'));
                productosSeleccionados.splice(idx, 1);
                actualizarSeleccionados();
            });
        });

        btnConfirm.disabled = false;
    }

    multiFileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        files.forEach(file => {
            const isImage = file.type.startsWith('image/');
            const item = {
                file: file,
                name: file.name,
                isImage: isImage,
                previewUrl: null
            };

            if (isImage) {
                const reader = new FileReader();
                reader.onload = (evt) => {
                    item.previewUrl = evt.target.result;
                    renderArchivos();
                };
                reader.readAsDataURL(file);
            }
            archivosAdjuntos.push(item);
        });
        renderArchivos();
        multiFileInput.value = '';
    });

    function renderArchivos() {
        filesCount.textContent = archivosAdjuntos.length;
        summaryFilesCount.textContent = archivosAdjuntos.length;

        if (archivosAdjuntos.length === 0) {
            filesContainer.innerHTML = '<p class="empty-tip-files">No hay archivos adjuntos</p>';
            if (productosSeleccionados.length === 0) btnConfirm.disabled = true;
            return;
        }

        filesContainer.innerHTML = archivosAdjuntos.map((item, idx) => `
            <div class="file-box">
                <button class="file-box-remove" data-idx="${idx}" title="Eliminar">✕</button>
                ${item.isImage && item.previewUrl ? 
                    `<img src="${item.previewUrl}" class="file-thumb" alt="${item.name}">` : 
                    `<div class="file-doc-icon">📄</div>`
                }
                <span class="file-box-name" title="${item.name}">${item.name}</span>
            </div>
        `).join('');

        filesContainer.querySelectorAll('.file-box-remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const idx = parseInt(e.target.getAttribute('data-idx'));
                archivosAdjuntos.splice(idx, 1);
                renderArchivos();
            });
        });

        btnConfirm.disabled = false;
    }

    function abrirModalFoto() {
        if (!imagenGeneradaBase64) return;
        lightboxImg.src = `data:${imagenGeneradaMime};base64,${imagenGeneradaBase64}`;
        imageLightboxModal.style.display = 'flex';
    }

    function cerrarModalFoto() {
        imageLightboxModal.style.display = 'none';
    }

    btnMostrarFoto.addEventListener('click', abrirModalFoto);
    if (resultThumbImg) {
        resultThumbImg.addEventListener('click', abrirModalFoto);
    }
    btnCloseLightbox.addEventListener('click', cerrarModalFoto);

    imageLightboxModal.addEventListener('click', (e) => {
        if (e.target === imageLightboxModal) cerrarModalFoto();
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && imageLightboxModal.style.display === 'flex') cerrarModalFoto();
    });

    // Fase 6.3: Manejo de Respuesta Real o Mock
    btnConfirm.addEventListener('click', async () => {
        if (productosSeleccionados.length === 0 && archivosAdjuntos.length === 0) return;

        btnConfirm.disabled = true;
        btnConfirm.innerHTML = '<span class="spinner-inline"></span> Procesando...';
        confirmationNotice.className = 'confirmation-notice warning';
        confirmationNotice.innerHTML = '⏳ <strong>Renderizando montaje...</strong> Ajustando cuota de IA, esto puede tomar unos segundos.';
        confirmationNotice.style.display = 'block';

        try {
            const detalleProductos = productosSeleccionados.map(p => `${p.cantidad}x ${p.nombre} (${p.sku})`).join(', ') || 'Sin producto';
            const skus = productosSeleccionados.map(p => p.sku).join(', ') || 'N/A';
            const nombresArchivos = archivosAdjuntos.map(a => a.name);

            const res = await fetch('/api/confirm-and-save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    productos: productosSeleccionados,
                    archivos_nombres: nombresArchivos,
                    sku: skus,
                    product_name: detalleProductos,
                    notes: approvalNotes.value.trim() || 'Aprobado',
                    target_sheet: 'Hoja 1'
                })
            });

            const data = await res.json();
            if (!res.ok || !data.success) {
                throw new Error(data.message || 'Error en la solicitud');
            }

            // Manejo según si vino imagen real o Mock (Fase 6.3)
            if (data.status === 'mock') {
                confirmationNotice.className = 'confirmation-notice warning';
                confirmationNotice.innerHTML = '⚠️ <strong>Render de prueba:</strong> El flujo funciona, pero la cuota de IA está llena.';
            } else {
                confirmationNotice.className = 'confirmation-notice success';
                confirmationNotice.innerHTML = '✅ <strong>Renderizado con IA exitoso</strong> y registrado en Sheets.';
            }
            confirmationNotice.style.display = 'block';

            if (data.image_base64) {
                imagenGeneradaBase64 = data.image_base64;
                imagenGeneradaMime = data.mime_type || 'image/svg+xml';

                // Mostrar miniatura en el panel 3
                resultThumbImg.src = `data:${imagenGeneradaMime};base64,${imagenGeneradaBase64}`;
                resultThumbWrapper.style.display = 'flex';

                // Activar botón flotante 'MOSTRAR FOTO'
                btnMostrarFoto.style.display = 'inline-flex';

                // Abrir modal automáticamente en grande
                abrirModalFoto();
            }

        } catch (err) {
            confirmationNotice.className = 'confirmation-notice error';
            confirmationNotice.textContent = `❌ ${err.message}`;
            confirmationNotice.style.display = 'block';
        } finally {
            btnConfirm.disabled = false;
            btnConfirm.innerHTML = 'Confirmar';
        }
    });
});
