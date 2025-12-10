#!/usr/bin/env python3
"""
Simple validation script for environmental risk analysis application.
"""

import os
import sys
import pandas as pd
import tempfile
import shutil

def test_project_manager():
    """Test project manager functionality."""
    print("Testing ProjectManager...")
    try:
        from project_manager import ProjectManager
        
        temp_dir = tempfile.mkdtemp()
        pm = ProjectManager(projects_dir=temp_dir)
        
        # Create project
        project_id = pm.create_project("Test Project", "Description", "Location")
        print(f"✓ Created project: {project_id}")
        
        # Test project exists
        assert pm.project_exists(project_id), "Project should exist"
        print("✓ Project exists check")
        
        # Load project
        project_data = pm.load_project(project_id)
        assert project_data['name'] == "Test Project", "Project name mismatch"
        print("✓ Project loading")
        
        shutil.rmtree(temp_dir)
        return True
        
    except Exception as e:
        print(f"✗ ProjectManager test failed: {e}")
        return False

def test_environmental_scorer():
    """Test environmental scoring system."""
    print("Testing EnvironmentalScorer...")
    try:
        from environmental_scoring import EnvironmentalScorer
        
        scorer = EnvironmentalScorer()
        
        # Test pH scoring
        score = scorer.score_parameter('pH', 7.0)
        assert score in [1, 2, 3], "Score should be 1, 2, or 3"
        print(f"✓ pH scoring: {score}")
        
        # Test DataFrame scoring
        df = pd.DataFrame({
            'Parameter': ['pH', 'Temperature'],
            'Value': [7.2, 25.5],
            'Unit': ['pH units', '°C']
        })
        
        scored_df = scorer.score_dataframe(df)
        assert 'Score' in scored_df.columns, "Score column should be added"
        print("✓ DataFrame scoring")
        
        return True
        
    except Exception as e:
        print(f"✗ EnvironmentalScorer test failed: {e}")
        return False

def test_config():
    """Test configuration loading."""
    print("Testing config...")
    try:
        import config
        print("✓ Config module loaded")
        return True
    except Exception as e:
        print(f"✗ Config test failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("=== APPLICATION VALIDATION ===")
    
    tests = [
        test_config,
        test_project_manager,
        test_environmental_scorer
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All core components are working correctly!")
        return True
    else:
        print("✗ Some components have issues")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
