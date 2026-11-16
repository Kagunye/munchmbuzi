"""
Load Mbuzi Munch's real content (taken from mbuzimunch.com, the printed menu
and their social pages) into the database.

    python manage.py seed_site          # add anything missing
    python manage.py seed_site --reset  # wipe content tables and reload

Bookings and job applications are never touched.
"""

import datetime
import shutil
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import Branch, Dish, JobOpening, MenuCategory, MenuItem, Post, Review

IMG = Path(settings.BASE_DIR) / "static" / "img"

# Branch reels from @mbuzi_munch: (video, poster) relative to static/
BRANCH_REELS = {
    "Galleria Mall": ("video/reels/reel-galleria.mp4", "img/reels/reel-galleria.jpg"),
    "Delamere Naivasha": ("video/reels/reel-naivasha.mp4", "img/reels/reel-naivasha.jpg"),
}

BRANCHES = [
    dict(
        name="Golf Park", area="Ngong Racecourse", city="Nairobi", phone="0723 868 686",
        email="golfpark@mbuzimunch.com", image="branch-golfpark.jpg",
        tagline="Fresh air, golf course and racecourse views.",
        description=(
            "Our flagship at the Ngong Racecourse Golf Park. Watch the horse racing and golfers "
            "from the terrace while the grill does its work. Kid friendly, with order-to-your-spot "
            "service at the Driving Range, Padel and Putting Green via our QR menus. Home of Tabu, "
            "our events space for private parties."
        ),
        hours_weekday="07:00 – 22:00", hours_weekend="07:00 – 23:00",
        map_query="Mbuzi Munch Golf Park Ngong Racecourse Nairobi",
    ),
    dict(
        name="Galleria Mall", area="Langata Road, Karen", city="Nairobi", phone="0794 587 187",
        email="galleria@mbuzimunch.com", image="branch-galleria.jpg",
        tagline="Chilled vibes, good music, great ribs.",
        description=(
            "Find us at Galleria Mall on Langata Road. A relaxed spot with good music, superb "
            "service and the full Mbuzi Munch grill menu, perfect after shopping or for a "
            "laid-back evening."
        ),
        map_query="Mbuzi Munch Galleria Mall Langata Road Nairobi",
    ),
    dict(
        name="Buffalo Mall", area="Buffalo Mall", city="Naivasha", phone="0758 283 247",
        email="buffalo@mbuzimunch.com", image="branch-buffalo.jpg",
        tagline="Awesome African cuisine on the Naivasha road.",
        description=(
            "Our Naivasha home at Buffalo Mall, a favourite stop for travellers and locals alike. "
            "Quick, friendly service and, as our guests say, the best mbuzi in town."
        ),
        map_query="Mbuzi Munch Buffalo Mall Naivasha",
    ),
    dict(
        name="Delamere Naivasha", area="Delamere Farm Shops Stop Over", city="Naivasha",
        phone="0740 000 800", email="delamere@mbuzimunch.com", image="branch-delamere.jpg",
        tagline="Field-to-plate dining next to the model farm.", is_new=True,
        description=(
            "Our newest branch, steps from the Delamere model farm that supplies much of our "
            "produce and meat. Modern rustic interiors, shaded outdoor seating over the fields, "
            "and a games area with pool, darts, table chess and board games for the whole family."
        ),
        map_query="Delamere Farm Shops Naivasha",
    ),
]

