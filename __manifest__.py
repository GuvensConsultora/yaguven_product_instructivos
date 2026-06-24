{
    "name": "Yaguven - Instructivos por producto (histórico por lote)",
    "summary": (
        "Asocia a cada producto su instructivo de armado vigente y el "
        "histórico de instructivos por lote. Modelo propio con many2one a "
        "product.template (no invasivo) y apartado en la ficha del website "
        "Mosconi. No afecta a los demás websites."
    ),
    "version": "18.0.1.1.0",
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
    "installable": True,
    "application": False,
    "auto_install": False,
}
