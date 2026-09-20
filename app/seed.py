"""Menu transcribed from Oasis' published temp-menu-04172024.jpg.
Prices and restaurant policies need owner confirmation before live trading.
"""
import re

GROUPS = {
 'Mains': [
 ('Samarkand Plov',18,'Fragrant rice, carrots, lamb, beef and traditional spices','plov.webp'),
 ('Shepherd’s Fried Lamb with Potatoes',55,'Serves 3–4 people'),
 ('Tabaka Oasis',14,'Marinated fried Cornish hen'),
 ('Manti',14,'Four steamed dumplings with chopped beef and onions, pumpkin or potato'),
 ('Crispy Manti',14,'Four pan-fried dumplings with chopped beef and onions'),
 ('Homemade Beef Ravioli',14,''),('Fried Ravioli with Beef',14,''),
 ('Turkish Fried Liver',15,''),('Tefteli',18,'Homemade lamb and beef meatballs and potatoes')],
 'Kebabs': [('Lamb',9,''),('Lamb Ribs',10,''),('Beef Tenderloin',10,''),('Beef Roulade',10,''),('Ground Beef',9,''),('Chicken Thighs',8,''),('Chicken Wings',9,''),('Veal Liver',9,''),('Veggie Kebab',8,''),('Grilled Tomatoes',8,''),('Salmon Kebab',15,''),('Shrimp Kebab',11,''),('Lamb Chops',32,'Served with a side dish')],
 'Starters': [('Tandoori Samsa',4,'Crispy pastry stuffed with chopped beef and onions','samsa.webp'),('Kutabi',3.5,'Thin dough pockets with beef, or herbs and cheese'),('Chebureki',4,'Deep-fried dough pockets stuffed with ground lamb and beef'),('Pickled Herring with Potatoes',15,''),('Pickled Vegetables',14,''),('Sliced Beef Tongue',16,'')],
 'Salads': [('Fresh Salad',12,'Tomatoes, cucumbers, onions, spring mix and herbs'),('Fresh Salad with Avocado and Feta Cheese',14,''),('Achichuk',12,'Thinly sliced tomatoes, onions and herbs'),('Maraganda',14,'Greek salad topped with cured beef'),('Ru-Mex',14,'Avocado, hard-boiled eggs, pickles and light mayonnaise'),('Eggplant Salad',14,''),('Spring Salad',14,'Beets, baby arugula, sunflower seeds, balsamic dressing and goat cheese'),('Asia',14,'Chicken breast, mushrooms, eggs, green onions and light mayonnaise'),('Nejnost',14,'Beef tongue strips, cucumbers, green peas, hard-boiled eggs and mayonnaise'),('Suzma',12,'Sour yogurt, cucumbers, pickles and herbs'),('Smak',14,'Homemade seasoned croutons, tomato cubes, mozzarella and mayonnaise')],
 'Soups': [('Shurpa',8,'Traditional Uzbek lamb and beef soup with vegetables'),('Lagman',8,'Homemade noodles, beef and vegetables'),('Kharcho',8,'Rice, beef and vegetables'),('Borscht',8,'Beet, beef, cabbage and vegetable soup'),('Homemade Beef Ravioli Soup',8,''),('Lentil',8,''),('Okroshka',8,'Seasonal yogurt soup with radishes, potatoes, hard-boiled eggs and boiled halal sausage')],
 'Seafood': [('Garlic Butter Sautéed Shrimp and Vegetables',28,'','shrimp.webp'),('Bronzini Grilled',28,'')],
 'Sides': [('Homemade Potatoes with Mushrooms',12,''),('Hand Cut French Fries',8,''),('Rice',8,''),('Village Style Potatoes',11,'Yukon potatoes with garlic and dill')],
 'Desserts': [('Baklava',6,''),('Napoleon',7,''),('Honey Cake',7,''),('Ice Cream',7,'Vanilla or chocolate')],
 'Drinks': [('Homemade Fruit Compote',11,'Fruit punch · pitcher'),('Turshak Ob',13,'Dried apricot punch · pitcher'),('Ayran',3.5,'Yogurt drink'),('Tarhun',4,'Carbonated tarragon drink'),('Sodas',2.5,''),('Sparkling Water',5,''),('Mexican Coke',3.5,''),('Tea',3.5,'Green or black'),('Black Tea with Lemon and Sugar',5.5,''),('Turkish Coffee',3.5,''),('Chalop',7,'Seasonal yogurt drink with sliced cucumbers, radishes and herbs')],
 'Lunch Specials': [('Plov Special',22.5,'Plov, tomato salad, ¼ bread and tea, soda or compote'),('Shish Kebab Special',20,'Two skewers, rice or fries, ¼ bread and a drink. Beef tenderloin or lamb ribs +$1 per skewer'),('Soup Special',10.5,'Choice of soup, ¼ bread and a drink'),('Samsa Special',16,'Four samsas and tea, soda or compote'),('Manti Special',15,'Meat, pumpkin or potato manti, ¼ bread and a drink')]
}

def menu():
    result=[]
    for category, items in GROUPS.items():
        for row in items:
            name,price,description,*image=row
            options=[]
            if name in ('Manti','Manti Special'): options=[{'label':'Filling','values':['Beef','Pumpkin','Potato']}]
            if name=='Kutabi': options=[{'label':'Filling','values':['Beef','Herbs and cheese']}]
            if name=='Ice Cream': options=[{'label':'Flavor','values':['Vanilla','Chocolate']}]
            if name=='Tea': options=[{'label':'Tea','values':['Green','Black']}]
            if category=='Lunch Specials':
                options.append({'label':'Drink','values':['Tea','Soda','Compote']})
                if name=='Shish Kebab Special':
                    options += [{'label':'First skewer','values':['Lamb','Chicken','Ground beef','Veal liver','Beef tenderloin (+$1)','Lamb ribs (+$1)']},{'label':'Second skewer','values':['Lamb','Chicken','Ground beef','Veal liver','Beef tenderloin (+$1)','Lamb ribs (+$1)']},{'label':'Side','values':['Rice','Fries']}]
                if name=='Soup Special': options.append({'label':'Soup','values':['Shurpa','Lagman','Kharcho','Borscht','Lentil']})
            if name=='Lamb Chops':options=[{'label':'Side','values':['Rice','Fries']}]
            result.append(dict(id=re.sub('[^a-z0-9]+','-',name.lower()).strip('-'),name=name,category=category,price=round(price*100),description=description,image=image[0] if image else '',options=options,available=True))
    return result

DEFAULTS={'accept_orders':True,'accept_reservations':True,'pickup_lead':30,'pickup_interval':15,'pickup_cutoff':30,'advance_days':7,'reservation_lead':120,'reservation_duration':90,'reservation_interval':30,'max_party':6,'capacity':24,'tax_bps':0,'hours':[[660,1320]]*6+[[660,1260]],'closures':[],'email_enabled':False}