DISHES = [
    ("Mbuzi Leg Deluxe", "Free-range goat leg with onions, spices and sauce. Serves 2–3.", "2,600", "food", "mbuzi-leg.jpg"),
    ("T-Bone Steak", "400g grilled steak with pepper sauce, potato wedges and spinach.", "1,950", "food", "tbone-fries.jpg"),
    ("Whole Tilapia", "Lake Victoria tilapia, fried or fricassee, with ugali and greens.", "970", "food", "tilapia-platter.jpg"),
    ("Kuku Choma", "Flame-grilled chicken infused with our secret herb blend.", "1,100", "food", "chicken-platter.jpg"),
    ("Choma Wraps", "Grilled kuku or mbuzi wrapped with peppers and onions.", "700", "food", "wraps-fries.jpg"),
    ("Boran Big Beefy", "Home-made lean beef burger with all the trimmings.", "900", "food", "burger.jpg"),
    ("Kuku & Mbuzi Melts", "Toasted quesadillas with kachumbari and dips.", "800", "food", "samosa-platter.jpg"),
    ("Masala Chips", "Our legendary chips tossed in a spicy masala sauce.", "400", "food", "masala-chips.jpg"),
    ("Iced Tea", "Brewed in-house, served over ice.", "250", "drink", "drink-iced-tea.jpg"),
    ("Virgin Mojito", "Fresh mint, lime and soda.", "350", "drink", "drink-mojito.jpg"),
    ("Pink Cat Martini", "Gordon's Pink, pineapple and grenadine.", "700", "drink", "drink-cocktail.jpg"),
    ("Strawberry Lemonade", "House lemonade with crushed strawberries.", "380", "drink", "drink-juice.jpg"),
    ("Mocha Milkshake", "Thick, cold and topped with chocolate.", "450", "drink", "drink-milkshake.jpg"),
]

REVIEWS = [
    ("Maurice", "A place of fresh air and lovely view of the golf course and horseracing, a variety of food choices, kid friendly and very helpful staff!", "Golf Park"),
    ("Brian", "The choma was reaaaally good! I loved the fries. Great ribs and some fine wraps. Loved it!", "Golf Park"),
    ("Benedict", "Great ribs and some fine wraps. Loved it! Keep coming back.", "Galleria Mall"),
    ("Kimathi", "The customer service is superb. If you like chilled places with good music, this is definitely it!", "Galleria Mall"),
    ("Sam", "The attendant was very lovely. Got served quickly and the meat was fantastic!", "Buffalo Mall"),
    ("Anna", "Awesome African cuisine. Best Mbuzi!", "Buffalo Mall"),
    ("Cindy", "The service was fast and friendly, and the steak was cooked to absolute perfection. Highly recommended!", "Delamere Naivasha"),
    ("Cindy", "Incredible African food. The Mbuzi is a must-order. Perfection!", "Delamere Naivasha"),
]

