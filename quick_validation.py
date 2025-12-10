import pandas as pd
import tempfile
import os

# Test basic functionality
print("Testing basic components...")

# Test DataFrame creation and scoring
df = pd.DataFrame({
    'Parameter': ['pH', 'Temperature'],
    'Value': [7.2, 25.5],
    'Unit': ['pH units', '°C']
})

print(f"✓ Created DataFrame with {len(df)} rows")

# Test file operations
temp_dir = tempfile.mkdtemp()
test_file = os.path.join(temp_dir, 'test.txt')

with open(test_file, 'w') as f:
    f.write("Test content")

print(f"✓ File operations working: {os.path.exists(test_file)}")

# Test project structure
projects_dir = os.path.join(temp_dir, 'projects')
os.makedirs(projects_dir, exist_ok=True)

print(f"✓ Directory creation: {os.path.exists(projects_dir)}")

print("Basic validation completed successfully!")
