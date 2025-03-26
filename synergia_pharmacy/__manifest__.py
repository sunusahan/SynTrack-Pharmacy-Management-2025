# -*- coding: utf-8 -*-
{
    'name': 'Synergia Pharmacy Management Base',
    'version': '1.2',
    'category': 'Inventory/Sales',
    'sequence': 35,
    'summary': 'Pharmcay Management related views Customized',
    'website': 'https://synergiasoft.com/',
    'depends': ['product', 'stock', 'synergia_barcode_report', 'point_of_sale', 'web','account'],
    'data': [
        'data/pharmacy_receipt.xml',
        'security/ir.model.access.csv',
        'views/product.xml',
        'reports/lot_barcode.xml',
        'reports/synergia_pharmacy_receipt.xml',
        'views/insurance_plan.xml',
        'views/res_partner.xml',
        'views/master_data.xml',
        'views/pos_order.xml',
        'views/account_move.xml',
    ],
'assets': {
        'web.assets_backend': [
            'synergia_pharmacy/static/src/components/eid_widget.js',
            'synergia_pharmacy/static/src/components/eid_widget.xml'
            ],
},
    'installable': True,
    'application': False,
}