# (section, category, price_label, note, [(name, description, price, serves, veg, spicy), ...])
MENU = [
    ("mains", "Specialities", "", "", [
        ("Mbuzi Leg Deluxe", "With onions, spices & sauce", "2600", "Serves 2-3", False, False),
        ("Nyama Feast Platter", "Mbuzi arm, T-bone, ½ chicken, choma sausages, onion rings, ugali fries, potato wedges, kachumbari", "4300", "Serves 4", False, False),
        ("Kuku Special", "Whole / Half / Quarter", "2350 / 1250 / 750", "", False, False),
        ("T-Bone (400 grammes)", "Grilled steak with pepper sauce, potato wedges & spinach", "1950", "", False, False),
        ("Roasted Bone Marrow", "Kachumbari and brioche bun", "700", "", False, False),
        ("Whole Tilapia", "Fried or fricassee", "970 / 1100", "", False, False),
        ("Mbuzi Choma Ribs", "The traditional favourite", "950", "", False, False),
        ("Sausage Special", "Juicy sausages sliced & fried with onions, peppers & chips", "600", "", False, False),
        ("Golden Battered Kuku Strips", "Served with chips", "800", "", False, False),
    ]),
    ("mains", "Nyama Choma from our Grill", "",
     "Our meats are grilled to your specification (medium, well done etc.) and with your preferred sauce, so let your waiter know. Deluxe dishes are finished off in the pan with onions & gravy.", [
        ("Mbuzi Leg Deluxe", "", "2600", "Serves 2-3", False, False),
        ("Mbuzi Leg", "", "2450", "Serves 2-3", False, False),
        ("Mbuzi Arm Deluxe", "", "1900", "Serves 1-2", False, False),
        ("Mbuzi Arm", "", "1700", "Serves 1-2", False, False),
        ("Mbuzi Stew", "", "1100", "Serves 1", False, False),
        ("Mbuzi Choma Ribs", "", "950", "Serves 1", False, False),
        ("Mbuzi Liver Deluxe", "", "550", "Serves 1", False, False),
        ("Mbuzi Matumbo Deluxe", "", "500", "Serves 1", False, False),
    ]),
    ("mains", "Kuku Kitamu from our Pans & Grills", "", "", [
        ("Kuku Choma", "Half / Whole", "1100 / 2200", "", False, False),
        ("Kuku Wings Spicy/Saucy", "Eight pieces", "850", "", False, True),
        ("Battered Chicken & Chips", "", "800", "", False, False),
        ("Grilled Kuku Breast", "", "750", "", False, False),
    ]),
    ("mains", "Burgers", "", "", [
        ("Boran Big Beefy", "Home-made ground lean beef burger", "900", "", False, False),
        ("Kuku Cruncher", "Crunchy battered chicken", "900", "", False, False),
        ("Mbuzi Muncher", "Home-made goat-meat burger", "900", "", False, False),
        ("Filet of Fish Burger", "Crispy battered tilapia filet", "900", "", False, False),
    ]),
    ("mains", "Wraps & Quesadillas", "", "", [
        ("Kuku or Mbuzi Melt", "Chicken or goat", "800", "", False, False),
        ("Spinach and Feta Melt", "", "600", "", True, False),
        ("Falafel Wrap", "New veggie special", "700", "", True, False),
        ("Choma Wrap", "", "700", "", False, False),
        ("Choma Special Wrap", "", "700", "", False, False),
        ("Crispy Kuku Wrap", "", "700", "", False, False),
        ("Grilled Kuku Wrap", "", "700", "", False, False),
    ]),
    ("mains", "Mbuzi Munch Combos", "", "", [
        ("Mbuzi Ribs + Chips", "", "1100", "", False, False),
        ("Any Meat Melt + Chips", "", "950", "", False, False),
        ("Veggie Melt + Chips", "", "800", "", True, False),
        ("Any Burger + Chips", "", "1000", "", False, False),
        ("Any Wrap + Chips", "", "900", "", False, False),
    ]),
    ("mains", "Fish", "", "", [
        ("Fried Whole Tilapia", "", "970", "", False, False),
        ("Fricassee Whole Tilapia", "", "1100", "", False, False),
        ("Battered Fish & Chips", "", "950", "", False, False),
        ("Golden Fish Strips & Chips", "", "850", "", False, False),
    ]),
    ("mains", "Super Healthy Dishes", "", "", [
        ("Grilled Chicken Caesar Salad", "", "800", "", False, False),
        ("Greek Feta Salad", "", "700", "", True, False),
        ("Garden Salad", "", "600", "", True, False),
        ("Dahl Curry & Chapati", "", "700", "", True, True),
    ]),
    ("mains", "Sides & Snacks", "", "", [
        ("Samosas (2 pieces)", "Choice of goat, beef, chicken or feta and spinach", "320", "", False, False),
        ("Our Legendary Chips", "", "280", "", True, False),
        ("Masala Chips", "", "400", "", True, True),
        ("Masala Wedges", "", "400", "", True, True),
        ("Cheesy Chips", "", "450", "", True, False),
        ("Sauté Potatoes", "", "300", "", True, False),
        ("Potato Wedges", "", "300", "", True, False),
        ("Roast Potatoes", "", "300", "", True, False),
        ("Onion Rings", "", "280", "", True, False),
        ("Ugali", "", "100", "", True, False),
        ("Ugali Chips", "", "150", "", True, False),
        ("Rice", "", "200", "", True, False),
        ("Chapati", "", "130", "", True, False),
        ("Kachumbari", "", "150", "", True, False),
        ("Greens", "", "180", "", True, False),
        ("Pilau Chicken/Beef", "", "600", "", False, False),
    ]),
    ("mains", "Desserts", "", "", [
        ("Sticky Toffee Pudding", "Served with ice cream", "400", "", True, False),
        ("Chocolate Brownie", "Served with ice cream", "400", "", True, False),
        ("Ice Cream Assorted", "", "300", "", True, False),
    ]),
    ("breakfast", "Eggs & Omelettes", "", "Omelettes are made with 3 eggs.", [
        ("Fried or Poached Eggs", "Two eggs plus a round of toast", "330", "", True, False),
        ("Scrambled Eggs", "Three eggs and a round of toast", "400", "", True, False),
        ("Plain Omelette", "", "300", "", True, False),
        ("Cheese Omelette", "", "580", "", True, False),
        ("Spanish Omelette", "", "350", "", True, False),
    ]),
    ("breakfast", "Breakfast Combos", "", "", [
        ("Big Combo", "2 sausages, 2 fried eggs, 1 mandazi or toast, Kenyan tea", "450", "", False, False),
        ("Mid Combo", "1 samosa, 1 fried egg, 1 mandazi or toast, Kenyan tea", "400", "", False, False),
        ("Breakfast Burrito – Eggs", "Wrap with eggs, cheese, onions, peppers", "750", "", True, False),
        ("Breakfast Burrito – Spinach", "Wrap with spinach plus a cheese omelette", "650", "", True, False),
        ("Breakfast Sausage Special Combo", "Four juicy sausages sliced & fried with onions, peppers & breakfast potatoes", "600", "", False, False),
        ("Sausage and Egg Roll", "Two juicy sausages sliced, egg and brioche bun", "350", "", False, False),
        ("Giant Chocolate Chip Cookie", "", "200", "", True, False),
        ("Coffee/Tea and Cookie Combo", "", "350", "", True, False),
    ]),
    ("breakfast", "Breakfast Sides", "", "", [
        ("Sausages (two pieces)", "", "200", "", False, False),
        ("Samosas (two pieces)", "", "320", "", False, False),
        ("Spinach", "", "320", "", True, False),
        ("Wholemeal Toast (2 slices)", "", "80", "", True, False),
        ("Mandazi (per piece)", "", "60", "", True, False),
        ("Breakfast Potatoes", "", "200", "", True, False),
        ("Chapati", "", "130", "", True, False),
        ("Pancakes (4 pieces) with Honey", "", "300", "", True, False),
        ("Baked Beans on Toast", "", "350", "", True, False),
    ]),
    ("drinks", "Soft Drinks", "", "", [
        ("Soda", "Coke / Fanta / Sprite 500ml", "160", "", True, False),
        ("Still Water", "500ml / 1 litre", "150 / 250", "", True, False),
        ("Sparkling Water", "1000ml", "300", "", True, False),
        ("Fresh Juices", "500ml", "300", "", True, False),
        ("Lemonade", "", "350", "", True, False),
        ("Blueberry Lemonade", "", "380", "", True, False),
        ("Strawberry Lemonade", "", "380", "", True, False),
        ("Mint Punch", "", "400", "", True, False),
        ("Red Bull / Monster", "", "480", "", True, False),
        ("Ribena / Lucozade Boxes 150ml", "", "250", "", True, False),
        ("Lucozade Box 500ml", "", "500", "", True, False),
        ("Ribena Tot", "", "50", "", True, False),
    ]),
    ("drinks", "Mocktails", "", "", [
        ("Virgin Mojito", "", "350", "", True, False),
        ("Rock Shandy", "", "450", "", True, False),
        ("Virgin Sunrise", "", "500", "", True, False),
    ]),
    ("drinks", "Smoothies", "", "", [
        ("Strawberry", "", "500", "", True, False),
        ("Banana", "", "500", "", True, False),
        ("Mango", "", "500", "", True, False),
        ("Mixed Fruit", "", "550", "", True, False),
    ]),
    ("drinks", "Milkshakes", "", "", [
        ("Vanilla", "", "400", "", True, False),
        ("Chocolate", "", "400", "", True, False),
        ("Strawberry", "", "400", "", True, False),
        ("Espresso", "", "450", "", True, False),
        ("Mocha", "", "450", "", True, False),
        ("Caramel Espresso", "", "550", "", True, False),
    ]),
    ("drinks", "Iced Drinks", "", "", [
        ("Iced Tea", "", "250", "", True, False),
        ("Iced Coffee", "", "250", "", True, False),
        ("Iced Latte", "", "300", "", True, False),
        ("Iced Vanilla Latte", "", "400", "", True, False),
        ("Iced Mocha", "", "350", "", True, False),
        ("Iced Caramel Macchiato", "", "400", "", True, False),
    ]),
    ("drinks", "Tea", "Cup / Pot", "", [
        ("Kenyan", "", "120 / 250", "", True, False),
        ("Spiced", "", "150 / 300", "", True, False),
        ("Chamomile", "", "250", "", True, False),
        ("Minty Green", "", "250", "", True, False),
        ("Spiced Herbal", "", "250", "", True, False),
        ("Green Herbal", "", "250", "", True, False),
    ]),
    ("drinks", "Coffee", "Single / Double", "", [
        ("Americano", "", "180 / 200", "", True, False),
        ("Espresso", "", "180 / 200", "", True, False),
        ("Macchiato", "", "200 / 250", "", True, False),
        ("Café Latte", "", "200 / 250", "", True, False),
        ("Cappuccino", "", "200 / 250", "", True, False),
        ("House Coffee", "", "200 / 250", "", True, False),
        ("Mocha", "", "350", "", True, False),
        ("Caramel Macchiato", "", "330", "", True, False),
        ("Vanilla Latte", "", "330", "", True, False),
        ("Extra Syrup", "", "100", "", True, False),
    ]),
    ("drinks", "Hot Drinks", "", "", [
        ("Ginger Dawa", "", "350", "", True, False),
        ("Hot Chocolate", "", "300", "", True, False),
    ]),
    ("bar", "Cocktails", "", "", [
        ("Gin & Tonic", "Tanqueray, tonic, lime wedge", "650", "", False, False),
        ("Pink Pussy Cat Martini", "Gordon's Pink, pineapple juice, grenadine syrup", "700", "", False, False),
        ("Honolulu", "Gordon's gin, pineapple, orange & lime juice, sugar syrup, Angostura bitters", "700", "", False, False),
        ("Mojito", "Mint leaves, brown sugar, Bacardi rum, lime juice, soda water", "700", "", False, False),
        ("London Cosmopolitan", "Smirnoff vodka, lime juice, cranberry juice, triple sec", "700", "", False, False),
        ("Margarita", "Tequila Camino, triple sec & Cointreau, lime juice", "700", "", False, False),
        ("Long Island Ice Tea", "Smirnoff, Bacardi, Tequila Camino, Gordon's, triple sec & lime, sugar syrup, Coke", "900", "", False, False),
        ("Vesper Martini", "Gordon's gin, Smirnoff vodka, Martini", "700", "", False, False),
        ("Kenyan Dawa", "Smirnoff vodka, honey, lime", "700", "", False, False),
        ("Espresso Martini", "Smirnoff vodka, Kahlua, sugar syrup, espresso", "750", "", False, False),
        ("Singleton Espresso", "Singleton whisky, sugar syrup, Kahlua, espresso", "1100", "", False, False),
        ("Whisky Sour", "Bulleit bourbon, lime juice, sugar syrup, Angostura bitters", "900", "", False, False),
        ("Pimms", "Pimms No 1, lime, sugar syrup, strawberries, orange, cucumber, mint, Sprite", "800", "", False, False),
    ]),
    ("bar", "Beers", "", "", [
        ("Tusker Draft 500ml", "", "325", "", False, False),
        ("Tusker Draft Jug 2L", "", "1150", "", False, False),
        ("Tusker Lager / Manyatta", "", "400", "", False, False),
        ("White Cap", "", "450", "", False, False),
        ("Pilsner", "", "400", "", False, False),
        ("Balozi", "", "400", "", False, False),
        ("Whitecap Crisp", "", "450", "", False, False),
        ("Tusker Lite", "", "450", "", False, False),
        ("Tusker Malt", "", "450", "", False, False),
        ("Tusker Cider", "", "450", "", False, False),
        ("Guinness Smooth", "", "450", "", False, False),
        ("Hunters", "", "400", "", False, False),
        ("Heineken / Heineken 0.0", "", "500", "", False, False),
        ("Savanna", "", "500", "", False, False),
        ("Guinness Kubwa", "", "450", "", False, False),
    ]),
    ("bar", "Craft Ciders – Kenyan Originals", "", "", [
        ("Lime & Ginger", "", "450", "", False, False),
        ("Passion & Lime", "", "450", "", False, False),
        ("Pineapple & Mint", "", "450", "", False, False),
    ]),
    ("bar", "Whiskies", "Shot / Bottle", "", [
        ("Johnnie Walker Red", "", "250 / 3800", "", False, False),
        ("Jameson", "", "300 / 6000", "", False, False),
        ("Jack Daniels", "", "400 / 8000", "", False, False),
        ("Johnnie Walker Black", "", "430 / 8600", "", False, False),
        ("Bulleit Bourbon", "", "500 / 10000", "", False, False),
        ("Singleton 12yrs", "", "600 / 14000", "", False, False),
        ("Johnnie Walker Double Black", "", "450 / 11000", "", False, False),
        ("Glenfiddich 12yrs", "", "700 / 15000", "", False, False),
        ("Glenfiddich 15yrs", "", "950 / 20000", "", False, False),
        ("Johnnie Walker Gold", "", "850 / 18000", "", False, False),
        ("Singleton 18yrs", "", "1000 / 20000", "", False, False),
        ("Glenfiddich 18yrs", "", "900 / 18500", "", False, False),
        ("Johnnie Walker Blue", "", "– / 50000", "", False, False),
        ("Johnnie Walker Green", "", "800 / 17500", "", False, False),
        ("Johnnie Walker 18yrs", "", "1100 / 22000", "", False, False),
    ]),
    ("bar", "Rums", "Shot / Bottle", "", [
        ("Bacardi", "", "300 / 5000", "", False, False),
        ("Captain Morgan Gold", "", "250 / 3500", "", False, False),
        ("Captain Morgan Spiced", "", "300 / 4500", "", False, False),
    ]),
    ("bar", "Gins", "Shot / Bottle", "", [
        ("Tanqueray London", "", "300 / 6500", "", False, False),
        ("Tanqueray No. 10", "", "500 / 9500", "", False, False),
        ("Tanqueray Sevilla", "", "300 / 6500", "", False, False),
        ("Tanqueray Royal", "", "300 / 6500", "", False, False),
        ("Gordon's Dry + Pink", "", "300 / 4500", "", False, False),
        ("Gilbeys", "", "250 / 4000", "", False, False),
    ]),
    ("bar", "Vodkas", "Shot / Bottle", "", [
        ("Smirnoff Red", "", "250 / 3500", "", False, False),
        ("Ketel One", "", "400 / 7500", "", False, False),
        ("Smirnoff Ice Guarana", "Can", "400", "", False, False),
    ]),
    ("bar", "Tequilas", "Shot / Bottle", "", [
        ("Jose Cuervo", "", "300 / 5500", "", False, False),
        ("Tequila Camino", "", "300 / 5500", "", False, False),
        ("Don Julio Blanco", "", "700 / 14000", "", False, False),
        ("Don Julio Reposado", "", "750 / 15000", "", False, False),
    ]),
    ("bar", "Liqueurs & Brandies", "Shot / Bottle", "", [
        ("Bailey's", "", "300 / 5500", "", False, False),
        ("Jägermeister", "", "450 / 7500", "", False, False),
        ("Hennessy VSOP", "", "1200 / 25000", "", False, False),
        ("Viceroy", "", "250 / 3500", "", False, False),
    ]),
    ("bar", "White Wines", "Glass / Bottle", "", [
        ("La Escondida Torrontes", "Argentina · Dry white, stone fruits", "600 / 3000", "", False, False),
        ("Yellow Tail Sauvignon Blanc", "Australia · Refreshing, light with aromas of fruits", "600 / 3000", "", False, False),
        ("Versus Sweet White", "South Africa · Crisp, light with tropical fruits", "550 / 3500", "", False, False),
        ("Versus Dry White (1L)", "South Africa · Ripe apple, peach & Muscat fruits", "600 / 4000", "", False, False),
    ]),
    ("bar", "Red, Rosé & Sparkling", "Glass / Bottle", "", [
        ("Trumpeter Cab Franc", "Argentina / Mendoza · Intense, pepper & black fruits", "– / 4200", "", False, False),
        ("Trumpeter Malbec", "Argentina · A dry crisp wine", "– / 4200", "", False, False),
        ("Versus Dry Red (1L)", "South Africa · Light, ripe black fruits & berries", "600 / 4000", "", False, False),
        ("Versus Sweet Red", "South Africa · Sweet with flavours of berries", "550 / 3500", "", False, False),
        ("San Filipe Rosé", "A young fresh wine with translucent pink colour", "– / 4200", "", False, False),
        ("Gorgeous Sparkling", "Raspberry cream, strawberries, spiced peach and cherry blossom", "4200", "", False, False),
    ]),
]

