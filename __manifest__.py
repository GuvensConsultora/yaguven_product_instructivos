{
    "name": "Yaguven - Instructivos por producto (histórico por lote)",
    "summary": (
        "Asocia a cada producto su instructivo de armado vigente y el "
        "histórico de instructivos por lote. Modelo propio con many2one a "
        "product.template (no invasivo) y ficha web del sitio Mosconi en tres bloques "
        "(información, dónde comprar, consultas). No afecta a los demás websites."
    ),
    "version": "18.0.2.0.1",
    "category": "Website",
    "author": "Guvens Consultora",
    "license": "LGPL-3",
    "depends": ["website_sale"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_config_parameter.xml",
        "views/product_template_views.xml",
        "views/website_templates.xml",
    ],
    # Link del botón «Consultar»: parámetro yaguven_instructivos.consultar_url
    # (Ajustes > Técnico > Parámetros del sistema). No se precarga: sin
    # parámetro, el botón no aparece.
    "assets": {
        "web.assets_frontend": [
            "yaguven_product_instructivos/static/src/scss/ficha_producto.scss",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
