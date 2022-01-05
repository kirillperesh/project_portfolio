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
        'photos': '???'
        },
    'Little Red Riding Hood (S)': {
        'description': 'A knitted red hat, nice and pretty. S-size (demo)',
        'category': 'Hats',
        'tags': ('red', 'hat', 'wool', 'winter', 'cold'),
        'attributes': {"Color": "Red", "Size": "Small", "Material":"Wool"},
        'photos': '???'
        },
    'Little Red Riding Hood (M)': {
        'description': 'A knitted red hat, nice and pretty. M-size (demo)',
        'category': 'Hats',
        'tags': ('red', 'hat', 'wool', 'winter', 'cold'),
        'attributes': {"Color": "Red", "Size": "Medium", "Material":"Wool"},
        'photos': '???'
        },
    'Ruby Anklet': {
        'description': 'Handcrafted Ruby Cluster Ankle Bracelet (demo)',
        'category': 'Jewelry',
        'tags': ('silver', 'ruby', 'anklet', 'foot', 'gemstone'),
        'attributes': {"Color": "White, red", "Size": "Small", "Material":"Silver, ruby"},
        'photos': '???'
        },
    'Blue Dainty Anklet': {
        'description': 'Handmade delicate blue bead anklet nice anklet for dressy occasions,you can wear this bead anklet on a trip to the beach,perfect for a cruise or beach vacation (demo)',
        'category': 'Jewelry',
        'tags': ('silver', 'gold', 'anklet', 'foot', 'blue'),
        'attributes': {"Color": "Blue", "Size": "Small", "Material":"Silver, gold"},
        'photos': '???'
        },
    'Silver Flower Pendant Necklace': {
        'description': 'Pendant necklace featuring a dainty cutout flower design with a floral cluster of genuine African amethyst stones set in high polished sterling silver (demo)',
        'category': 'Necklaces',
        'tags': ('silver', 'amethyst', 'gemstone', 'flower'),
        'attributes': {"Color": "Silver, purple", "Size": "Medium", "Material":"Silver, amethyst"},
        'photos': '???'
        },
    'Stainless Steel Vampire Coffin Ring': {
        'description': 'Solid Stainless Steel, Never Rust or Green Finger, Comfort Fit Strong and Solid, Hypoallergenic, Safe to Wear in Water (demo)',
        'category': 'Rings',
        'tags': ('steel', 'creepy', 'coffin', 'vampire'),
        'attributes': {"Color": "Silver, black", "Size": "Small", "Material":"Stainless Steel"},
        'photos': '???'
        },
    'Stainless Steel Eye of God Ring': {
        'description': 'Hypoallergenic: Guaranteed to be Lead & Nickel free. Fade resistant (demo)',
        'category': 'Rings',
        'tags': ('steel', 'creepy', 'eye', 'scary'),
        'attributes': {"Color": "Silver, black", "Size": "Medium", "Material":"Stainless Steel"},
        'photos': '???'
        },
}