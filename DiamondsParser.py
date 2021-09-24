#!/usr/bin/env python
from bearth.script.FileParser import FileParser
from bearth.script.Parser import DataError, get_logger

SHAPE_MAPPING = {
    'Round Brilliant': 'Round',
    'Emerald Cut': 'Emerald',
    'Oval Brilliant': 'Oval',
    'Pear Brilliant': 'Pear',
    # 'TR': 'Do not import',
}

class GrownDiamondsParser(FileParser):

    HEADER_MAPPING = {
        'lot #': 'vendor_stock_number',
        'shape': 'shape',
        'color': 'color',
        'clarity': 'clarity',
        'weight': 'carat',
        'lab': 'report',
        'cut grade': 'cut',
        'polish': 'polish',
        'symmetry': 'symmetry',
        'fluor': 'fluorescence',
        'rapaport price': 'rap_price',
        '% off rap': 'rap_percent',
        'price/ct': 'be_price',
        'certificate #': 'certificate_number',
        'length': 'length',
        'width': 'width',
        'depth': 'depth',
        'depth %': 'depth_percent',
        'table %': 'table',
        'girdle': 'girdle',
        'culet': 'culet',
        'description/comments': 'description',
        'origin': 'origin',
        'memo status': 'available_for_memo',
        'inscription #': 'inscription',
        'cert link': 'certificate_link',
        'diamond image': 'image',
        'video': 'v360_link',
        'digital cert': 'digital_cert',
        'h&a': 'hearts_and_arrows_diamonds',
        'hearts image': 'hearts_image_link',
        'arrows image': 'arrows_image_link',
        'vendor h&a': 'vendor_hearts_and_arrows_diamonds',
    }

    def __init__(self):
        super(GrownDiamondsParser, self).__init__()
        self.content = ""
        self.log = get_logger(name='Grown Diamonds')
        self.dt = {}
        self.total_num = 0
        self.valid_num = 0
        self.stockno_prefix = 'LC'
        self.supplier = 'Grown Diamonds'
        self.SHAPE_MAPPING.update(SHAPE_MAPPING)

    def parse_node(self, values):
        row = {'vendor_stock_number': values[self.HEADER_INDEX['vendor_stock_number']],
               'shape': values[self.HEADER_INDEX['shape']],
               'carat': values[self.HEADER_INDEX['carat']],
               'color': values[self.HEADER_INDEX['color']],
               'clarity': values[self.HEADER_INDEX['clarity']],
               'rap_price': values[self.HEADER_INDEX['rap_price']],
               'rap_percent': values[self.HEADER_INDEX['rap_percent']],
               'report': values[self.HEADER_INDEX['report']],
               'measurements': self.convert_mm_by_lwd(values[self.HEADER_INDEX['length']], values[self.HEADER_INDEX['width']], values[self.HEADER_INDEX['depth']]),
               'cut': values[self.HEADER_INDEX['cut']],
               'be_price': values[self.HEADER_INDEX['be_price']],
               'table': values[self.HEADER_INDEX['table']],
               'origin': 'Lab Created',
               }
        if values[self.HEADER_INDEX['image']]:
            row['image'] = values[self.HEADER_INDEX['image']]
        if values[self.HEADER_INDEX['polish']]:
            row['polish'] = values[self.HEADER_INDEX['polish']]
        if values[self.HEADER_INDEX['symmetry']]:
            row['symmetry'] = values[self.HEADER_INDEX['symmetry']]
        if values[self.HEADER_INDEX['fluorescence']]:
            row['fluorescence'] = values[self.HEADER_INDEX['fluorescence']]
        if values[self.HEADER_INDEX['depth_percent']]:
            row['depth'] = values[self.HEADER_INDEX['depth_percent']]
        if values[self.HEADER_INDEX['girdle']]:
            row['girdle'] = values[self.HEADER_INDEX['girdle']]
        if values[self.HEADER_INDEX['culet']]:
            row['culet'] = values[self.HEADER_INDEX['culet']]
        if values[self.HEADER_INDEX['certificate_number']]:
            row['certificate_number'] = values[self.HEADER_INDEX['certificate_number']].strip()
        if values[self.HEADER_INDEX['certificate_link']]:
            row['certificate_link'] = values[self.HEADER_INDEX['certificate_link']].strip()
        if self.HEADER_INDEX.get('v360_link') and values[self.HEADER_INDEX.get('v360_link')]:
            row['v360_link'] = values[self.HEADER_INDEX.get('v360_link')]

        try:
            row['supplier'] = self.supplier
            row['available_for_memo'] = self.convert_memo(self.supplier)
            row['vendor_stock_number'] = self.covert_vendor_stockno(row['vendor_stock_number'])
            row['stock_number'] = self.convert_stockno(row['vendor_stock_number'], row['supplier'], row['available_for_memo'])
            row['carat'] = self.convert_carat(row['carat'])
            row['shape'] = self.convert_shape(row['shape'])
            row['length_width_ratio'] = self.convert_lwratio(row['measurements'], row['shape'])
            row['shape'] = self.process_shape(row['shape'], row['length_width_ratio'])
            row['rap_price'] = self.convert_rap_price(row['rap_price'])
            row['rap_percent'] = self.convert_rap_percent(row['rap_percent'])
            row['report'] = self.convert_lab(row['report'])
            row['color'] = self.convert_color(row['color'])
            row['clarity'] = self.convert_clarity(row['clarity'].replace(' ', ''))
            row['be_price'] = self.convert_beprice_with_carat(row['be_price'], row['carat'])

            if 'polish' in row:
                row['polish'] = self.convert_polish(row['polish'])
            if 'symmetry' in row:
                row['symmetry'] = self.convert_symmetry(row['symmetry'])
            if 'fluorescence' in row:
                row['fluorescence'] = self.convert_fluor(row['fluorescence'])
            if 'depth' in row:
                row['depth'] = self.convert_depth(row['depth'])
            if 'table' in row:
                row['table'] = self.convert_table(row['table'])
            if 'girdle' in row:
                row['girdle'] = self.convert_girdle(row['girdle'])
            if 'culet' in row:
                row['culet'] = self.convert_culet(row['culet'])
            if 'hearts_and_arrows_diamonds' in self.HEADER_INDEX:
                row['vendor_hearts_and_arrows_diamonds'] = self.convert_boolean(
                    values[self.HEADER_INDEX['hearts_and_arrows_diamonds']])
                row['hearts_and_arrows_diamonds'] = self.convert_hearts_and_arrows(
                    row['vendor_hearts_and_arrows_diamonds'], row['shape'], row['stock_number'], row['supplier'])
            if 'hearts_image_link' in self.HEADER_INDEX:
                row['hearts_image_link'] = self.convert_url(
                    values[self.HEADER_INDEX['hearts_image_link']])
            if 'arrows_image_link' in self.HEADER_INDEX:
                row['arrows_image_link'] = self.convert_url(
                    values[self.HEADER_INDEX['arrows_image_link']])
            cut = row['cut']
            row['cut'] = self.process_cut(cut, row['shape'], row.get('proportion'), row['polish'], row['symmetry'],
                                          row.get("girdle", ""), row.get("length_width_ratio", ""),
                                          row.get("culet", ""), row['depth'], row['table'], row['report'])

            self.validate_row(row)
            self.cleanup_row(row)
            row['price'] = self.convert_new_price_phase_two(row, self.supplier)
            if self.HEADER_INDEX.get('digital_cert'):
                row['digital_cert'] = self.convert_digital_cert(values[self.HEADER_INDEX.get('digital_cert')])
            else:
                row['digital_cert'] = False
            self.dt[row['stock_number']] = row
        except Exception as e:
            self.log.error('%s\ndiamond info: %s'%(str(e), row))
            return None

if __name__ == '__main__':
    import doctest
    doctest.testmod()
    from django.conf import settings
    from bearth.apps.dashboard.inventory import import_data
    import os
    f = open(os.path.join(settings.PROJECT_ROOT, 'tmp/grown diamonds/brilliantearth-update.csv'), 'rb').read()
    a = GrownDiamondsParser()
    res = a.load(f)
    b = import_data.import_data(res)['diamond_count']
    print(b)
