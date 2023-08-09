{
    'name': 'Material Request',
    'version': '16.0.1.0.0',
    'author': 'Ajit',
    'category': 'material',
    'sequence': 15,
    'depends': ['base_setup', 'purchase', 'stock', 'hr'],
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'data/material_request_sequence.xml',
        'data/demo_product.xml',
        'views/material_request_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}
