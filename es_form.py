class GiftGuideSearchForm(RingSearchForm):

    product_class = CommaSeparatedCharField(required=False)

    def clean_metal(self):
        metals = self.cleaned_data.get('metal', '')
        metal_list = []
        for metal in metals:
            if product_define.FINISHED_JEWELRY_METAL_MAP.get(metal):
                metal_list.extend(product_define.FINISHED_JEWELRY_METAL_MAP.get(metal))
            else:
                metal_list.append(metal)
        return metal_list

    def search(self, ignore_kls=False, user_can_preview=False, products_upc=None, page_name=None):
        if user_can_preview:
            # sqs = super(RingSearchForm, self).search().narrow('valid:true OR can_be_previewed:true').exclude(exclude=True).using('product')
            sqs = super(RingSearchForm, self).search().filter(Q('term', valid=True) | Q('term', can_be_previewed=True)).exclude('term', exclude=True)
        else:
            # sqs = super(RingSearchForm, self).search().narrow('valid:true').exclude(exclude=True).using('product')
            sqs = super(RingSearchForm, self).search().filter('term', valid=True).exclude('term', exclude=True)

        # sqs = sqs.filter(upc__in=products_upc)
        sqs = self.query_currency_price(sqs)
        sqs = sqs.filter('terms', upc=list(products_upc))

        if self.is_valid():
            if self.cleaned_data.get('metal'):
                metal = self.cleaned_data['metal']
                # 'all' == 'Default View', for new filter 'Default View' is change to 'all'
                # if 'all' in metal:
                #     sqs = sqs.filter(SQ(product_class='Wedding Bands', is_default=True) | SQ(product_class__in=('Pre-Set Earrings', 'Pre-Set Pendants', 'Bracelets')))
                if 'all' not in metal:
                    # sqs = sqs.filter(metal__in=metal)
                    if self.data.get('tocari_metal') == 'is_true':
                        if 'Default View' in metal:
                            sqs = sqs.filter('term', is_default=True)
                        else:
                            if 'Rose Gold' in metal:
                                metal.append('14K Rose Gold')
                                metal.append('18K Rose Gold')
                            if 'Yellow Gold' in metal:
                                metal.append('18K Yellow Gold')
                                metal.append('14K Yellow Gold')
                            if 'White Gold' in metal:
                                metal.append('18K White Gold')
                                metal.append('14K White Gold')
                            sqs = sqs.filter('terms', metal=metal)
                    else:
                        sqs = sqs.filter('terms', metal=metal)

            if self.cleaned_data.get('product_class'):
                product_class = self.cleaned_data['product_class']
                if product_class != ['all']:
                    if 'Engagement Rings' in product_class:
                        product_class.remove('Engagement Rings')
                        product_class.extend(['Uncerted Preset Rings', 'CYO Rings'])
                    # sqs = sqs.filter(product_class__in=product_class)
                    sqs = sqs.filter('terms', product_class=product_class)

            part_qs = [self.get_page_range_query(), self.get_select_style_query(), self.get_shipping_day_query()]
            for qs in part_qs:
                if qs:
                    sqs = sqs.filter(qs)
        sqs = self.sort_(sqs, products_upc)

        # FT-21803
        if page_name in ('diamonds-that-care', 'Simone-I-Smith'):
            gift_guide_items = GiftGuidePageItem.objects.filter(page__name=page_name)
            gift_guide_image_dict = {}
            for i in gift_guide_items:
                if i.product_image:
                    gift_guide_image_dict[i.product] = i.product_image.url

            if gift_guide_image_dict:
                for upc in gift_guide_image_dict:
                    for product in sqs:
                        if product['upc'] == upc:
                            product['image'] = gift_guide_image_dict[upc]
                            product['image_original'] = gift_guide_image_dict[upc]

        return sqs

    def get_page_range_query(self):
        if self.cleaned_data.get('price_range'):
            price_field = 'price'
            if self.cleaned_data.get('currency') and self.cleaned_data['currency'] != 'USD':
                price_field = '%s_price' % self.cleaned_data['currency']
            qs = None
            for start, end in self.cleaned_data['price_range']:
                # part_qs = SQ(**{'%s__gte' % price_field: start,
                #                 '%s__lte' % price_field: end})
                # HARDCODE
                if end == Decimal("Infinity"):
                    end = 999999999
                part_qs = Q({"range": {price_field: {"gte": start}}}) & Q({"range": {price_field: {"lte": end}}})
                if not qs:
                    qs = part_qs
                else:
                    qs = qs | part_qs
            return qs

    def get_shipping_day_query(self):
        shipping_days = self.data.get('shipping_day')
        part_qs = None
        if shipping_days:
            for vendor in list(shipping_days.keys()):
                # qs = SQ(shipping_day__lte=shipping_days[vendor], vendor__exact=vendor)
                qs = Q({'range': {'shipping_day': {"lte": shipping_days[vendor]}}}) & Q('term', vendor=vendor)
                if part_qs is None:
                    part_qs = qs
                else:
                    part_qs = part_qs | qs
        return part_qs

    def get_select_style_query(self):
        if self.cleaned_data.get('selected_style'):
            selected_style = self.cleaned_data['selected_style']
            part_qs = None
            for s in selected_style:
                qs = None
                if s == 'none':
                    #qs = SQ(type_of_gemstone='none', has_sidestones=False) | SQ(setting_style_override__in=['Solitaire'])
                    qs = (Q('term', type_of_gemstone='none') & Q('term', has_sidestones=False)) | Q('terms', setting_style_override=['Solitaire'])
                elif s == 'labcreateddiamond':
                    # qs = SQ(product_class__exact__in=(category_define.CATEGORY_PENDANTS, category_define.CATEGORY_EARRINGS),
                    #     sidestones__in=('labcreateddiamond', 'Lab Created Diamond', 'lab created diamond')) | SQ(
                    #     product_class__exact__in=(category_define.CATEGORY_PENDANTS, category_define.CATEGORY_EARRINGS),
                    #     type_of_gemstone__in=('labcreateddiamond', 'Lab Created Diamond', 'lab created diamond'))| SQ(sidestones__in=('labcreateddiamond', 'Lab Created Diamond', 'lab created diamond'), product_class__exact=category_define.CATEGORY_BRACELETS)

                    qs = (Q('terms', product_class=(category_define.CATEGORY_PENDANTS, category_define.CATEGORY_PENDANTS)) & Q('terms', sidestones=('labcreateddiamond', 'Lab Created Diamond', 'lab created diamond'))) | (Q('terms', product_class=[category_define.CATEGORY_PENDANTS, category_define.CATEGORY_EARRINGS])) & Q('terms', type_of_gemstone=('labcreateddiamond', 'Lab Created Diamond', 'lab created diamond')) | (Q('term', product_class=category_define.CATEGORY_BRACELETS) & Q('terms', type_of_gemstone=('labcreateddiamond', 'Lab Created Diamond', 'lab created diamond')))
                elif s == 'diamond_g':
                    # qs = (SQ(product_class__exact__in=(category_define.CATEGORY_PENDANTS, category_define.CATEGORY_EARRINGS),
                    #     sidestones__in=('diamond', 'diamonds')) & SQ(
                    #     product_class__exact__in=(category_define.CATEGORY_PENDANTS, category_define.CATEGORY_EARRINGS),
                    #     type_of_gemstone__in=('diamond',))) | SQ(
                    #     has_sidestones=False, product_class__exact__in=(category_define.CATEGORY_PENDANTS, category_define.CATEGORY_EARRINGS),
                    #     type_of_gemstone__in=('diamond',)) | SQ(sidestones__in=('diamond', 'diamonds'), product_class__exact=category_define.CATEGORY_BRACELETS)
                    qs = ((Q('terms', product_class=(category_define.CATEGORY_PENDANTS, category_define.CATEGORY_EARRINGS)) & Q('terms', sidestones=('diamond', 'diamonds'))) & (Q('terms', product_class=(category_define.CATEGORY_PENDANTS, category_define.CATEGORY_EARRINGS)) & Q('terms', type_of_gemstone=('diamond',)))) | (Q('term', has_sidestones=False) & Q('terms', product_class=(category_define.CATEGORY_PENDANTS, category_define.CATEGORY_EARRINGS)) & Q('terms', type_of_gemstone=('diamond',))) | (Q('terms', sidestones=('diamond', 'diamonds')) & Q('term', product_class=category_define.CATEGORY_BRACELETS))
                elif s == 'sapphire_g':
                    # qs = SQ(type_of_gemstone='sapphire') | SQ(
                    #     product_class__exact__in=(category_define.CATEGORY_EARRINGS,
                    #                               category_define.CATEGORY_PENDANTS,
                    #                               category_define.CATEGORY_BRACELETS),
                    #     sidestones='sapphire')
                    qs = Q('term', type_of_gemstone='sapphire') | (Q('terms', product_class=(category_define.CATEGORY_EARRINGS, category_define.CATEGORY_PENDANTS, category_define.CATEGORY_BRACELETS)) & Q('term', sidestones='sapphire'))
                elif s == 'aquamarine_g':
                    # qs = SQ(type_of_gemstone='aquamarine') | SQ(
                    #     product_class__exact__in=(category_define.CATEGORY_EARRINGS,
                    #                               category_define.CATEGORY_PENDANTS,
                    #                               category_define.CATEGORY_BRACELETS),
                    #     sidestones='aquamarine')
                    qs = Q('term', type_of_gemstone='aquamarine') | (Q('terms', product_class=(category_define.CATEGORY_EARRINGS, category_define.CATEGORY_PENDANTS, category_define.CATEGORY_BRACELETS)) & Q('term', sidestones='aquamarine'))
                elif s == 'other_cg':
                    # qs = SQ(type_of_gemstone=Raw('*')) & ~SQ(type_of_gemstone__in=('diamond', 'sapphire', 'aquamarine', 'labcreateddiamond','none')) | SQ(type_of_gemstone=Raw('*')) & ~SQ(sidestones__in=('diamond', 'sapphire', 'aquamarine', 'labcreateddiamond', 'none', ))
                    qs = (Q('wildcard', type_of_gemstone='*') & ~Q('terms', type_of_gemstone=('diamond', 'sapphire', 'aquamarine', 'labcreateddiamond','none'))) | (Q('wildcard', type_of_gemstone='*') & ~Q('terms', sidestones=('diamond', 'sapphire', 'aquamarine', 'labcreateddiamond','none',)))
                elif s == 'pearl':
                    qs = Q('term', type_of_gemstone='pearl')  | (Q(
                        'terms', product_class=(category_define.CATEGORY_EARRINGS,
                                                          category_define.CATEGORY_PENDANTS,
                                                          category_define.CATEGORY_BRACELETS)) & Q('term', sidestones='pearl'))
                elif s == 'emerald':
                    qs = Q('term', type_of_gemstone='emerald')  | (Q(
                        'terms', product_class=(category_define.CATEGORY_EARRINGS,
                                                          category_define.CATEGORY_PENDANTS,
                                                          category_define.CATEGORY_BRACELETS)) & Q('term', sidestones='emerald'))
                elif s == 'multigemstone':
                    qs = Q('term', is_multi_gemstone=True)
                if qs:
                    if part_qs is None:
                        part_qs = qs
                    else:
                        part_qs = part_qs | qs
            return part_qs

    def sort_(self, sqs, products_upc):
        results = sqs.execute_all()
        sorted_results = sorted(results, key=lambda item: products_upc.index(item["upc"]))
        return sorted_results