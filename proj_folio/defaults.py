# CUSTOM DEFAULTS

DEFAULT_NO_IMAGE_URL = 'https://static.thenounproject.com/png/1554489-200.png'

# Defaults values to generate demo staff user
staff_user_username_demo = 'General_Kenobi'
staff_user_password_demo = 'staffpassword'
staff_user_email_demo = 'hello@the.re'

# Defaults values to generate demo categories
category_filters_demo = ('Color', 'Size', 'Material')

# Defaults values to generate demo products
rnd_stock_demo = (3, 15)
rnd_discount_demo = (0, 0, 10, 15)
rnd_cost_price_demo = (5, 199)
rnd_selling_price_demo = (200, 3500)
products_to_generate_demo = {
    'Little Blue Riding Hood (M)': {
        'description': 'A knitted blue hat, nice and pretty. M-size (demo)',
        'category': 'Hats',
        'tags': ('blue', 'hat', 'wool', 'winter', 'cold'),
        'attributes': {"Color": "Blue", "Size": "Medium", "Material":"Wool"},
        'photos': (
            'https://d3312htug2rvv.cloudfront.net/img/600/744/resize/productImages/2021/04/4652517/eb51f9dbb5d57dfbbdceb2c3b4da186c_1.jpeg',
            'https://d3312htug2rvv.cloudfront.net/img/600/744/resize/productImages/2021/04/4652517/eb08c5e59ee4e014e78f557a4878bbf2_1.jpeg',
            'https://d3312htug2rvv.cloudfront.net/img/600/744/resize/productImages/2021/04/4652517/164ddcef653be22456546ac444044a70_1.jpeg',
            ),
        },
    'Little Red Riding Hood (S)': {
        'description': 'A knitted red hat, nice and pretty. S-size (demo)',
        'category': 'Hats',
        'tags': ('red', 'hat', 'wool', 'winter', 'cold'),
        'attributes': {"Color": "Red", "Size": "Small", "Material":"Wool"},
        'photos': (
            'https://www.fourrure-privee.com/6736-atmn_xlarge/red-woolen-cap-courchevel-and-fox-fur-tassel.jpg',
            'https://www.fourrure-privee.com/6737-atmn_large/red-woolen-cap-courchevel-and-fox-fur-tassel.jpg',
            ),
        },
    'Little Red Riding Hood (M)': {
        'description': 'A knitted red hat, nice and pretty. M-size (demo)',
        'category': 'Hats',
        'tags': ('red', 'hat', 'wool', 'winter', 'cold'),
        'attributes': {"Color": "Red", "Size": "Medium", "Material":"Wool"},
        'photos': (
            'https://www.fourrure-privee.com/6736-atmn_xlarge/red-woolen-cap-courchevel-and-fox-fur-tassel.jpg',
            'https://www.fourrure-privee.com/6737-atmn_large/red-woolen-cap-courchevel-and-fox-fur-tassel.jpg',
            ),
        },
    'Ruby Anklet': {
        'description': 'Handcrafted Ruby Cluster Ankle Bracelet (demo)',
        'category': 'Jewelry',
        'tags': ('silver', 'ruby', 'anklet', 'foot', 'gemstone'),
        'attributes': {"Color": "White, red", "Size": "Small", "Material":"Silver, ruby"},
        'photos': (
            'https://m.media-amazon.com/images/I/517ty+57SZL._SL1112_.jpg',
            'https://m.media-amazon.com/images/I/51t2JBLLZAL._SL1152_.jpg',
            ),
        },
    'Blue Dainty Anklet': {
        'description': 'Handmade delicate blue bead anklet nice anklet for dressy occasions,you can wear this bead anklet on a trip to the beach,perfect for a cruise or beach vacation (demo)',
        'category': 'Jewelry',
        'tags': ('silver', 'gold', 'anklet', 'foot', 'blue'),
        'attributes': {"Color": "Blue", "Size": "Small", "Material":"Silver, gold"},
        'photos': (
            'https://m.media-amazon.com/images/I/619533O0ViL._AC_SX569_.jpg',
            'https://m.media-amazon.com/images/I/91CcIEmVv2L._AC_SX679_.jpg',
            ),
        },
    'Silver Flower Pendant Necklace': {
        'description': 'Pendant necklace featuring a flower design. Chain:18", Sterling Silver with 925 stamp. The ideal gift for family or friends on a special occasion (demo)',
        'category': 'Necklaces',
        'tags': ('silver', 'amethyst', 'gemstone', 'flower'),
        'attributes': {"Color": "Silver, purple", "Size": "Medium", "Material":"Silver, amethyst"},
        'photos': (
            'https://i.etsystatic.com/19038924/r/il/dff5d1/3177280110/il_794xN.3177280110_2gpm.jpg',
            'https://i.etsystatic.com/19038924/r/il/13e29f/3224987375/il_794xN.3224987375_e5nx.jpg',
            'https://i.etsystatic.com/19038924/r/il/8bf6a1/3224987259/il_794xN.3224987259_5dib.jpg',
            'https://i.etsystatic.com/19038924/r/il/c9998c/3224987477/il_794xN.3224987477_noa8.jpg',
            'https://i.etsystatic.com/19038924/r/il/26125f/3177280148/il_794xN.3177280148_luax.jpg',
            'https://i.etsystatic.com/19038924/r/il/de7c8e/3411889043/il_794xN.3411889043_kfvb.jpg',
        ),
        },
    'Stainless Steel Vampire Coffin Ring': {
        'description': 'Solid Stainless Steel, Never Rust or Green Finger, Comfort Fit Strong and Solid, Hypoallergenic, Safe to Wear in Water (demo)',
        'category': 'Rings',
        'tags': ('steel', 'creepy', 'coffin', 'vampire'),
        'attributes': {"Color": "Silver, black", "Size": "Small", "Material":"Stainless Steel"},
        'photos': (
            'https://m.media-amazon.com/images/I/51ZGJJTuNgL._AC_UY535_.jpg',
            'https://m.media-amazon.com/images/I/61gOGFihdvL._AC_UY535_.jpg',
            'https://m.media-amazon.com/images/I/61rFQBsTPiL._AC_UY535_.jpg',
            'https://m.media-amazon.com/images/I/61L4wv5vOIL._AC_UY535_.jpg',
            'https://m.media-amazon.com/images/I/61tOM+oRFSL._AC_UY535_.jpg',
            'https://m.media-amazon.com/images/I/61sZ77NaTFL._AC_UY535_.jpg',
        ),
        },
    'Stainless Steel Eye of God Ring': {
        'description': 'Hypoallergenic: Guaranteed to be Lead & Nickel free. Fade resistant (demo)',
        'category': 'Rings',
        'tags': ('steel', 'creepy', 'eye', 'scary'),
        'attributes': {"Color": "Silver, black", "Size": "Medium", "Material":"Stainless Steel"},
        'photos': (
            'https://m.media-amazon.com/images/I/71WIDg47sAL._AC_UL1320_.jpg',
            'https://m.media-amazon.com/images/I/71aujoRnQGL._AC_UL1500_.jpg',
            'https://m.media-amazon.com/images/I/71UV0HeHQcL._AC_UL1500_.jpg',
            'https://m.media-amazon.com/images/I/71SwlL+E2dL._AC_UL1500_.jpg',
            'https://m.media-amazon.com/images/I/81D1L5NCVpL._AC_UL1500_.jpg',
        ),
        },
}
