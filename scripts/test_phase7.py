"""
Test script for Phase 7 (Memory)
Validates DB CRUD operations (including UPSERT) and tool schemas.
"""
import sys
import os

# Add root directory to python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.memory.db import init_db, add_memory, remove_memory, get_all_memories
from backend.planner.schema import TOOLS_SCHEMA

def run_tests():
    print("🧪 Running Phase 7 Tests...\n")
    
    # 1. DB Tests
    print("Testing DB...")
    init_db()
    
    # Clean state for test
    memories = get_all_memories()
    for m in memories:
        if m['label'].startswith('test_'):
            remove_memory(m['label'])
            
    # Add new
    m1 = add_memory("fact", "test_color", "Blue")
    print("✅ Insert new memory")
    
    # Upsert (same category and label, different value)
    m2 = add_memory("fact", "test_color", "Red")
    print("✅ Upsert (overwrite) memory")
    
    # Fetch
    mems = get_all_memories()
    test_mem = next((m for m in mems if m['label'] == 'test_color'), None)
    assert test_mem is not None, "Memory not found!"
    assert test_mem['value'] == 'Red', "Upsert failed to update value!"
    print("✅ Fetch memory correctly")
    
    # Remove
    success = remove_memory("test_color")
    assert success is True, "Remove memory failed!"
    print("✅ Remove memory")
    
    # 2. Schema Tests
    print("\nTesting Schemas...")
    tool_names = [t['function']['name'] for t in TOOLS_SCHEMA]
    assert 'remember' in tool_names, "remember tool missing from schema"
    assert 'forget' in tool_names, "forget tool missing from schema"
    print("✅ Memory tools present in schema")
    
    print("\n🎉 ALL PHASE 7 TESTS PASSED!")

if __name__ == "__main__":
    run_tests()
