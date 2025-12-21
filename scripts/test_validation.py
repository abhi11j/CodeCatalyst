import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Scanner.Utility.apply_suggestions import _validate_change_entry
repo = os.getcwd()
# Test: path traversal
try:
    _validate_change_entry({'path':'../etc/passwd','action':'add','content':'x'}, repo)
    print('ERROR: traversal not detected')
except Exception as e:
    print('OK traversal detected:', type(e).__name__, e)
# Test: invalid action
try:
    _validate_change_entry({'path':'safe.txt','action':'rename','content':'x'}, repo)
    print('ERROR: invalid action not detected')
except Exception as e:
    print('OK invalid action detected:', type(e).__name__, e)
# Test: oversize
try:
    _validate_change_entry({'path':'big.txt','action':'add','content':'x'* (210*1024)}, repo)
    print('ERROR: oversize not detected')
except Exception as e:
    print('OK oversize detected:', type(e).__name__, e)