POSTS = [
    dict(
        title="Mbuzi Munch Opens in Naivasha: Field-to-Plate Dining Steps from the Model Farm",
        image="branch-delamere.jpg", days_ago=20,
        excerpt=(
            "A fresh chapter for Mbuzi Munch begins in Naivasha, where our newest location brings "
            "farm-fresh flavours, a modern fit-out and family-friendly entertainment to the lakeside town."
        ),
        body="""A fresh chapter for Mbuzi Munch begins in Naivasha, where the restaurant's newest location brings farm-fresh flavours, a modern fit-out and family-friendly entertainment to the lakeside town. Literally steps from the restaurant, the adjoining model farm supplies much of the produce and meat, bringing a true field-to-plate experience that's rare in the region.

## Farm-connected dining
The restaurant sources vegetables, herbs and ethically raised goats directly from the model farm next door, so seasonal ingredients arrive at the kitchen within minutes. The close supply chain means menu items showcase peak freshness and traceability: chefs can tell guests which plot their salad greens or nyama came from, and specials shift with the farm calendar.

## A refreshed look and feel
Inside, Mbuzi Munch combines contemporary design with warm, rustic touches inspired by rural life: reclaimed wood tables, living-plant accents, large windows framing farm views, and ambient lighting for relaxed evenings. Outdoor seating overlooks the fields and is shaded for Naivasha's sunny afternoons, making it an inviting spot for everything from casual lunches to weekend family dinners.

## Family-friendly fun
Beyond the food, the new venue focuses on social dining. A dedicated games area features pool and darts for teens and adults, table chess for strategists, and family board games to keep younger guests entertained. The layout balances lively activity with quieter dining zones for guests who prefer a more intimate meal.

## Menu highlights
Expect a menu built around the farm's yields: slow-cooked goat specials, seasonal vegetable plates, wood-fired sides, and farm-to-cup beverages. Daily specials celebrate what's freshly harvested, and the kitchen offers customisable platters for groups. Sustainable practices (minimal food miles, reduced waste and composting) are woven into both kitchen and farm operations.

## Events and community
Mbuzi Munch plans farm tours, cook-along nights using picked produce, weekend family game tournaments, and pop-up markets featuring local artisans. These events aim to strengthen ties between diners, growers and the wider Naivasha community.

## Practical info
The venue welcomes walk-ins and reservations, with group-friendly menus and private-booking options for celebrations. Ample parking and outdoor space make it accessible for families and visitors from nearby towns.

## Bottom line
Mbuzi Munch's Naivasha location pairs authentic, traceable food with a lively, modern atmosphere. For locals and visitors alike, it's an easy choice for fresh, responsibly sourced meals and a relaxed spot where good food meets good fun, right next to the place it's grown.""",
    ),
    dict(
        title="Scan Me! How QR-Code Menus and M-Pesa Are Bringing Your Meal to You",
        image="qr.png", days_ago=45,
        excerpt=(
            "Two simple tech changes, QR-code menus and M-Pesa payments, are helping us deliver "
            "our signature flavours wherever you are at Golf Park."
        ),
        body="""In Nairobi's fast-moving food scene, Mbuzi Munch is blending tradition with technology to make ordering, paying and receiving goat meat dishes faster, safer and more convenient. Two simple tech changes, QR-code menus and M-Pesa payments, are helping the restaurant deliver its signature flavours "wherever you are", whether you're at the office, at home, or on the go.

## What's new
- QR-code menus: each table carries a QR code. Scan it with any smartphone camera to open a mobile-friendly menu showing photos, portion sizes, prices and allergen info. No app download required.
- M-Pesa payments: integrated M-Pesa options let customers pay instantly from their phones (Lipa na M-Pesa Paybill or Buy Goods, or an M-Pesa push prompt) so orders are confirmed faster and cash handling is minimal.

## How it works
- Scan the QR code or visit the short link.
- Browse the digital menu and add to cart.
- Pay via M-Pesa and receive an instant confirmation and estimated delivery time.
- Your order is delivered to the QR code location: Driving Range, Padel or Putting Green.

## Benefits for you
- Speed and convenience: no waiting for a physical menu or cashier; ordering and payment take minutes.
- Safety and hygiene: contactless ordering and payment reduce surfaces exchanged.
- Real-time info: updated availability and prep times prevent disappointment.
- Secure payments: M-Pesa's widespread use and transaction receipts give peace of mind.""",
    ),
]

