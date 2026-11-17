import base64
import io
import re
import zipfile

from odoo import http
from odoo.http import content_disposition, request
from odoo.tools.mimetypes import guess_mimetype

_EXTENSIONES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
    "image/svg+xml": "svg",
}


def _nombre_archivo(texto):
    """Nombre de archivo legible y seguro: sin tildes raras ni separadores."""
    texto = re.sub(r"[^\w\s-]", "", texto or "producto", flags=re.UNICODE)
    return re.sub(r"[\s]+", "-", texto.strip())[:80] or "producto"


class YaguvenProductImagenes(http.Controller):
    """Botón «Imágenes del producto» de la ficha web: arma en el momento un .zip
    con las fotos que el producto ya tiene en Odoo (principal + extra del
    template + las propias de cada variante). No guarda nada.

    Sólo responde para productos publicados y visibles en el sitio que hace el
    pedido: el mismo criterio que la ficha, así no se pueden bajar fotos de un
    producto que el visitante no puede ver.
    """

    def _producto_visible(self, tmpl_id):
        """El producto, con sudo, sólo si está publicado y visible en este sitio."""
        tmpl = request.env["product.template"].sudo().browse(tmpl_id).exists()
        if (
            not tmpl
            or not tmpl.is_published
            or (tmpl.website_id and tmpl.website_id != request.website)
        ):
            raise request.not_found()
        return tmpl

    def _descargar_binario(self, registro, campo, nombre):
        if not registro[campo]:
            raise request.not_found()
        stream = request.env["ir.binary"]._get_stream_from(
            registro, campo, filename=nombre, mimetype="application/pdf"
        )
        return stream.get_response(as_attachment=True)

    @http.route(
        "/yaguven/instructivo/<int:inst_id>/pdf",
        type="http", auth="public", website=True, sitemap=False,
    )
    def descargar_instructivo(self, inst_id, **kw):
        # El modelo no da acceso a portal/público: se lee con sudo, sólo el PDF
        # de un instructivo cuyo producto está publicado en este sitio.
        inst = request.env["yaguven.product.instructivo"].sudo().browse(inst_id).exists()
        if not inst or not inst.active:
            raise request.not_found()
        self._producto_visible(inst.product_tmpl_id.id)
        nombre = inst.archivo_filename or "%s.pdf" % _nombre_archivo(inst.name)
        return self._descargar_binario(inst, "archivo", nombre)

    @http.route(
        "/yaguven/producto/<int:tmpl_id>/ficha-tecnica",
        type="http", auth="public", website=True, sitemap=False,
    )
    def descargar_ficha_tecnica(self, tmpl_id, **kw):
        tmpl = self._producto_visible(tmpl_id)
        nombre = tmpl.ficha_tecnica_filename or "%s-ficha-tecnica.pdf" % _nombre_archivo(tmpl.name)
        return self._descargar_binario(tmpl, "ficha_tecnica", nombre)

    @http.route(
        "/yaguven/producto/<int:tmpl_id>/imagenes",
        type="http",
        auth="public",
        website=True,
        sitemap=False,
    )
    def descargar_imagenes(self, tmpl_id, **kw):
        tmpl = self._producto_visible(tmpl_id)

        imagenes = tmpl.yaguven_imagenes_descarga()
        if not imagenes:
            raise request.not_found()

        base = _nombre_archivo(tmpl.name)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for n, datos in enumerate(imagenes, start=1):
                ext = _EXTENSIONES.get(guess_mimetype(datos), "jpg")
                zf.writestr("%s-%02d.%s" % (base, n, ext), datos)

        contenido = buffer.getvalue()
        return request.make_response(
            contenido,
            headers=[
                ("Content-Type", "application/zip"),
                ("Content-Length", str(len(contenido))),
                ("Content-Disposition", content_disposition("%s-imagenes.zip" % base)),
            ],
        )
