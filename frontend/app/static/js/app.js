// Métodos auxiliares para la interfaz Web

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('form-factura');
    const input = document.getElementById('id_factura');
    const btnGenerar = document.getElementById('btn-generar');
    const alerta = document.getElementById('alerta');
    const vistaPrevia = document.getElementById('vista-previa');
    const titulo = document.getElementById('preview-titulo');
    const frame = document.getElementById('pdf-frame');
    const btnDescargar = document.getElementById('btn-descargar');
    const btnImprimir = document.getElementById('btn-imprimir');

    let pdfUrl = null;

    function mostrarError(mensaje) {
        alerta.textContent = mensaje;
        alerta.hidden = false;
    }

    function ocultarError() {
        alerta.hidden = true;
        alerta.textContent = '';
    }

    function setCargando(cargando) {
        btnGenerar.disabled = cargando;
        btnGenerar.textContent = cargando ? 'Generando...' : 'Generar Factura';
    }

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const idFactura = input.value.trim();
        if (!idFactura) {
            mostrarError('Debe ingresar un número de factura');
            return;
        }

        ocultarError();
        setCargando(true);

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                headers: { 'X-Requested-With': 'fetch' },
                body: new FormData(form),
            });

            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.error || `Error ${response.status} generando la factura`);
            }

            const blob = await response.blob();
            if (pdfUrl) {
                URL.revokeObjectURL(pdfUrl);
            }
            pdfUrl = URL.createObjectURL(blob);

            titulo.textContent = `Factura ${idFactura}`;
            frame.src = pdfUrl;
            btnDescargar.href = pdfUrl;
            btnDescargar.download = `factura_${idFactura}.pdf`;
            vistaPrevia.hidden = false;
            vistaPrevia.scrollIntoView({ behavior: 'smooth' });
        } catch (err) {
            mostrarError(err.message);
        } finally {
            setCargando(false);
        }
    });

    btnImprimir.addEventListener('click', () => {
        try {
            frame.contentWindow.focus();
            frame.contentWindow.print();
        } catch (err) {
            // Algunos navegadores no permiten imprimir el visor de PDF embebido
            window.open(pdfUrl, '_blank');
        }
    });
});
