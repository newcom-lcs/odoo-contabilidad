{
    'name': 'Stock Valuation Layer - Información de Órdenes',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Agregar información de órdenes de venta y compra a la capa de valoración de stock',
    'description': """
        Este módulo extiende la capa de valoración de stock para incluir:
        - Número de orden (venta o compra) desde el movimiento de stock relacionado
        - Cantidad facturada desde la línea de orden de venta
        - Filtro predefinido para mostrar registros sin facturar (cantidad_facturada = 0)
    """,
    'author': 'Newcom LCS',
    'website': 'https://www.newcom-lcs.com',
    'license': 'LGPL-3',
    'depends': [
        'stock_account',
        'sale_stock',
        'purchase_stock',
    ],
    'data': [
        'views/stock_valuation_layer_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
} 