JOBS = [
    dict(
        title="Chef",
        summary=(
            "We are currently looking for a passionate and experienced Chef to join our team. "
            "If you are creative, reliable, and love preparing great food, we would love to hear from you."
        ),
    ),
]


def attach_file(instance, field, src, filename):
    """Attach src to a File/ImageField. If media/ already holds that file (it is
    committed to git for Vercel), point at it instead of saving a duplicate copy."""
    if not src.exists():
        return
    ff = getattr(instance, field)
    target = ff.field.generate_filename(instance, filename)
    if default_storage.exists(target):
        ff.name = target.replace("\\", "/")  # always store URL-style paths
        return
    with src.open("rb") as fh:
        ff.save(filename, File(fh), save=False)


def attach(instance, field, filename, subdir):
    """Attach an image from static/img (saved in media/ as '<subdir>-<filename>')."""
    attach_file(instance, field, IMG / filename, f"{subdir}-{filename}")


class Command(BaseCommand):
    help = "Load Mbuzi Munch branches, menu, dishes, reviews, news and job openings."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete existing content first.")

    @transaction.atomic
    def handle(self, *args, reset=False, **opts):
        if opts.get("verbosity", 1) == 0:
            self.stdout.write = lambda *a, **k: None
        if reset:
            for model in (MenuItem, MenuCategory, Dish, Review, Post, JobOpening):
                model.objects.all().delete()
            for sub in ("dishes", "news"):
                shutil.rmtree(Path(settings.MEDIA_ROOT) / sub, ignore_errors=True)
            self.stdout.write("Cleared content tables.")

        branches = {}
        for i, data in enumerate(BRANCHES):
            data = dict(data)
            image = data.pop("image")
            b, created = Branch.objects.get_or_create(name=data["name"], defaults={**data, "order": i})
            if created or not b.image:
                attach(b, "image", image, "branch")
                b.save()
            # Instagram reels shown beside the branch photo (only filled in if empty)
            reel = BRANCH_REELS.get(b.name)
            if reel and not b.video:
                for field, rel in (("video", reel[0]), ("video_poster", reel[1])):
                    src = Path(settings.BASE_DIR) / "static" / rel
                    attach_file(b, field, src, src.name)
                b.save()
            branches[b.name] = b
        self.stdout.write(f"Branches: {len(branches)}")

        for i, (name, desc, price, kind, image) in enumerate(DISHES):
            d, created = Dish.objects.get_or_create(
                name=name, defaults=dict(description=desc, price=price, kind=kind, order=i)
            )
            if created:
                attach(d, "image", image, "dish")
                d.save()
        self.stdout.write(f"Signature dishes: {Dish.objects.count()}")

        for i, (author, text, branch) in enumerate(REVIEWS):
            Review.objects.get_or_create(
                author=author, text=text, defaults=dict(branch=branches.get(branch), order=i)
            )
        self.stdout.write(f"Reviews: {Review.objects.count()}")

        for ci, (section, cat_name, price_label, note, items) in enumerate(MENU):
            cat, _ = MenuCategory.objects.get_or_create(
                section=section, name=cat_name,
                defaults=dict(price_label=price_label, note=note, order=ci),
            )
            for ii, (name, desc, price, serves, veg, spicy) in enumerate(items):
                MenuItem.objects.get_or_create(
                    category=cat, name=name,
                    defaults=dict(description=desc, price=price, serves=serves,
                                  is_vegetarian=veg, is_spicy=spicy, order=ii),
                )
        self.stdout.write(f"Menu: {MenuCategory.objects.count()} categories, {MenuItem.objects.count()} items")

        for data in POSTS:
            data = dict(data)
            image, days = data.pop("image"), data.pop("days_ago")
            p, created = Post.objects.get_or_create(
                title=data["title"],
                defaults={**data, "published_at": timezone.now() - datetime.timedelta(days=days)},
            )
            if created:
                attach(p, "image", image, "post")
                p.save()
        self.stdout.write(f"News posts: {Post.objects.count()}")

        for i, data in enumerate(JOBS):
            JobOpening.objects.get_or_create(title=data["title"], defaults={**data, "order": i})
        self.stdout.write(f"Job openings: {JobOpening.objects.count()}")

        self.stdout.write(self.style.SUCCESS("Mbuzi Munch content loaded."))
