"""Quick test to verify the fixes work."""
import sys
sys.path.insert(0, '.')

print("Testing backend imports...")
try:
    from backend.calculators import calc_bmi, calc_ideal_weight, calc_calories, calc_water
    from backend.models import BMIRequest, IdealWeightRequest, CalorieRequest, WaterRequest
    print("  ✓ Imports OK")
except Exception as e:
    print(f"  ✗ Import failed: {e}")
    sys.exit(1)

print("\nTesting BMI metric (70kg, 170cm):")
try:
    r = BMIRequest(weight=70, height=170, unit='metric')
    result = calc_bmi(r)
    expected = round(70 / (1.70 ** 2), 1)
    assert result['bmi'] == expected, f"Expected {expected}, got {result['bmi']}"
    print(f"  ✓ BMI = {result['bmi']} ({result['category']})")
except Exception as e:
    print(f"  ✗ Failed: {e}")

print("\nTesting BMI imperial (154lbs, 67in):")
try:
    r2 = BMIRequest(weight=154, height=67, unit='imperial')
    result2 = calc_bmi(r2)
    # 154 lbs = 69.85kg, 67in = 170.18cm
    expected_kg = 154 * 0.453592
    expected_cm = 67 * 2.54
    expected_bmi = round(expected_kg / ((expected_cm / 100) ** 2), 1)
    assert result2['bmi'] == expected_bmi, f"Expected {expected_bmi}, got {result2['bmi']}"
    print(f"  ✓ BMI = {result2['bmi']} ({result2['category']}) — should be similar to metric test")
except Exception as e:
    print(f"  ✗ Failed: {e}")

print("\nTesting ideal weight validation (too short, 140cm):")
try:
    from fastapi import HTTPException
    r3 = IdealWeightRequest(height=140, gender='male')
    calc_ideal_weight(r3)
    print("  ✗ Should have raised HTTPException!")
except HTTPException as e:
    print(f"  ✓ Correctly raised HTTPException 400: {e.detail[:60]}...")
except Exception as e:
    print(f"  ✗ Wrong exception type: {type(e).__name__}: {e}")

print("\nTesting ideal weight valid (170cm, male):")
try:
    r4 = IdealWeightRequest(height=170, gender='male')
    result4 = calc_ideal_weight(r4)
    print(f"  ✓ Ideal = {result4['ideal']} kg, range {result4['low']}–{result4['high']} kg")
except Exception as e:
    print(f"  ✗ Failed: {e}")

print("\nTesting auth JWT secret validation:")
try:
    import warnings
    import os
    os.environ.pop('JWT_SECRET', None)
    
    # Reimport to trigger the validation
    import importlib
    import backend.auth as auth_module
    importlib.reload(auth_module)
    
    jwt_secret = auth_module.JWT_SECRET
    assert jwt_secret != "nexora-dev-secret-change-in-prod", "Old insecure default used!"
    assert len(jwt_secret) >= 32, f"JWT secret too short: {len(jwt_secret)} chars"
    print(f"  ✓ JWT secret is random, {len(jwt_secret)} chars (not the insecure default)")
except Exception as e:
    print(f"  ✗ Failed: {e}")

print("\nTesting route order in main (checking clear_done before rid):")
try:
    from backend.main import app
    delete_routes = [(i, str(r.path), list(r.methods)) for i, r in enumerate(app.routes) 
                     if hasattr(r, 'path') and hasattr(r, 'methods') and 'DELETE' in (r.methods or set())]
    
    print("  All DELETE routes in order:")
    for i, path, methods in delete_routes:
        print(f"    [{i}] {path}")
    
    clear_done_idx = next((i for i, p, m in delete_routes if 'done/clear' in p), -1)
    rid_delete_idx = next((i for i, p, m in delete_routes if '{rid}' in p), -1)
    
    if clear_done_idx == -1:
        print("  ⚠ Could not find clear_done route")
    elif rid_delete_idx == -1:
        print("  ⚠ Could not find /{rid} DELETE route")
    elif clear_done_idx < rid_delete_idx:
        print(f"  ✓ /done/clear route (pos {clear_done_idx}) is before /" + "{rid} route (pos {rid_delete_idx})")
    else:
        print(f"  ✗ /done/clear (pos {clear_done_idx}) is AFTER /" + "{rid} (pos {rid_delete_idx}) — route ordering bug!")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"  ✗ Failed: {e}")

print("\nAll tests done!")
