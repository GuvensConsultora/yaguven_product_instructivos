import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class YaguvenProductInstructivo(models.Model):
    _name = "yaguven.product.instructivo"
    _description = "Instructivo de armado por producto (con histórico por lote)"
    # El actual primero; luego históricos por secuencia/lote. id como desempate estable.
    # Se ordena por lote_num (entero), no por lote (texto): como texto "9" quedaba arriba de "45".
    _order = "es_actual desc, sequence, lote_num desc, id desc"

    product_tmpl_id = fields.Many2one(
        "product.template",
        string="Producto",
        required=True,
        ondelete="cascade",
        index=True,
    )
    # Hook de variante (hoy dormido: en Mosconi el único atributo de variante
    # es 'color', que no impacta el armado). Vacío = el instructivo aplica a
    # TODAS las variantes del template. Seteado = override solo para esa
    # variante (caso futuro: un atributo que sí cambie el armado modelado
    # como variante en vez de como template aparte).
    product_id = fields.Many2one(
        "product.product",
        string="Variante específica",
        ondelete="cascade",
        index=True,
        domain="[('product_tmpl_id', '=', product_tmpl_id)]",
        help="Opcional. Si se indica, el instructivo aplica solo a esa "
        "variante (override). Vacío = aplica a todas las variantes del producto.",
    )
    name = fields.Char(
        string="Nombre del instructivo",
        required=True,
        help="Nombre descriptivo del instructivo / archivo PDF "
        "(ej. 'PLACARD 22 PACK - IA (LOTE 131)').",
    )
    lote = fields.Char(
        string="Lote",
        help="Número de lote del instructivo histórico (ej. '131'). "
        "Vacío para el instructivo actual.",
    )
    lote_num = fields.Integer(
        string="Lote (número)",
        compute="_compute_lote_num",
        store=True,
        index=True,
        help="Número de lote como entero, para ordenar los históricos.",
    )
    es_actual = fields.Boolean(
        string="Es el actual",
        default=False,
        help="Marca el instructivo vigente del producto. "
        "Solo uno por producto.",
    )
    # storage A: el PDF cargado en Odoo (ir.attachment vía Binary attachment=True)
    archivo = fields.Binary(
        string="PDF",
        attachment=True,
        help="Archivo PDF del instructivo, alojado en Odoo.",
    )
    archivo_filename = fields.Char(string="Nombre de archivo")
    # storage B: link público de fallback (eldomosconi.com.ar/fotos/instructivos/)
    url = fields.Char(
        string="URL pública",
        help="Link público al PDF (fallback). Se usa en el website si el "
        "producto no tiene el PDF cargado en Odoo.",
    )
    sequence = fields.Integer(string="Secuencia", default=10)
    active = fields.Boolean(string="Activo", default=True)

    @api.depends("lote")
    def _compute_lote_num(self):
        # Toma el primer grupo de dígitos del lote ("LOTE 131" -> 131); sin dígitos -> 0.
        for inst in self:
            m = re.search(r"\d+", inst.lote or "")
            inst.lote_num = int(m.group()) if m else 0

    @api.onchange("product_id")
    def _onchange_product_id(self):
        # Si se elige la variante primero, autocompletar el template.
        if self.product_id:
            self.product_tmpl_id = self.product_id.product_tmpl_id

    @api.constrains("product_id", "product_tmpl_id")
    def _check_variante_del_template(self):
        for inst in self:
            if inst.product_id and inst.product_id.product_tmpl_id != inst.product_tmpl_id:
                raise ValidationError(
                    "La variante seleccionada no pertenece al producto '%s'."
                    % inst.product_tmpl_id.display_name
                )

    @api.constrains("es_actual", "product_tmpl_id", "product_id")
    def _check_un_solo_actual(self):
        # Un solo "actual" por alcance: el general del template (product_id
        # vacío) y, si se usa el hook, uno por cada variante.
        for inst in self:
            if not inst.es_actual:
                continue
            otros = self.search_count([
                ("product_tmpl_id", "=", inst.product_tmpl_id.id),
                ("product_id", "=", inst.product_id.id),
                ("es_actual", "=", True),
                ("id", "!=", inst.id),
            ])
            if otros:
                alcance = (
                    "la variante '%s'" % inst.product_id.display_name
                    if inst.product_id
                    else "el producto '%s'" % inst.product_tmpl_id.display_name
                )
                raise ValidationError(
                    "Ya hay un instructivo marcado como actual para %s. "
                    "Solo puede haber uno." % alcance
                )
