import base64

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # Inverse one2many: NO agrega columna a la tabla nativa (C.2). Solo expone
    # los instructivos del propio módulo en la ficha del producto.
    instructivo_ids = fields.One2many(
        "yaguven.product.instructivo",
        "product_tmpl_id",
        string="Instructivos",
    )
    instructivo_actual_id = fields.Many2one(
        "yaguven.product.instructivo",
        string="Instructivo actual",
        compute="_compute_instructivo_actual",
        help="Instructivo vigente del producto (el marcado como actual).",
    )
    instructivo_count = fields.Integer(
        string="Cant. instructivos",
        compute="_compute_instructivo_actual",
    )

    # Ficha técnica para descargar desde la web. Campos nuevos del módulo, no
    # redefine ningún nativo (C.2). Misma lógica que el instructivo: el PDF
    # cargado en Odoo tiene prioridad; si no hay, se usa el link público.
    # Ambos vacíos = la web no muestra el renglón.
    ficha_tecnica = fields.Binary(
        string="Ficha técnica (PDF)",
        attachment=True,
        help="PDF con medidas, materiales y especificaciones del producto.",
    )
    ficha_tecnica_filename = fields.Char(string="Nombre de archivo de la ficha técnica")
    ficha_tecnica_url = fields.Char(
        string="Ficha técnica (link)",
        help="Link público a la ficha técnica. Se usa si no hay PDF cargado.",
    )

    def yaguven_imagenes_descarga(self):
        """Fotos del producto para el .zip de la web, en bytes y sin repetidas:
        principal, extra del template y las propias de cada variante.
        La ficha usa esta misma función para decidir si muestra el botón."""
        self.ensure_one()
        tmpl = self.sudo()
        candidatas = [tmpl.image_1920]
        candidatas += tmpl.product_template_image_ids.mapped("image_1920")
        for variante in tmpl.product_variant_ids:
            candidatas.append(variante.image_variant_1920)
            candidatas += variante.product_variant_image_ids.mapped("image_1920")
        vistas, imagenes = set(), []
        for b64 in candidatas:
            if not b64 or b64 in vistas:
                continue
            vistas.add(b64)
            imagenes.append(base64.b64decode(b64))
        return imagenes

    @api.depends("instructivo_ids", "instructivo_ids.es_actual", "instructivo_ids.product_id")
    def _compute_instructivo_actual(self):
        for tmpl in self:
            tmpl.instructivo_count = len(tmpl.instructivo_ids)
            # El "actual" general es el de alcance template (sin variante).
            tmpl.instructivo_actual_id = tmpl.instructivo_ids.filtered(
                lambda r: r.es_actual and not r.product_id
            )[:1]

    def resolver_instructivos(self, product_id=False):
        """Devuelve (actual, historicos) resolviendo el alcance variante→template.

        Si la variante indicada tiene instructivos propios (hook de variante),
        priman sobre los del template; si no, se usan los del template (los de
        product_id vacío, que aplican a todas las variantes). Hoy el hook está
        dormido en Mosconi: todos los instructivos son de alcance template.
        Pensado para un render por variante (controller/JS) como ladrillo futuro.
        """
        self.ensure_one()
        base = False
        if product_id:
            propios = self.instructivo_ids.filtered(
                lambda r: r.product_id.id == product_id
            )
            base = propios or False
        if not base:
            base = self.instructivo_ids.filtered(lambda r: not r.product_id)
        actual = base.filtered("es_actual")[:1]
        historicos = base.filtered(lambda r: not r.es_actual)
        return actual, historicos
