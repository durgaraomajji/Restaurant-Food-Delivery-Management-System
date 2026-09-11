from pathlib import Path

def test_required_structure():
    root=Path(__file__).parents[1]
    required=['app/main.py','app/database.py','app/config.py','app/models','app/schemas','app/routes','app/services','app/repositories','app/utils','alembic','postman_collection.json','.env.example','README.md','ER_DIAGRAM.md','ARCHITECTURE.md','SWAGGER_TEST_GUIDE.md']
    missing=[p for p in required if not (root/p).exists()]
    assert not missing, f'Missing: {missing}'

def test_required_route_modules():
    root=Path(__file__).parents[1]
    names=['auth.py','restaurants.py','menu.py','customers.py','cart.py','orders.py','payments.py','delivery.py','tracking.py','coupons.py','reviews.py','refunds.py']
    assert all((root/'app/routes'/n).exists() for n in names)
