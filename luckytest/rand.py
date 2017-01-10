import time
import random

def select_buy_info_new(activity_dict):
    target_amount = activity_dict['target_amount']
    current_amount = activity_dict['current_amount']
    left_amount = target_amount - current_amount
    unit = activity_dict['unit']

    seed = random.randint(1, 100)

    if seed < 30:
        r = 1 
    elif seed < 50:
        r = random.randint(2, 5)
    elif seed < 65:
        r = random.randint(6, 10)
    elif seed < 75:
        r = random.randint(11, 20)
    elif seed < 85:
        r = random.choice([30,40,50,60,70,80,90,100])
    elif seed < 90:
        r = random.randint(21, 99)
    elif seed < 95:
        r = random.choice([200,300,400,500,600,700,800,900,1000])
    elif seed < 98:
        r = random.randint(101, 999)
    elif target_amount > 1000:
        r = random.randint(1000, target_amount)
    else:
        r = 1000

    if r > target_amount/3:
        r = random.randint(1, target_amount/3)

    if r % unit != 0:
        r = (r/unit)*unit

    if r > 100 and r % 10 > 0:
        r = (r/10)*10

    if r == 0:
        r = unit

    rand = r

    quantity = unit * rand
    return quantity


for _ in xrange(100):
    import time
    time.sleep(1)
    print select_buy_info_new({'target_amount': 7488, 'current_amount': 0, 'unit':1})
