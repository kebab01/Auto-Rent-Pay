# Auto Rent Pay

## Why?
University does not have a direct debit option for paying accomodation rent, so I decided to build a script to act as a continual payment

## Setup
- Clone repository `git clone https://github.com/kebab01/Auto-Rent-Pay`
- Install requirements `pip install -r requirements.txt`
- Create env file for sensitive details `vim .env`
- In .env file add the following:
```
EMAIL=
PASS=
RENT=
CARD_NUM=
CARD_EXP_MONTH=
CARD_EXP_YEAR=
CARD_CCV=
```
- After each `=` place your corresponding details
- Run with `python main.py`
